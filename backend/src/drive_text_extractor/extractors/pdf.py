"""PDF extractor built on pypdfium2 (PDFium bindings, Apache-2.0 / BSD-3-Clause)."""

import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c

from drive_text_extractor.domain.errors import (
    CorruptFileError,
    EncryptedFileError,
    TooManyPagesError,
)
from drive_text_extractor.domain.models import (
    ExtractionMethod,
    ExtractionOptions,
    ExtractionResult,
    PageText,
)
from drive_text_extractor.extractors.text import normalize_text

PDF_SIGNATURE = b"%PDF-"
_SIGNATURE_WINDOW = 1024
"""The PDF spec tolerates junk before the header; readers look for it in the first 1 KiB."""


class PdfExtractor:
    """Reads the embedded text layer of each page."""

    media_types = frozenset({"application/pdf"})

    def __init__(self, *, max_pages: int = 200) -> None:
        self._max_pages = max_pages

    def accepts(self, head: bytes) -> bool:
        return PDF_SIGNATURE in head[:_SIGNATURE_WINDOW]

    def extract(self, data: bytes, options: ExtractionOptions) -> ExtractionResult:
        document = _open(data)
        try:
            page_count = len(document)
            if page_count == 0:
                raise CorruptFileError("This PDF has no pages.")
            if page_count > self._max_pages:
                raise TooManyPagesError(
                    f"This PDF has {page_count} pages; the limit is {self._max_pages}."
                )
            pages = tuple(self._read_page(document, index) for index in range(page_count))
        finally:
            document.close()
        return ExtractionResult(pages=pages)

    def _read_page(self, document: pdfium.PdfDocument, index: int) -> PageText:
        try:
            page = document[index]
            try:
                text_page = page.get_textpage()
                try:
                    raw = text_page.get_text_range()
                finally:
                    text_page.close()
            finally:
                page.close()
        except pdfium.PdfiumError as exc:
            raise CorruptFileError(f"Page {index + 1} of this PDF is damaged.") from exc
        return PageText(
            number=index + 1, method=ExtractionMethod.PDF_PARSER, text=normalize_text(raw)
        )


def _open(data: bytes) -> pdfium.PdfDocument:
    try:
        return pdfium.PdfDocument(data)
    except pdfium.PdfiumError as exc:
        if exc.err_code == pdfium_c.FPDF_ERR_PASSWORD:
            raise EncryptedFileError() from exc
        raise CorruptFileError() from exc
