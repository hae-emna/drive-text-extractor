"""Value objects shared by every layer: what a source lists, and what an extractor returns."""

from dataclasses import dataclass
from enum import StrEnum
from statistics import fmean


@dataclass(frozen=True, slots=True)
class SourceFile:
    """A file as reported by a file source, before anything is downloaded."""

    id: str
    name: str
    mime_type: str
    size_bytes: int | None = None
    modified_time: str | None = None
    path: str = ""
    """Location inside the listed folder, e.g. ``invoices/2024/a.pdf``. Empty means top level."""

    @property
    def display_path(self) -> str:
        return self.path or self.name


@dataclass(frozen=True, slots=True)
class SkippedFile:
    """A file present in the folder that will not be offered for extraction, and why."""

    name: str
    mime_type: str
    reason: str


class LinkKind(StrEnum):
    """What a pasted link points to."""

    FOLDER = "folder"
    FILE = "file"


@dataclass(frozen=True, slots=True)
class FolderListing:
    folder_id: str
    folder_name: str
    files: tuple[SourceFile, ...]
    skipped: tuple[SkippedFile, ...] = ()
    truncated: bool = False
    """True when the source stopped listing at its item limit."""


class ExtractionMethod(StrEnum):
    PDF_PARSER = "pdf_parser"
    OCR = "ocr"
    MIXED = "mixed"
    """File-level only: some pages came from the text layer, others from OCR."""


@dataclass(frozen=True, slots=True)
class ExtractionOptions:
    languages: tuple[str, ...] = ("eng",)
    """Tesseract language codes, e.g. ``("fra", "eng")``. Ignored for pages with a text layer."""


@dataclass(frozen=True, slots=True)
class OcrOutput:
    text: str
    confidence: float | None
    """Mean word confidence (0-100), or ``None`` when no word was recognised."""


@dataclass(frozen=True, slots=True)
class PageText:
    number: int
    """1-based page number. Images are a single page."""
    method: ExtractionMethod
    text: str
    confidence: float | None = None
    """Mean OCR word confidence (0-100). ``None`` when the text came from a PDF text layer."""


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    pages: tuple[PageText, ...]

    def __post_init__(self) -> None:
        if not self.pages:
            raise ValueError("an extraction result needs at least one page")

    @property
    def text(self) -> str:
        """All pages joined with a blank line, skipping pages that produced no text."""
        return "\n\n".join(page.text for page in self.pages if page.text)

    @property
    def method(self) -> ExtractionMethod:
        methods = {page.method for page in self.pages}
        return methods.pop() if len(methods) == 1 else ExtractionMethod.MIXED

    @property
    def mean_confidence(self) -> float | None:
        scores = [page.confidence for page in self.pages if page.confidence is not None]
        return round(fmean(scores), 1) if scores else None

    @property
    def char_count(self) -> int:
        return len(self.text)
