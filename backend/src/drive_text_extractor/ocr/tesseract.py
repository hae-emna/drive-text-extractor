"""Tesseract implementation of the ``OcrEngine`` port.

Tesseract (Apache-2.0) is called through pytesseract (Apache-2.0), which runs the ``tesseract``
binary in a subprocess. The subprocess releases the GIL, so several files can be recognised in
parallel from a thread pool.
"""

import csv
import io
import logging
from collections.abc import Sequence
from statistics import fmean

import pytesseract
from PIL.Image import Image

from drive_text_extractor.domain.errors import OcrError, OcrTimeoutError
from drive_text_extractor.domain.models import OcrOutput
from drive_text_extractor.extractors.text import normalize_text

logger = logging.getLogger(__name__)


DEFAULT_TIMEOUT_SECONDS = 120

_ORIENTATION_PACK = "osd"
"""Tesseract's orientation and script detection data, listed as a language but not one."""
_WHITE = 255

_MIN_ORIENTATION_CONFIDENCE = 2.0
"""Below this, Tesseract's orientation guess is noise (its own docs suggest ~2 as a floor)."""


class TesseractEngine:
    def __init__(
        self, *, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS, auto_rotate: bool = True
    ) -> None:
        self._timeout = timeout_seconds
        self._auto_rotate = auto_rotate

    def recognize(self, image: Image, languages: Sequence[str]) -> OcrOutput:
        language_spec = "+".join(languages)
        if self._auto_rotate:
            image = self.upright(image)
        try:
            # One Tesseract run produces both the plain text and the per-word TSV.
            text, tsv = pytesseract.run_and_get_multiple_output(
                image, extensions=["txt", "tsv"], lang=language_spec, timeout=self._timeout
            )
        except pytesseract.TesseractNotFoundError as exc:
            raise OcrError("The OCR engine (Tesseract) is not installed on the server.") from exc
        except pytesseract.TesseractError as exc:
            raise OcrError(_explain(exc, language_spec)) from exc
        except RuntimeError as exc:
            # pytesseract signals a timeout with a bare RuntimeError.
            if "timeout" in str(exc).lower():
                raise OcrTimeoutError() from exc
            raise OcrError() from exc
        return OcrOutput(text=normalize_text(text), confidence=mean_word_confidence(tsv))

    def upright(self, image: Image) -> Image:
        """Rotate sideways or upside-down scans using Tesseract's orientation detection.

        Public because the image OCR engine straightens its input the same way.
        """
        try:
            orientation = pytesseract.image_to_osd(
                image, output_type=pytesseract.Output.DICT, timeout=self._timeout
            )
        except (pytesseract.TesseractError, pytesseract.TesseractNotFoundError, RuntimeError):
            # Too little text to decide, or detection failed: recognise the image as it is
            # (a missing binary is reported by the recognition call itself).
            return image
        angle = int(orientation.get("rotate", 0))
        if (
            angle == 0
            or float(orientation.get("orientation_conf", 0)) < _MIN_ORIENTATION_CONFIDENCE
        ):
            return image
        logger.debug("Rotating image by %s degrees before OCR", angle)
        # OSD reports a clockwise correction; Pillow rotates counter-clockwise.
        return image.rotate(-angle, expand=True, fillcolor=_WHITE)

    @staticmethod
    def available_languages() -> list[str]:
        """Installed language packs, or an empty list when Tesseract is missing."""
        try:
            languages: list[str] = pytesseract.get_languages()
        except (pytesseract.TesseractNotFoundError, pytesseract.TesseractError, OSError):
            logger.warning("Tesseract is not available; OCR will fail")
            return []
        return sorted(language for language in languages if language != _ORIENTATION_PACK)


def mean_word_confidence(tsv: str) -> float | None:
    """Average Tesseract confidence over recognised words.

    Rows that are not words (pages, blocks, lines) carry a confidence of -1 and are ignored, as
    are empty words.
    """
    rows = csv.DictReader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE)
    scores = [
        float(row["conf"])
        for row in rows
        if row.get("conf") not in (None, "") and float(row["conf"]) >= 0 and row["text"].strip()
    ]
    return round(fmean(scores), 1) if scores else None


def _explain(error: pytesseract.TesseractError, language_spec: str) -> str:
    if "Failed loading language" in str(error.message):
        return f"The OCR language pack '{language_spec}' is not installed on the server."
    return "Text recognition failed on this file."
