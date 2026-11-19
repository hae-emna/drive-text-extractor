import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c
import pytest

from drive_text_extractor.domain.errors import (
    CorruptFileError,
    EncryptedFileError,
    TooManyPagesError,
)
from drive_text_extractor.domain.models import ExtractionMethod, ExtractionOptions
from drive_text_extractor.extractors import pdf as pdf_module
from drive_text_extractor.extractors.pdf import PdfExtractor
from tests.pdf_factory import make_pdf

OPTIONS = ExtractionOptions(languages=("eng",))


@pytest.fixture
def extractor() -> PdfExtractor:
    return PdfExtractor(max_pages=5)


def test_declares_the_pdf_media_type(extractor: PdfExtractor) -> None:
    assert extractor.media_types == {"application/pdf"}


@pytest.mark.parametrize(
    ("head", "accepted"),
    [
        (b"%PDF-1.7\n...", True),
        (b"\xef\xbb\xbfjunk before header %PDF-1.4", True),
        (b"\x89PNG\r\n\x1a\n", False),
        (b"\xff\xd8\xff\xe0", False),
        (b"", False),
    ],
)
def test_recognises_pdfs_by_content(extractor: PdfExtractor, head: bytes, accepted: bool) -> None:
    assert extractor.accepts(head) is accepted


def test_extracts_the_text_layer_page_by_page(extractor: PdfExtractor) -> None:
    data = make_pdf(["Invoice 2026-001\nTotal: 120.00 TND", "Second page"])

    result = extractor.extract(data, OPTIONS)

    assert [page.number for page in result.pages] == [1, 2]
    assert result.pages[0].text == "Invoice 2026-001\nTotal: 120.00 TND"
    assert result.pages[1].text == "Second page"
    assert result.method is ExtractionMethod.PDF_PARSER
    assert result.mean_confidence is None


def test_page_without_text_layer_yields_empty_text(extractor: PdfExtractor) -> None:
    result = extractor.extract(make_pdf(["Cover", None]), OPTIONS)

    assert result.pages[1].text == ""
    assert result.text == "Cover"


def test_rejects_documents_over_the_page_limit(extractor: PdfExtractor) -> None:
    with pytest.raises(TooManyPagesError, match="6 pages; the limit is 5"):
        extractor.extract(make_pdf(["page"] * 6), OPTIONS)


@pytest.mark.parametrize("data", [b"%PDF-1.4 but nothing else", b"plain text", b""])
def test_unreadable_documents_are_corrupt(extractor: PdfExtractor, data: bytes) -> None:
    with pytest.raises(CorruptFileError):
        extractor.extract(data, OPTIONS)


def test_password_protected_documents_are_reported_as_such(
    extractor: PdfExtractor, monkeypatch: pytest.MonkeyPatch
) -> None:
    def locked(_: bytes) -> pdfium.PdfDocument:
        raise pdfium.PdfiumError("Incorrect password error", err_code=pdfium_c.FPDF_ERR_PASSWORD)

    monkeypatch.setattr(pdf_module.pdfium, "PdfDocument", locked)

    with pytest.raises(EncryptedFileError):
        extractor.extract(b"%PDF-1.7", OPTIONS)
