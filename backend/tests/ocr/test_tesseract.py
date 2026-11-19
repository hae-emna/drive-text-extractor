"""TesseractEngine behaviour that does not need the binary: parsing and error mapping."""

from typing import Any

import pytesseract
import pytest
from PIL import Image

from drive_text_extractor.domain.errors import OcrError, OcrTimeoutError
from drive_text_extractor.ocr import tesseract as tesseract_module
from drive_text_extractor.ocr.tesseract import TesseractEngine, mean_word_confidence

HEADER = (
    "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext"
)


def tsv(*rows: tuple[int, float, str]) -> str:
    lines = [HEADER]
    lines += [f"{level}\t1\t1\t1\t1\t1\t0\t0\t10\t10\t{conf}\t{text}" for level, conf, text in rows]
    return "\n".join(lines)


def test_confidence_averages_recognised_words_only() -> None:
    data = tsv((1, -1, ""), (4, -1, ""), (5, 90.0, "Total"), (5, 70.5, "120"), (5, 95.0, " "))

    assert mean_word_confidence(data) == 80.2


def test_confidence_is_none_when_nothing_was_recognised() -> None:
    assert mean_word_confidence(tsv((1, -1, ""), (5, -1, ""))) is None
    assert mean_word_confidence("") is None


def test_quotes_in_words_do_not_break_parsing() -> None:
    assert mean_word_confidence(tsv((5, 88.0, '"quoted'), (5, 92.0, "word"))) == 90.0


@pytest.fixture
def image() -> Image.Image:
    return Image.new("L", (10, 10), color=255)


def fail_with(monkeypatch: pytest.MonkeyPatch, error: Exception) -> None:
    def run(*_: Any, **__: Any) -> list[str]:
        raise error

    monkeypatch.setattr(tesseract_module.pytesseract, "run_and_get_multiple_output", run)


def test_returns_normalised_text_and_confidence(
    monkeypatch: pytest.MonkeyPatch, image: Image.Image
) -> None:
    calls: list[dict[str, Any]] = []

    def run(_: Image.Image, **kwargs: Any) -> list[str]:
        calls.append(kwargs)
        return ["Total \r\n120 TND\n\n\n", tsv((5, 80.0, "Total"), (5, 90.0, "120"))]

    monkeypatch.setattr(tesseract_module.pytesseract, "run_and_get_multiple_output", run)

    output = TesseractEngine(timeout_seconds=7).recognize(image, ["fra", "eng"])

    assert output.text == "Total\n120 TND"
    assert output.confidence == 85.0
    assert calls == [{"extensions": ["txt", "tsv"], "lang": "fra+eng", "timeout": 7}]


def test_missing_binary_is_explained(monkeypatch: pytest.MonkeyPatch, image: Image.Image) -> None:
    fail_with(monkeypatch, pytesseract.TesseractNotFoundError())

    with pytest.raises(OcrError, match="not installed"):
        TesseractEngine().recognize(image, ["eng"])


def test_missing_language_pack_is_explained(
    monkeypatch: pytest.MonkeyPatch, image: Image.Image
) -> None:
    fail_with(monkeypatch, pytesseract.TesseractError(1, "Failed loading language 'ara'"))

    with pytest.raises(OcrError, match="'ara' is not installed"):
        TesseractEngine().recognize(image, ["ara"])


def test_timeout_has_its_own_error(monkeypatch: pytest.MonkeyPatch, image: Image.Image) -> None:
    fail_with(monkeypatch, RuntimeError("Tesseract process timeout"))

    with pytest.raises(OcrTimeoutError):
        TesseractEngine().recognize(image, ["eng"])
