"""RapidOcrEngine behaviour with a fake recogniser: no models needed."""

from dataclasses import dataclass, field
from typing import Any

import pytest
from PIL import Image

from drive_text_extractor.domain.errors import OcrError
from drive_text_extractor.ocr.rapid import RapidOcrEngine, text_lines


def box(left: float, top: float, width: float = 200, height: float = 20) -> list[list[float]]:
    right, bottom = left + width, top + height
    return [[left, top], [right, top], [right, bottom], [left, bottom]]


@dataclass
class Output:
    """The shape of RapidOCR's output: parallel boxes, texts and scores, or None for nothing."""

    boxes: Any = None
    txts: tuple[str, ...] | None = None
    scores: tuple[float, ...] | None = None


@dataclass
class FakeRecognizer:
    output: Output
    seen: list[Image.Image] = field(default_factory=list)

    def __call__(self, image: Image.Image) -> Output:
        self.seen.append(image)
        return self.output


CAFE = Output(
    boxes=[box(0, 0), box(0, 30), box(0, 300), box(300, 300)],
    txts=("modern circle", "café and concept store", "0:01", "0:09"),
    scores=(1.0, 0.94, 1.0, 1.0),
)


@pytest.fixture
def image() -> Image.Image:
    return Image.new("L", (40, 20), 255)


def engine_for(recognizer: FakeRecognizer, **options: Any) -> RapidOcrEngine:
    return RapidOcrEngine(recognizer_factory=lambda: recognizer, **options)


def test_reads_lines_in_reading_order(image: Image.Image) -> None:
    output = engine_for(FakeRecognizer(CAFE)).recognize(image, ["eng", "fra"])

    assert output.text == "modern circle\ncafé and concept store\n\n0:01 0:09"
    # (13 x 1.0 + 22 x 0.94 + 4 x 1.0 + 4 x 1.0) / 43 characters
    assert output.confidence == 96.9


def test_gives_the_recogniser_an_rgb_image(image: Image.Image) -> None:
    recognizer = FakeRecognizer(CAFE)

    engine_for(recognizer).recognize(image, ["eng"])

    assert recognizer.seen[0].mode == "RGB"


def test_straightens_the_image_first(image: Image.Image) -> None:
    recognizer = FakeRecognizer(CAFE)
    rotated: list[tuple[int, int]] = []

    def orient(img: Image.Image) -> Image.Image:
        rotated.append(img.size)
        return img.rotate(90, expand=True)

    engine_for(recognizer, orient=orient).recognize(image, ["eng"])

    assert rotated == [(40, 20)]
    assert recognizer.seen[0].size == (20, 40)


def test_drops_lines_without_letters_or_digits() -> None:
    noisy = Output(boxes=[box(0, 0), box(0, 30), box(0, 60)], txts=("..", "with us", "*"))
    noisy.scores = (0.76, 0.98, 0.93)

    assert [line.text for line in text_lines(noisy)] == ["with us"]


def test_an_image_without_text_gives_no_text_and_no_confidence(image: Image.Image) -> None:
    output = engine_for(FakeRecognizer(Output())).recognize(image, ["eng"])

    assert output.text == ""
    assert output.confidence is None


def test_loads_the_recogniser_once(image: Image.Image) -> None:
    loads: list[int] = []

    def factory() -> FakeRecognizer:
        loads.append(1)
        return FakeRecognizer(CAFE)

    engine = RapidOcrEngine(recognizer_factory=factory)
    engine.recognize(image, ["eng"])
    engine.recognize(image, ["fra"])

    assert loads == [1]


def test_refuses_languages_it_cannot_read(image: Image.Image) -> None:
    with pytest.raises(OcrError, match="cannot read: ara"):
        engine_for(FakeRecognizer(CAFE)).recognize(image, ["eng", "ara"])


def test_engine_failures_become_ocr_errors(image: Image.Image) -> None:
    def broken() -> FakeRecognizer:
        raise RuntimeError("model download failed")

    with pytest.raises(OcrError, match="Text recognition failed"):
        RapidOcrEngine(recognizer_factory=broken).recognize(image, ["eng"])
