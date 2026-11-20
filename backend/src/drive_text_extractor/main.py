"""Composition root: the one place that knows which concrete class implements each port.

Run with:  uvicorn drive_text_extractor.main:create_app --factory
"""

import logging
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from drive_text_extractor import __version__
from drive_text_extractor.api.errors import install_error_handlers
from drive_text_extractor.api.routes import router
from drive_text_extractor.config import OcrEngineName, Settings, SourceType
from drive_text_extractor.container import Container
from drive_text_extractor.domain.ports import FileSource, OcrEngine
from drive_text_extractor.drive.client import GoogleDriveSource
from drive_text_extractor.extractors.image import ImageExtractor
from drive_text_extractor.extractors.pdf import PdfExtractor
from drive_text_extractor.local.source import LocalFolderSource
from drive_text_extractor.ocr.rapid import RapidOcrEngine
from drive_text_extractor.ocr.routing import PreferredOcrEngine
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
    """Build the application. Tests pass fakes for the source and the OCR engine.

    ``ocr_engine`` replaces both OCR engines: the one for images and the one for scanned PDF pages.
    """
    settings = settings or Settings()
    _configure_logging(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as http:
            source, source_type = _file_source(settings, http, file_source)
            tesseract = TesseractEngine(
                timeout_seconds=settings.ocr_timeout_seconds,
                auto_rotate=settings.ocr_auto_rotate,
            )
            page_ocr = ocr_engine or tesseract
            image_ocr = ocr_engine or _image_ocr(settings, tesseract)
            languages = (
                tuple(installed_languages)
                if installed_languages is not None
                else tuple(TesseractEngine.available_languages())
            )
            container = build_container(
                settings, source, source_type, languages, page_ocr=page_ocr, image_ocr=image_ocr
            )
            app.state.container = container
            logger.info(
                "Started: source=%s, image OCR=%s, OCR languages=%s",
                source_type,
                settings.image_ocr_engine,
                languages,
            )
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
    return app


def build_container(
    settings: Settings,
    source: FileSource,
    source_type: SourceType,
    installed_languages: tuple[str, ...],
    *,
    page_ocr: OcrEngine,
    image_ocr: OcrEngine,
) -> Container:
    router = ExtractorRouter(
        [
            PdfExtractor(
                ocr=page_ocr,
                max_pages=settings.max_pdf_pages,
                min_text_chars=settings.pdf_ocr_min_chars,
                render_dpi=settings.pdf_render_dpi,
                max_render_pixels=settings.max_image_pixels,
            ),
            ImageExtractor(image_ocr, max_pixels=settings.max_image_pixels),
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


def _image_ocr(settings: Settings, tesseract: TesseractEngine) -> OcrEngine:
    """RapidOCR for photos and screenshots in the languages it reads, Tesseract for the rest.

    Scanned PDF pages keep Tesseract: they are pages, which its layout analysis handles well.
    """
    if settings.image_ocr_engine is OcrEngineName.TESSERACT:
        return tesseract
    rapid = RapidOcrEngine(
        models_dir=settings.ocr_models_dir,
        orient=tesseract.upright if settings.ocr_auto_rotate else None,
    )
    return PreferredOcrEngine(rapid, RapidOcrEngine.languages, fallback=tesseract)


def _file_source(
    settings: Settings, http: httpx.AsyncClient, override: FileSource | None
) -> tuple[FileSource, SourceType]:
    if override is not None:
        return override, settings.file_source
    if settings.file_source is SourceType.LOCAL:
        logger.info("Demo mode: reading folders under %s", settings.local_folder.resolve())
        local = LocalFolderSource(
            settings.local_folder,
            max_file_bytes=settings.max_file_bytes,
            max_items=settings.max_listed_files,
        )
        return local, SourceType.LOCAL
    api_key = settings.google_api_key.get_secret_value() if settings.google_api_key else None
    if api_key is None:
        logger.warning("GOOGLE_API_KEY is not set: listing Drive folders will fail")
    source = GoogleDriveSource(
        http,
        api_key,
        max_file_bytes=settings.max_file_bytes,
        max_items=settings.max_listed_files,
    )
    return source, SourceType.GOOGLE_DRIVE


def _configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    logging.getLogger("drive_text_extractor").setLevel(settings.log_level)
    # httpx logs every request at INFO; keep the application log readable.
    logging.getLogger("httpx").setLevel(logging.WARNING)
