from datetime import UTC, datetime

import anyio
import pytest

from drive_text_extractor.domain.errors import (
    FolderNotFoundError,
    InvalidSelectionError,
    JobNotFoundError,
    UnsupportedLanguageError,
)
from drive_text_extractor.domain.jobs import FileStatus, Job
from drive_text_extractor.domain.models import SourceFile
from drive_text_extractor.extractors.image import ImageExtractor
from drive_text_extractor.extractors.pdf import PdfExtractor
from drive_text_extractor.services.batch_runner import BatchRunner
from drive_text_extractor.services.folder_browser import FolderBrowser
from drive_text_extractor.services.job_service import JobService
from drive_text_extractor.services.job_store import InMemoryJobStore
from drive_text_extractor.services.router import ExtractorRouter
from tests.fakes import FakeFileSource, FakeOcrEngine
from tests.images import png_bytes
from tests.pdf_factory import make_pdf

pytestmark = pytest.mark.anyio

CREATED_AT = datetime(2026, 11, 19, 9, 30, tzinfo=UTC)
FILES = [
    SourceFile(id="pdf-1", name="invoice.pdf", mime_type="application/pdf", size_bytes=900),
    SourceFile(id="png-1", name="receipt.png", mime_type="image/png", size_bytes=400),
    SourceFile(id="doc-1", name="notes", mime_type="application/vnd.google-apps.document"),
]


@pytest.fixture
def source() -> FakeFileSource:
    return FakeFileSource(
        files=FILES, contents={"pdf-1": make_pdf(["Invoice 42"]), "png-1": png_bytes()}
    )


@pytest.fixture
def store() -> InMemoryJobStore:
    return InMemoryJobStore()


@pytest.fixture
def service(source: FakeFileSource, store: InMemoryJobStore) -> JobService:
    router = ExtractorRouter([PdfExtractor(), ImageExtractor(FakeOcrEngine())])
    return JobService(
        FolderBrowser(source, router),
        BatchRunner(source, router),
        store,
        new_id=lambda: "job-1",
        now=lambda: CREATED_AT,
    )


async def finished(job: Job) -> Job:
    with anyio.fail_after(2):
        # Polling is fine here: the job is driven by a background task we do not own.
        while job.finished_at is None:  # noqa: ASYNC110
            await anyio.sleep(0.005)
    return job


async def test_starts_a_job_and_runs_it_in_the_background(
    service: JobService, store: InMemoryJobStore
) -> None:
    job = await service.start("link", ["png-1", "pdf-1"], languages=["fra", "eng"])

    assert job.id == "job-1"
    assert job.created_at == CREATED_AT
    assert job.folder_name == FakeFileSource.FOLDER_NAME
    assert job.options.languages == ("fra", "eng")
    assert [task.file.name for task in job.tasks] == ["receipt.png", "invoice.pdf"]
    assert store.get("job-1") is job

    await finished(job)
    assert {task.status for task in job.tasks} == {FileStatus.DONE}


async def test_uses_server_side_metadata_and_ignores_duplicate_ids(service: JobService) -> None:
    job = await service.start("link", ["pdf-1", "pdf-1"], languages=["eng"])

    assert len(job.tasks) == 1
    assert job.tasks[0].file.size_bytes == 900
    await finished(job)


@pytest.mark.parametrize("file_ids", [["not-in-folder"], ["doc-1"]], ids=["unknown", "skipped"])
async def test_refuses_files_that_are_not_offered_in_the_folder(
    service: JobService, file_ids: list[str]
) -> None:
    with pytest.raises(InvalidSelectionError, match="no longer in this folder"):
        await service.start("link", file_ids, languages=["eng"])


async def test_refuses_an_empty_selection_without_listing(
    service: JobService, source: FakeFileSource
) -> None:
    with pytest.raises(InvalidSelectionError, match="at least one file"):
        await service.start("link", [], languages=["eng"])

    assert source.listed_recursively == []


async def test_refuses_unsupported_languages(service: JobService) -> None:
    with pytest.raises(UnsupportedLanguageError):
        await service.start("link", ["pdf-1"], languages=["klingon"])


async def test_source_errors_reach_the_caller(service: JobService, source: FakeFileSource) -> None:
    source.list_error = FolderNotFoundError()

    with pytest.raises(FolderNotFoundError):
        await service.start("link", ["pdf-1"], languages=["eng"])


async def test_gets_jobs_by_id(service: JobService) -> None:
    job = await service.start("link", ["pdf-1"], languages=["eng"])

    assert service.get("job-1") is job
    with pytest.raises(JobNotFoundError):
        service.get("nope")
    await finished(job)


async def test_cancel_marks_the_job(service: JobService) -> None:
    job = await service.start("link", ["pdf-1", "png-1"], languages=["eng"])

    assert service.cancel("job-1").cancel_requested
    await finished(job)
    assert job.is_finished
