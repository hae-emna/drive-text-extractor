"""PDF extractor built on pypdfium2 (PDFium bindings, Apache-2.0 / BSD-3-Clause)."""

import math

import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c
from PIL.Image import Image

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
from drive_text_extractor.domain.ports import OcrEngine
from drive_text_extractor.extractors.text import normalize_text

PDF_SIGNATURE = b"%PDF-"
_SIGNATURE_WINDOW = 1024
"""The PDF spec tolerates junk before the header; readers look for it in the first 1 KiB."""


_POINTS_PER_INCH = 72


class PdfExtractor:
    """Reads each page's text layer, and OCRs the pages that have none (scans).

    The decision is made per page because real documents mix typed pages with scanned ones.
    Without an OCR engine, pages without a text layer simply come back empty.
    """

    media_types = frozenset({"application/pdf"})

    def __init__(
        self,
        *,
        ocr: OcrEngine | None = None,
        max_pages: int = 200,
        min_text_chars: int = 20,
        render_dpi: int = 300,
        max_render_pixels: int = 40_000_000,
    ) -> None:
        self._ocr = ocr
        self._max_pages = max_pages
        self._min_text_chars = min_text_chars
        self._render_dpi = render_dpi
        self._max_render_pixels = max_render_pixels

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
            pages = tuple(self._read_page(document, index, options) for index in range(page_count))
        finally:
            document.close()
        return ExtractionResult(pages=pages)

    def _read_page(
        self, document: pdfium.PdfDocument, index: int, options: ExtractionOptions
    ) -> PageText:
        number = index + 1
        ocr = self._ocr
        try:
            page = document[index]
            try:
                text = normalize_text(_text_layer(page))
                if ocr is None or _visible_chars(text) >= self._min_text_chars:
                    return PageText(number=number, method=ExtractionMethod.PDF_PARSER, text=text)
                image = self._render(page)
            finally:
                page.close()
        except pdfium.PdfiumError as exc:
            raise CorruptFileError(f"Page {number} of this PDF is damaged.") from exc

        output = ocr.recognize(image, options.languages)
        if not output.text and text:
            # OCR found nothing where the text layer had a little: keep what we had.
            return PageText(number=number, method=ExtractionMethod.PDF_PARSER, text=text)
        return PageText(
            number=number,
            method=ExtractionMethod.OCR,
            text=output.text,
            confidence=output.confidence,
        )

    def _render(self, page: pdfium.PdfPage) -> Image:
        width, height = page.get_size()
        scale = self._render_dpi / _POINTS_PER_INCH
        if width * height * scale * scale > self._max_render_pixels:
            # Oversized page (poster, plan): lower the resolution instead of exhausting memory.
            scale = math.sqrt(self._max_render_pixels / (width * height))
        bitmap = page.render(scale=scale, grayscale=True)
        try:
            image: Image = bitmap.to_pil().copy()
        finally:
            bitmap.close()
        return image


def _text_layer(page: pdfium.PdfPage) -> str:
    text_page = page.get_textpage()
    try:
        raw: str = text_page.get_text_range()
    finally:
        text_page.close()
    return raw


def _visible_chars(text: str) -> int:
    return sum(1 for char in text if not char.isspace())


def _open(data: bytes) -> pdfium.PdfDocument:
    try:
        return pdfium.PdfDocument(data)
    except pdfium.PdfiumError as exc:
        if exc.err_code == pdfium_c.FPDF_ERR_PASSWORD:
            raise EncryptedFileError() from exc
        raise CorruptFileError() from exc
