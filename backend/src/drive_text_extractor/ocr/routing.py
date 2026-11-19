"""Choose an OCR engine by the languages a batch asks for."""

from collections.abc import Sequence

from PIL.Image import Image

from drive_text_extractor.domain.models import OcrOutput
from drive_text_extractor.domain.ports import OcrEngine


class PreferredOcrEngine:
    """Uses ``preferred`` when it reads every requested language, ``fallback`` otherwise."""

    def __init__(
        self, preferred: OcrEngine, languages: frozenset[str], fallback: OcrEngine
    ) -> None:
        self._preferred = preferred
        self._languages = languages
        self._fallback = fallback

    def recognize(self, image: Image, languages: Sequence[str]) -> OcrOutput:
        engine = self._preferred if set(languages) <= self._languages else self._fallback
        return engine.recognize(image, languages)
