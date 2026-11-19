from datetime import UTC, datetime

import pytest

from drive_text_extractor.domain.errors import FileTooLargeError
from drive_text_extractor.domain.jobs import FileStatus, FileTask, Job
from drive_text_extractor.domain.models import (
    ExtractionMethod,
    ExtractionOptions,
    ExtractionResult,
    SourceFile,
)
from drive_text_extractor.extractors.image import ImageExtractor
from drive_text_extractor.extractors.pdf import PdfExtractor
from drive_text_extractor.services.batch_runner import BatchRunner
from drive_text_extractor.services.router import ExtractorRouter
from tests.fakes import FakeFileSource, FakeOcrEngine
from tests.images import png_bytes
from tests.pdf_factory import make_pdf

pytestmark = pytest.mark.anyio

FINISHED_AT = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)


class ExplodingExtractor:
    """An extractor with a bug: raises something that is not a domain error."""

    media_types = frozenset({"text/plain"})

    def accepts(self, head: bytes) -> bool:
        return head.startswith(b"BOOM")

    def extract(self, data: bytes, options: ExtractionOptions) -> ExtractionResult:
        raise KeyError("bug")


def source_file(file_id: str, mime_type: str = "application/pdf") -> SourceFile:
    return SourceFile(id=file_id, name=f"{file_id}.bin", mime_type=mime_type)


def make_job(*files: SourceFile, languages: tuple[str, ...] = ("eng",)) -> Job:
    return Job(
        id="job-1",
        link="link",
        folder_id="folder",
        folder_name="Folder",
        options=ExtractionOptions(languages=languages),
        tasks=[FileTask(file) for file in files],
        created_at=datetime(2026, 11, 19, tzinfo=UTC),
    )


@pytest.fixture
def ocr() -> FakeOcrEngine:
    return FakeOcrEngine(text="text from image")


@pytest.fixture
def router(ocr: FakeOcrEngine) -> ExtractorRouter:
    return ExtractorRouter([PdfExtractor(), ImageExtractor(ocr), ExplodingExtractor()])


def runner(source: FakeFileSource, router: ExtractorRouter, concurrency: int = 2) -> BatchRunner:
    return BatchRunner(source, router, concurrency=concurrency, now=lambda: FINISHED_AT)


async def test_routes_each_file_to_the_right_pipeline(
    router: ExtractorRouter, ocr: FakeOcrEngine
) -> None:
    source = FakeFileSource(contents={"pdf": make_pdf(["Typed invoice text"]), "png": png_bytes()})
    job = make_job(source_file("pdf"), source_file("png", "image/png"), languages=("ara",))

    await runner(source, router).run(job)

    pdf, png = job.tasks
    assert pdf.status is FileStatus.DONE
    assert pdf.result is not None
    assert pdf.result.method is ExtractionMethod.PDF_PARSER
    assert pdf.result.text == "Typed invoice text"
    assert png.result is not None
    assert png.result.method is ExtractionMethod.OCR
    assert ocr.calls[0].languages == ("ara",)
    assert job.finished_at == FINISHED_AT


async def test_one_failing_file_does_not_stop_the_batch(router: ExtractorRouter) -> None:
    source = FakeFileSource(
        contents={
            "first": make_pdf(["first file"]),
            "too-big": FileTooLargeError("This file is 40 MB; the limit is 25 MB."),
            "corrupt": b"%PDF-1.7 truncated",
            "last": png_bytes(),
        }
    )
    job = make_job(*(source_file(i) for i in ["first", "too-big", "corrupt", "last"]))

    await runner(source, router).run(job)

    statuses = {task.file.id: task.status for task in job.tasks}
    assert statuses == {
        "first": FileStatus.DONE,
        "too-big": FileStatus.FAILED,
        "corrupt": FileStatus.FAILED,
        "last": FileStatus.DONE,
    }
    too_big = job.task_for("too-big")
    assert too_big.failure is not None
    assert too_big.failure.code == "file_too_large"
    assert too_big.failure.message == "This file is 40 MB; the limit is 25 MB."
    assert job.task_for("corrupt").failure is not None
    assert job.is_finished


async def test_unexpected_errors_are_contained_and_logged(
    router: ExtractorRouter, caplog: pytest.LogCaptureFixture
) -> None:
    source = FakeFileSource(contents={"bug": b"BOOM!", "fine": make_pdf(["ok"])})
    job = make_job(source_file("bug"), source_file("fine"))

    await runner(source, router).run(job)

    bug = job.task_for("bug")
    assert bug.status is FileStatus.FAILED
    assert bug.failure is not None
    assert bug.failure.code == "internal_error"
    assert "KeyError" not in bug.failure.message
    assert job.task_for("fine").status is FileStatus.DONE
    assert "unexpected error on bug.bin" in caplog.text


async def test_unknown_content_fails_with_unsupported_file(router: ExtractorRouter) -> None:
    job = make_job(source_file("gif", "image/gif"))

    await runner(FakeFileSource(contents={"gif": b"GIF89a..."}), router).run(job)

    assert job.tasks[0].failure is not None
    assert job.tasks[0].failure.code == "unsupported_file"


async def test_never_processes_more_files_at_once_than_allowed(router: ExtractorRouter) -> None:
    files = [source_file(f"f{n}") for n in range(6)]
    source = FakeFileSource(contents={f.id: make_pdf(["text"]) for f in files}, download_delay=0.01)

    await runner(source, router, concurrency=2).run(make_job(*files))

    assert source.max_in_flight == 2


async def test_records_how_long_each_file_took(router: ExtractorRouter) -> None:
    ticks = iter([10.0, 10.25])
    job = make_job(source_file("a"))
    source = FakeFileSource(contents={"a": make_pdf(["a"])})

    await BatchRunner(source, router, clock=lambda: next(ticks)).run(job)

    assert job.tasks[0].duration_ms == 250


async def test_cancelled_job_skips_files_not_yet_started(router: ExtractorRouter) -> None:
    files = [source_file(f"f{n}") for n in range(3)]
    source = FakeFileSource(contents={f.id: make_pdf(["text"]) for f in files})
    job = make_job(*files)
    job.cancel_requested = True

    await runner(source, router).run(job)

    assert {task.status for task in job.tasks} == {FileStatus.CANCELLED}
    assert source.downloads == []


def test_rejects_a_concurrency_below_one(router: ExtractorRouter) -> None:
    with pytest.raises(ValueError, match="at least 1"):
        BatchRunner(FakeFileSource(), router, concurrency=0)
