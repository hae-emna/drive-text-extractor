"""Application settings.

Every tunable is read here, once, from environment variables or an optional ``.env`` file.
The rest of the code receives a ``Settings`` instance and never touches ``os.environ``.
"""

from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from drive_text_extractor.domain.ports import DEFAULT_MAX_LISTED_FILES
from drive_text_extractor.domain.units import BYTES_PER_MB, PIXELS_PER_MEGAPIXEL
from drive_text_extractor.extractors.image import DEFAULT_MAX_MEGAPIXELS
from drive_text_extractor.extractors.pdf import (
    DEFAULT_MAX_PAGES,
    DEFAULT_MIN_TEXT_CHARS,
    DEFAULT_RENDER_DPI,
)
from drive_text_extractor.ocr.tesseract import DEFAULT_TIMEOUT_SECONDS
from drive_text_extractor.services.batch_runner import DEFAULT_CONCURRENCY


class SourceType(StrEnum):
    """Where folders are read from."""

    GOOGLE_DRIVE = "google_drive"
    LOCAL = "local"
    """A folder on the server: a demo mode that needs no API key."""


class OcrEngineName(StrEnum):
    RAPIDOCR = "rapidocr"
    TESSERACT = "tesseract"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # The repository-level .env is shared with docker compose; a backend-local one wins.
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    file_source: SourceType = SourceType.GOOGLE_DRIVE
    """Where folders are read from. 'local' is a demo mode that needs no API key."""

    google_api_key: SecretStr | None = None
    """Google Cloud API key with the Drive API enabled. Only needed for the Drive source."""

    local_folder: Path = Path("../samples/input")
    """Root folder of the 'local' source. Links then look like 'local:' or 'local:subfolder'."""

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    static_dir: Path | None = None
    """Built web page to serve at ``/``. Unset during development, when Vite serves it."""

    # --- Batch processing ---
    batch_concurrency: int = Field(default=DEFAULT_CONCURRENCY, ge=1, le=16)
    """Files processed at the same time. OCR is CPU-bound: keep it near the number of cores."""

    low_confidence_threshold: float = Field(default=60.0, ge=0, le=100)
    """OCR results with a mean word confidence below this are flagged in the UI and export."""

    # --- Source limits ---
    max_file_size_mb: int = Field(default=25, ge=1, le=500)
    """Files above this size are refused before (or while) downloading."""

    max_listed_files: int = Field(default=DEFAULT_MAX_LISTED_FILES, ge=1)
    """Listing stops after this many files and the folder is flagged as truncated."""

    # --- Extraction limits ---
    max_pdf_pages: int = Field(default=DEFAULT_MAX_PAGES, ge=1)
    """PDFs with more pages are refused, to bound processing time per file."""

    pdf_ocr_min_chars: int = Field(default=DEFAULT_MIN_TEXT_CHARS, ge=0)
    """PDF pages whose text layer has fewer visible characters are treated as scans and OCR'd."""

    pdf_render_dpi: int = Field(default=DEFAULT_RENDER_DPI, ge=72, le=600)
    """Resolution at which scanned PDF pages are rendered for OCR."""

    max_image_megapixels: int = Field(default=DEFAULT_MAX_MEGAPIXELS, ge=1)
    """Images above this size are refused before decoding (decompression-bomb guard)."""

    ocr_timeout_seconds: int = Field(default=DEFAULT_TIMEOUT_SECONDS, ge=5)
    """Tesseract is stopped if one image or page takes longer than this."""

    ocr_auto_rotate: bool = True
    """Detect and fix sideways or upside-down scans before OCR (costs one extra Tesseract pass)."""

    image_ocr_engine: OcrEngineName = OcrEngineName.RAPIDOCR
    """Engine for PNG and JPEG files. RapidOCR finds text anywhere in photos and screenshots and
    reads English and French; images in other languages, and scanned PDF pages, use Tesseract."""

    ocr_models_dir: Path | None = None
    """Where RapidOCR keeps its models. Unset: inside the installed package, fetched on first use.
    The Docker image sets it to a folder filled at build time."""

    @property
    def max_file_bytes(self) -> int:
        return self.max_file_size_mb * BYTES_PER_MB

    @property
    def max_image_pixels(self) -> int:
        return self.max_image_megapixels * PIXELS_PER_MEGAPIXEL
