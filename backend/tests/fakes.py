"""Test doubles for the domain ports. They let services be tested without network or OCR."""

from collections.abc import Sequence
from dataclasses import dataclass, field

from PIL.Image import Image

from drive_text_extractor.domain.models import OcrOutput


@dataclass
class RecordedOcrCall:
    size: tuple[int, int]
    mode: str
    languages: tuple[str, ...]


@dataclass
class FakeOcrEngine:
    """Returns canned text and records what it was asked to read."""

    text: str = "recognised text"
    confidence: float | None = 91.0
    calls: list[RecordedOcrCall] = field(default_factory=list)

    def recognize(self, image: Image, languages: Sequence[str]) -> OcrOutput:
        self.calls.append(RecordedOcrCall(image.size, image.mode, tuple(languages)))
        return OcrOutput(text=self.text, confidence=self.confidence)
