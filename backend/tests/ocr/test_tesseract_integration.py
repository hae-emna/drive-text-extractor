"""Runs the real Tesseract binary. Skipped when it is not installed; CI and Docker install it."""

import shutil

import pytest
from PIL import Image, ImageDraw, ImageFont

from drive_text_extractor.domain.errors import OcrError
from drive_text_extractor.ocr.tesseract import TesseractEngine

pytestmark = [
    pytest.mark.ocr,
    pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract is not installed"),
]


def render_text(lines: list[str], size: int = 42) -> Image.Image:
    font = ImageFont.load_default(size=size)
    image = Image.new("L", (1500, 80 + 80 * len(lines)), color=255)
    draw = ImageDraw.Draw(image)
    for index, line in enumerate(lines):
        draw.text((40, 40 + 80 * index), line, font=font, fill=0)
    return image


def test_recognises_printed_text_with_high_confidence() -> None:
    image = render_text(["Invoice number 2026-001", "Total amount 120 TND"])

    output = TesseractEngine().recognize(image, ["eng"])

    assert "Invoice" in output.text
    assert "120" in output.text
    assert output.confidence is not None
    assert output.confidence > 60


@pytest.mark.parametrize("angle", [90, 180, 270])
def test_straightens_rotated_scans(angle: int) -> None:
    lines = [
        "Orientation detection needs a few lines of text",
        "so this paragraph is long enough for Tesseract",
        "Invoice number 2026-001 total amount 120 TND",
        "Thank you for your business and see you soon",
    ]
    rotated = render_text(lines).rotate(angle, expand=True, fillcolor=255)

    output = TesseractEngine(auto_rotate=True).recognize(rotated, ["eng"])

    assert "Invoice" in output.text
    assert "Tesseract" in output.text


def test_combines_language_packs() -> None:
    image = render_text(["Facture de Tunis", "Invoice from Tunis"])

    output = TesseractEngine().recognize(image, ["fra", "eng"])

    assert "Facture" in output.text
    assert "Invoice" in output.text


def test_blank_image_yields_no_text_and_no_confidence() -> None:
    output = TesseractEngine().recognize(Image.new("L", (600, 400), color=255), ["eng"])

    assert output.text == ""
    assert output.confidence is None


def test_unknown_language_pack_is_reported() -> None:
    with pytest.raises(OcrError, match="not installed"):
        TesseractEngine().recognize(render_text(["text"]), ["xyz"])


def test_lists_installed_language_packs() -> None:
    assert {"eng", "fra", "ara"} <= set(TesseractEngine.available_languages())
