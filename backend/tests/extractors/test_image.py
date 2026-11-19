import pytest
from PIL import Image

from drive_text_extractor.domain.errors import CorruptFileError, ImageTooLargeError
from drive_text_extractor.domain.models import ExtractionMethod, ExtractionOptions
from drive_text_extractor.extractors.image import ImageExtractor
from tests.fakes import FakeOcrEngine
from tests.images import encode, png_bytes

OPTIONS = ExtractionOptions(languages=("ara", "fra"))


@pytest.fixture
def ocr() -> FakeOcrEngine:
    return FakeOcrEngine(text="فاتورة Facture", confidence=77.5)


@pytest.fixture
def extractor(ocr: FakeOcrEngine) -> ImageExtractor:
    return ImageExtractor(ocr, max_pixels=4_000_000)


def test_declares_png_and_jpeg(extractor: ImageExtractor) -> None:
    assert extractor.media_types == {"image/png", "image/jpeg"}


@pytest.mark.parametrize(
    ("head", "accepted"),
    [
        (png_bytes()[:16], True),
        (encode(Image.new("RGB", (8, 8)), "JPEG")[:16], True),
        (b"%PDF-1.7", False),
        (b"GIF89a", False),
        (b"", False),
    ],
)
def test_recognises_images_by_content(
    extractor: ImageExtractor, head: bytes, accepted: bool
) -> None:
    assert extractor.accepts(head) is accepted


def test_returns_one_ocr_page_with_engine_text_and_confidence(
    extractor: ImageExtractor, ocr: FakeOcrEngine
) -> None:
    result = extractor.extract(png_bytes(), OPTIONS)

    assert len(result.pages) == 1
    page = result.pages[0]
    assert page.number == 1
    assert page.method is ExtractionMethod.OCR
    assert page.text == ocr.text
    assert page.confidence == 77.5


def test_engine_receives_the_prepared_image_and_languages(
    extractor: ImageExtractor, ocr: FakeOcrEngine
) -> None:
    extractor.extract(encode(Image.new("RGBA", (400, 200)), "PNG"), OPTIONS)

    [call] = ocr.calls
    assert call.mode == "L"
    assert call.size == (1200, 600)
    assert call.languages == ("ara", "fra")


@pytest.mark.parametrize(
    "data",
    [
        b"\x89PNG\r\n\x1a\nnot really a png",
        png_bytes()[:-40],
        b"\xff\xd8\xff garbage",
    ],
    ids=["bad-body", "truncated", "bad-jpeg"],
)
def test_damaged_images_are_corrupt(extractor: ImageExtractor, data: bytes) -> None:
    with pytest.raises(CorruptFileError):
        extractor.extract(data, OPTIONS)


def test_refuses_images_over_the_pixel_limit_before_decoding(
    extractor: ImageExtractor, ocr: FakeOcrEngine
) -> None:
    with pytest.raises(ImageTooLargeError, match="3000 x 2000 pixels"):
        extractor.extract(png_bytes(3000, 2000, mode="L"), OPTIONS)

    assert ocr.calls == []
