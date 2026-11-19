import pytest

from drive_text_extractor.domain.models import ExtractionMethod, ExtractionOptions
from drive_text_extractor.extractors.pdf import PdfExtractor
from tests.fakes import FakeOcrEngine
from tests.pdf_factory import make_pdf

OPTIONS = ExtractionOptions(languages=("fra", "eng"))
TYPED = "This page has a real text layer with plenty of characters."


@pytest.fixture
def ocr() -> FakeOcrEngine:
    return FakeOcrEngine(text="Scanned annex", confidence=82.0)


def test_typed_pages_never_reach_ocr(ocr: FakeOcrEngine) -> None:
    result = PdfExtractor(ocr=ocr).extract(make_pdf([TYPED, TYPED]), OPTIONS)

    assert result.method is ExtractionMethod.PDF_PARSER
    assert ocr.calls == []


def test_pages_without_text_layer_are_ocrd_page_by_page(ocr: FakeOcrEngine) -> None:
    result = PdfExtractor(ocr=ocr).extract(make_pdf([TYPED, None]), OPTIONS)

    typed, scanned = result.pages
    assert typed.method is ExtractionMethod.PDF_PARSER
    assert typed.text == TYPED
    assert scanned.method is ExtractionMethod.OCR
    assert scanned.text == "Scanned annex"
    assert scanned.confidence == 82.0
    assert result.method is ExtractionMethod.MIXED


def test_scanned_page_is_rendered_at_300_dpi_in_grayscale(ocr: FakeOcrEngine) -> None:
    PdfExtractor(ocr=ocr).extract(make_pdf([None]), OPTIONS)

    [call] = ocr.calls
    assert call.mode == "L"
    assert call.size[0] == 2550  # 8.5 in x 300 dpi
    assert call.languages == ("fra", "eng")


def test_pages_with_only_a_few_characters_count_as_scans(ocr: FakeOcrEngine) -> None:
    # Scans often carry a stamped page number in their text layer and nothing else.
    result = PdfExtractor(ocr=ocr, min_text_chars=20).extract(make_pdf(["- 3 -"]), OPTIONS)

    assert result.pages[0].method is ExtractionMethod.OCR


def test_keeps_the_text_layer_when_ocr_finds_nothing() -> None:
    blank_ocr = FakeOcrEngine(text="", confidence=None)

    result = PdfExtractor(ocr=blank_ocr).extract(make_pdf(["- 3 -"]), OPTIONS)

    assert result.pages[0].method is ExtractionMethod.PDF_PARSER
    assert result.pages[0].text == "- 3 -"


def test_oversized_pages_are_rendered_at_a_capped_resolution(ocr: FakeOcrEngine) -> None:
    poster = make_pdf([None], page_size=(5000, 5000))

    PdfExtractor(ocr=ocr, max_render_pixels=4_000_000).extract(poster, OPTIONS)

    [call] = ocr.calls
    width, height = call.size
    assert width * height <= 4_000_000 * 1.01


def test_without_ocr_engine_empty_pages_stay_empty() -> None:
    result = PdfExtractor().extract(make_pdf([None]), OPTIONS)

    assert result.pages[0].method is ExtractionMethod.PDF_PARSER
    assert result.pages[0].text == ""
