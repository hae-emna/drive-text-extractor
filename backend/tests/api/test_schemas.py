from datetime import UTC, datetime

from drive_text_extractor.api.schemas import EXPORT_SCHEMA_VERSION, export_out, job_out
from drive_text_extractor.domain.jobs import Failure, FileTask, Job
from drive_text_extractor.domain.models import (
    ExtractionMethod,
    ExtractionOptions,
    ExtractionResult,
    PageText,
    SourceFile,
)

CREATED = datetime(2026, 11, 19, 9, 0, tzinfo=UTC)
FINISHED = datetime(2026, 11, 19, 9, 1, tzinfo=UTC)


def make_job() -> Job:
    scanned = FileTask(SourceFile("s", "scan.png", "image/png", 2048, path="2024/scan.png"))
    scanned.start()
    scanned.succeed(
        ExtractionResult(pages=(PageText(1, ExtractionMethod.OCR, "blurry", 41.0),)),
        duration_ms=900,
    )
    typed = FileTask(SourceFile("t", "typed.pdf", "application/pdf", 4096))
    typed.start()
    typed.succeed(
        ExtractionResult(pages=(PageText(1, ExtractionMethod.PDF_PARSER, "clean"),)),
        duration_ms=30,
    )
    broken = FileTask(SourceFile("b", "broken.pdf", "application/pdf", 10))
    broken.start()
    broken.fail(Failure("corrupt_file", "This file is damaged."), duration_ms=3)
    waiting = FileTask(SourceFile("w", "waiting.pdf", "application/pdf", 10))
    return Job(
        id="job-1",
        link="https://drive.google.com/drive/folders/abc",
        folder_id="abc",
        folder_name="Invoices",
        options=ExtractionOptions(languages=("fra", "ara")),
        tasks=[scanned, typed, broken, waiting],
        created_at=CREATED,
    )


def test_job_snapshot_reports_status_summary_and_results() -> None:
    out = job_out(make_job(), low_confidence_below=60)

    assert out.status == "running"
    assert out.languages == ["fra", "ara"]
    assert out.summary.model_dump() == {
        "total": 4,
        "pending": 1,
        "processing": 0,
        "done": 2,
        "failed": 1,
        "cancelled": 0,
    }
    scanned, typed, broken, waiting = out.files
    assert scanned.file.path == "2024/scan.png"
    assert scanned.method is ExtractionMethod.OCR
    assert scanned.low_confidence is True
    assert typed.low_confidence is False
    assert typed.mean_confidence is None
    assert typed.text == "clean"
    assert broken.error is not None
    assert broken.error.code == "corrupt_file"
    assert broken.pages == []
    assert waiting.status == "pending"
    assert waiting.method is None


def test_finished_job_is_reported_as_finished() -> None:
    job = make_job()
    job.finished_at = FINISHED

    assert job_out(job, low_confidence_below=60).status == "finished"


def test_export_is_versioned_and_describes_its_source() -> None:
    export = export_out(make_job(), source_type="google_drive", low_confidence_below=60)
    data = export.model_dump(mode="json")

    assert data["schema_version"] == EXPORT_SCHEMA_VERSION
    assert data["source"] == {
        "type": "google_drive",
        "link": "https://drive.google.com/drive/folders/abc",
        "folder": {"id": "abc", "name": "Invoices"},
    }
    assert data["created_at"] == "2026-11-19T09:00:00Z"
    assert data["files"][0]["pages"] == [
        {"number": 1, "method": "ocr", "confidence": 41.0, "text": "blurry"}
    ]
