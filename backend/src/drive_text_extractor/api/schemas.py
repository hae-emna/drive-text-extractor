"""Request and response models, and the mapping from domain objects.

The JSON shapes are a contract with the web page (and with whoever reads an export), so they are
declared here explicitly instead of serialising domain objects as they happen to be.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from drive_text_extractor.config import SourceType
from drive_text_extractor.domain.jobs import FileStatus, FileTask, Job
from drive_text_extractor.domain.languages import SUPPORTED_LANGUAGES
from drive_text_extractor.domain.models import (
    ExtractionMethod,
    FolderListing,
    LinkKind,
    PageText,
    SkippedFile,
    SourceFile,
)

EXPORT_SCHEMA_VERSION = "1.1"
"""1.1 added ``source.kind``; additive changes bump the minor version."""

MAX_LINK_LENGTH = 2048
MAX_FILES_PER_JOB = 1000

# --- Requests ------------------------------------------------------------------------------


class ListFilesRequest(BaseModel):
    link: str = Field(min_length=1, max_length=MAX_LINK_LENGTH)
    recursive: bool = False


class StartJobRequest(BaseModel):
    link: str = Field(min_length=1, max_length=MAX_LINK_LENGTH)
    file_ids: list[str] = Field(min_length=1, max_length=MAX_FILES_PER_JOB)
    languages: list[str] = Field(default=["eng"], min_length=1, max_length=len(SUPPORTED_LANGUAGES))
    recursive: bool = False


# --- Responses -----------------------------------------------------------------------------


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class FileOut(BaseModel):
    id: str
    name: str
    path: str
    mime_type: str
    size_bytes: int | None
    modified_time: str | None


class SkippedFileOut(BaseModel):
    name: str
    mime_type: str
    reason: str


class FolderOut(BaseModel):
    id: str
    name: str


class FolderListingOut(BaseModel):
    kind: LinkKind
    folder: FolderOut
    """The folder, or the file itself when the link points to a single file."""
    files: list[FileOut]
    skipped: list[SkippedFileOut]
    truncated: bool


class PageOut(BaseModel):
    number: int
    method: ExtractionMethod
    confidence: float | None
    text: str


class FileResultOut(BaseModel):
    file: FileOut
    status: FileStatus
    method: ExtractionMethod | None
    mean_confidence: float | None
    low_confidence: bool
    char_count: int
    duration_ms: int | None
    text: str
    pages: list[PageOut]
    error: ErrorBody | None


class SummaryOut(BaseModel):
    total: int
    pending: int
    processing: int
    done: int
    failed: int
    cancelled: int


class JobOut(BaseModel):
    id: str
    status: Literal["running", "finished"]
    created_at: datetime
    finished_at: datetime | None
    cancel_requested: bool
    folder: FolderOut
    languages: list[str]
    summary: SummaryOut
    files: list[FileResultOut]


class SourceOut(BaseModel):
    type: SourceType
    kind: LinkKind
    link: str
    folder: FolderOut


class ExportOut(BaseModel):
    """The downloadable result of a batch. ``schema_version`` changes on breaking changes."""

    schema_version: str = EXPORT_SCHEMA_VERSION
    job_id: str
    created_at: datetime
    finished_at: datetime | None
    languages: list[str]
    source: SourceOut
    summary: SummaryOut
    files: list[FileResultOut]


class LanguageOut(BaseModel):
    code: str
    name: str
    installed: bool


class HealthOut(BaseModel):
    status: Literal["ok"] = "ok"
    version: str
    source: SourceType
    languages: list[LanguageOut]


# --- Mapping -------------------------------------------------------------------------------


def file_out(file: SourceFile) -> FileOut:
    return FileOut(
        id=file.id,
        name=file.name,
        path=file.display_path,
        mime_type=file.mime_type,
        size_bytes=file.size_bytes,
        modified_time=file.modified_time,
    )


def skipped_out(skipped: SkippedFile) -> SkippedFileOut:
    return SkippedFileOut(name=skipped.name, mime_type=skipped.mime_type, reason=skipped.reason)


def listing_out(listing: FolderListing) -> FolderListingOut:
    return FolderListingOut(
        kind=listing.kind,
        folder=FolderOut(id=listing.folder_id, name=listing.folder_name),
        files=[file_out(file) for file in listing.files],
        skipped=[skipped_out(skipped) for skipped in listing.skipped],
        truncated=listing.truncated,
    )


def page_out(page: PageText) -> PageOut:
    return PageOut(
        number=page.number, method=page.method, confidence=page.confidence, text=page.text
    )


def file_result_out(task: FileTask, *, low_confidence_below: float) -> FileResultOut:
    result = task.result
    confidence = result.mean_confidence if result else None
    return FileResultOut(
        file=file_out(task.file),
        status=task.status,
        method=result.method if result else None,
        mean_confidence=confidence,
        low_confidence=confidence is not None and confidence < low_confidence_below,
        char_count=result.char_count if result else 0,
        duration_ms=task.duration_ms,
        text=result.text if result else "",
        pages=[page_out(page) for page in result.pages] if result else [],
        error=ErrorBody(code=task.failure.code, message=task.failure.message)
        if task.failure
        else None,
    )


def summary_out(job: Job) -> SummaryOut:
    counts = job.counts()
    return SummaryOut(
        total=len(job.tasks),
        pending=counts[FileStatus.PENDING],
        processing=counts[FileStatus.PROCESSING],
        done=counts[FileStatus.DONE],
        failed=counts[FileStatus.FAILED],
        cancelled=counts[FileStatus.CANCELLED],
    )


def job_out(job: Job, *, low_confidence_below: float) -> JobOut:
    return JobOut(
        id=job.id,
        status="finished" if job.finished_at is not None else "running",
        created_at=job.created_at,
        finished_at=job.finished_at,
        cancel_requested=job.cancel_requested,
        folder=FolderOut(id=job.folder_id, name=job.folder_name),
        languages=list(job.options.languages),
        summary=summary_out(job),
        files=[file_result_out(t, low_confidence_below=low_confidence_below) for t in job.tasks],
    )


def export_out(job: Job, *, source_type: SourceType, low_confidence_below: float) -> ExportOut:
    return ExportOut(
        job_id=job.id,
        created_at=job.created_at,
        finished_at=job.finished_at,
        languages=list(job.options.languages),
        source=SourceOut(
            type=source_type,
            kind=job.link_kind,
            link=job.link,
            folder=FolderOut(id=job.folder_id, name=job.folder_name),
        ),
        summary=summary_out(job),
        files=[file_result_out(t, low_confidence_below=low_confidence_below) for t in job.tasks],
    )
