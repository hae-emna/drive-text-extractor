"""Composition root: the one place that knows which concrete class implements each port.

Run with:  uvicorn drive_text_extractor.main:create_app --factory
"""

import logging
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from drive_text_extractor import __version__
from drive_text_extractor.api.errors import install_error_handlers
from drive_text_extractor.api.routes import router
from drive_text_extractor.config import Settings
from drive_text_extractor.container import Container, SourceType
from drive_text_extractor.domain.ports import FileSource, OcrEngine
from drive_text_extractor.drive.client import GoogleDriveSource
from drive_text_extractor.extractors.image import ImageExtractor
from drive_text_extractor.extractors.pdf import PdfExtractor
from drive_text_extractor.ocr.tesseract import TesseractEngine
from drive_text_extractor.services.batch_runner import BatchRunner
from drive_text_extractor.services.folder_browser import FolderBrowser
from drive_text_extractor.services.job_service import JobService
from drive_text_extractor.services.job_store import InMemoryJobStore
from drive_text_extractor.services.router import ExtractorRouter

logger = logging.getLogger(__name__)

_HTTP_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


def create_app(
    settings: Settings | None = None,
    *,
    file_source: FileSource | None = None,
    ocr_engine: OcrEngine | None = None,
    installed_languages: Sequence[str] | None = None,
) -> FastAPI:
    """Build the application. Tests pass fakes for the source and the OCR engine."""
    settings = settings or Settings()
    _configure_logging(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as http:
            source, source_type = _file_source(settings, http, file_source)
            ocr = ocr_engine or TesseractEngine(
                timeout_seconds=settings.ocr_timeout_seconds,
                auto_rotate=settings.ocr_auto_rotate,
            )
            languages = (
                tuple(installed_languages)
                if installed_languages is not None
                else tuple(TesseractEngine.available_languages())
            )
            container = build_container(settings, source, source_type, ocr, languages)
            app.state.container = container
            logger.info("Started: source=%s, OCR languages=%s", source_type, languages)
            yield
            await container.jobs.shutdown()

    app = FastAPI(
        title="Drive Text Extractor",
        version=__version__,
        summary="Extract text from the PDFs and images of a public Google Drive folder.",
        lifespan=lifespan,
    )
    install_error_handlers(app)
    app.include_router(router, prefix="/api")
    if settings.static_dir is not None and settings.static_dir.is_dir():
        # Mounted last so /api routes take precedence over files.
        app.mount("/", StaticFiles(directory=settings.static_dir, html=True), name="web")
    return app


def build_container(
    settings: Settings,
    source: FileSource,
    source_type: SourceType,
    ocr: OcrEngine,
    installed_languages: tuple[str, ...],
) -> Container:
    router = ExtractorRouter(
        [
            PdfExtractor(
                ocr=ocr,
                max_pages=settings.max_pdf_pages,
                min_text_chars=settings.pdf_ocr_min_chars,
                render_dpi=settings.pdf_render_dpi,
                max_render_pixels=settings.max_image_megapixels * 1_000_000,
            ),
            ImageExtractor(ocr, max_pixels=settings.max_image_megapixels * 1_000_000),
        ]
    )
    browser = FolderBrowser(source, router)
    runner = BatchRunner(source, router, concurrency=settings.batch_concurrency)
    jobs = JobService(browser, runner, InMemoryJobStore())
    return Container(
        settings=settings,
        browser=browser,
        jobs=jobs,
        source_type=source_type,
        installed_languages=installed_languages,
    )


def _file_source(
    settings: Settings, http: httpx.AsyncClient, override: FileSource | None
) -> tuple[FileSource, SourceType]:
    if override is not None:
        return override, "google_drive"
    api_key = settings.google_api_key.get_secret_value() if settings.google_api_key else None
    if api_key is None:
        logger.warning("GOOGLE_API_KEY is not set: listing Drive folders will fail")
    source = GoogleDriveSource(
        http,
        api_key,
        max_file_bytes=settings.max_file_bytes,
        max_items=settings.max_listed_files,
    )
    return source, "google_drive"


def _configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    logging.getLogger("drive_text_extractor").setLevel(settings.log_level)
    # httpx logs every request at INFO; keep the application log readable.
    logging.getLogger("httpx").setLevel(logging.WARNING)
