"""Runs the real RapidOCR models.

They are fetched on first use (about 14 MB). The Docker image bakes them in and CI caches them,
both through ``OCR_MODELS_DIR``.
"""

import shutil
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

from drive_text_extractor.config import Settings
from drive_text_extractor.ocr.preprocess import prepare_for_ocr
from drive_text_extractor.ocr.rapid import RapidOcrEngine
from drive_text_extractor.ocr.tesseract import TesseractEngine

pytestmark = pytest.mark.ocr


@pytest.fixture(scope="module")
def engine() -> RapidOcrEngine:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    return RapidOcrEngine(models_dir=settings.ocr_models_dir)


# Pillow's built-in font has no accented letters; these do. Docker and CI have DejaVu.
FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"]
FONT = next((path for path in FONTS if Path(path).is_file()), None)
needs_font = pytest.mark.skipif(FONT is None, reason="No TrueType font with accents found")


def font(size: int) -> ImageFont.FreeTypeFont:
    assert FONT is not None
    return ImageFont.truetype(FONT, size)


def screenshot() -> Image.Image:
    """Like a phone screenshot of a video: light captions of several sizes on a dark, busy scene."""
    image = Image.new("RGB", (720, 1280), (38, 52, 46))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 300, 720, 640), fill=(196, 168, 112))  # a lit shop front
    draw.text((60, 340), "modern circle", font=font(72), fill=(35, 30, 25))
    draw.text((60, 440), "café and concept store", font=font(40), fill=(35, 30, 25))
    draw.text((90, 860), "Spend the day with us", font=font(48), fill=(250, 238, 190))
    draw.text((40, 1190), "0:01", font=font(30), fill=(240, 240, 240))
    draw.text((600, 1190), "0:09", font=font(30), fill=(240, 240, 240))
    return image


@needs_font
def test_reads_text_scattered_over_a_picture(engine: RapidOcrEngine) -> None:
    output = engine.recognize(prepare_for_ocr(screenshot()), ["eng", "fra"])

    for text in ("modern circle", "café and concept store", "Spend the day with us"):
        assert text in output.text
    assert "0:01 0:09" in output.text
    assert output.confidence is not None
    assert output.confidence > 80


@needs_font
def test_keeps_french_accents(engine: RapidOcrEngine) -> None:
    image = Image.new("L", (1400, 260), 255)
    draw = ImageDraw.Draw(image)
    draw.text((40, 40), "Livré le 14 novembre à Hammamet", font=font(56), fill=0)
    draw.text((40, 150), "Reçu en bon état par le client", font=font(56), fill=0)

    output = engine.recognize(image, ["fra"])

    assert "Livré le 14 novembre à Hammamet" in output.text
    assert "Reçu en bon état" in output.text


def test_a_blank_image_has_no_text(engine: RapidOcrEngine) -> None:
    output = engine.recognize(Image.new("L", (600, 400), 255), ["eng"])

    assert output.text == ""
    assert output.confidence is None


@needs_font
@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract is not installed")
def test_reads_a_sideways_page_in_order() -> None:
    lines = [
        "Orientation detection needs a few lines of text",
        "so this paragraph is long enough for Tesseract",
        "Invoice number 2026-001 total amount 120 TND",
    ]
    page = Image.new("L", (1500, 80 + 80 * len(lines)), 255)
    draw = ImageDraw.Draw(page)
    for index, text in enumerate(lines):
        draw.text((40, 40 + 80 * index), text, font=font(42), fill=0)
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    engine = RapidOcrEngine(models_dir=settings.ocr_models_dir, orient=TesseractEngine().upright)

    output = engine.recognize(page.rotate(90, expand=True, fillcolor=255), ["eng"])

    assert output.text.splitlines()[0].startswith("Orientation detection")
    assert output.text.splitlines()[-1].endswith("120 TND")
