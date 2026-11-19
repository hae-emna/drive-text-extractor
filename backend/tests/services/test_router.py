import pytest

from drive_text_extractor.domain.errors import CorruptFileError, UnsupportedFileError
from drive_text_extractor.extractors.image import ImageExtractor
from drive_text_extractor.extractors.pdf import PdfExtractor
from drive_text_extractor.services.router import ExtractorRouter
from tests.fakes import FakeOcrEngine
from tests.images import png_bytes
from tests.pdf_factory import make_pdf


@pytest.fixture
def pdf() -> PdfExtractor:
    return PdfExtractor()


@pytest.fixture
def image() -> ImageExtractor:
    return ImageExtractor(FakeOcrEngine())


@pytest.fixture
def router(pdf: PdfExtractor, image: ImageExtractor) -> ExtractorRouter:
    return ExtractorRouter([pdf, image])


def test_routes_pdfs_to_the_pdf_extractor(router: ExtractorRouter, pdf: PdfExtractor) -> None:
    assert router.select(make_pdf(["x"])) is pdf


def test_routes_images_to_the_image_extractor(
    router: ExtractorRouter, image: ImageExtractor
) -> None:
    # select() never sees a name or MIME type: a PNG uploaded as "scan.pdf" still goes to OCR.
    assert router.select(png_bytes()) is image


def test_unknown_content_is_unsupported(router: ExtractorRouter) -> None:
    with pytest.raises(UnsupportedFileError):
        router.select(b"GIF89a\x01\x00")


def test_empty_file_is_reported_as_corrupt(router: ExtractorRouter) -> None:
    with pytest.raises(CorruptFileError, match="empty"):
        router.select(b"")


def test_supported_media_types_are_the_union_of_extractors(router: ExtractorRouter) -> None:
    assert router.supported_media_types == {"application/pdf", "image/png", "image/jpeg"}
    assert router.supports("image/jpeg")
    assert not router.supports("application/vnd.google-apps.document")


def test_needs_at_least_one_extractor() -> None:
    with pytest.raises(ValueError, match="at least one"):
        ExtractorRouter([])
