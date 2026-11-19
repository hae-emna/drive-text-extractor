"""A real scanned PDF (an image, no text layer) through pypdfium2 and the real Tesseract."""

import io
import shutil

import pytest
from PIL import Image, ImageDraw, ImageFont

from drive_text_extractor.domain.models import ExtractionMethod, ExtractionOptions
from drive_text_extractor.extractors.pdf import PdfExtractor
from drive_text_extractor.ocr.tesseract import TesseractEngine

pytestmark = [
    pytest.mark.ocr,
    pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract is not installed"),
]


def scanned_pdf(lines: list[str]) -> bytes:
    """What a scanner produces: a page that is only a picture of text."""
    page = Image.new("L", (1700, 2200), color=255)
    draw = ImageDraw.Draw(page)
    font = ImageFont.load_default(size=48)
    for index, line in enumerate(lines):
        draw.text((120, 150 + 90 * index), line, font=font, fill=0)
    buffer = io.BytesIO()
    page.save(buffer, format="PDF", resolution=200)
    return buffer.getvalue()


def test_scanned_pdf_is_read_through_ocr() -> None:
    data = scanned_pdf(["Scanned contract", "Signed in Nabeul on 12 November 2026"])

    result = PdfExtractor(ocr=TesseractEngine()).extract(data, ExtractionOptions(("eng",)))

    assert result.method is ExtractionMethod.OCR
    assert "contract" in result.text
    assert "Nabeul" in result.text
    assert result.mean_confidence is not None
