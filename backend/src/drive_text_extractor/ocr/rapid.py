"""RapidOCR implementation of the ``OcrEngine`` port, for photos and screenshots.

Tesseract is built for pages: it first segments the image into blocks, paragraphs and lines, and
on a photo, a screenshot or a poster that segmentation finds little or nothing. RapidOCR
(Apache-2.0) runs PaddleOCR's deep-learning models on ONNX Runtime (MIT): a detector finds every
line of text wherever it is, then each line is read on its own. See ``rapid_models`` for which
models, and ``layout`` for how the lines are put back in reading order.

Only the Latin recogniser is used, so this engine reads English and French. Arabic stays with
Tesseract: RapidOCR's Arabic model needs an extra right-to-left dependency.
"""

import logging
import threading
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from PIL.Image import Image

from drive_text_extractor.domain.errors import OcrError
from drive_text_extractor.domain.models import OcrOutput
from drive_text_extractor.extractors.text import normalize_text
from drive_text_extractor.ocr.layout import TextLine, arrange, mean_confidence
from drive_text_extractor.ocr.rapid_models import LANGUAGES, engine_params

logger = logging.getLogger(__name__)

Recognizer = Callable[[Image], Any]
"""Reads an RGB image and returns RapidOCR's output (``boxes``, ``txts``, ``scores``)."""


class RapidOcrEngine:
    languages = LANGUAGES

    def __init__(
        self,
        *,
        models_dir: Path | None = None,
        orient: Callable[[Image], Image] | None = None,
        recognizer_factory: Callable[[], Recognizer] | None = None,
    ) -> None:
        """
        ``orient`` straightens sideways or upside-down images first: the detector reads rotated
        lines, but the line order of a rotated page would come out wrong.
        ``recognizer_factory`` exists for tests; by default RapidOCR is loaded on first use.
        """
        self._orient = orient
        self._factory = recognizer_factory or (lambda: _load_rapidocr(models_dir))
        self._recognizer: Recognizer | None = None
        # One recognition at a time: ONNX Runtime already spreads each run over every core, and
        # RapidOCR does not document its pipeline objects as thread-safe.
        self._lock = threading.Lock()

    def recognize(self, image: Image, languages: Sequence[str]) -> OcrOutput:
        unsupported = sorted(set(languages) - self.languages)
        if unsupported:
            raise OcrError(f"The image OCR engine cannot read: {', '.join(unsupported)}.")
        if self._orient is not None:
            image = self._orient(image)
        rgb = image.convert("RGB")
        with self._lock:
            try:
                if self._recognizer is None:
                    self._recognizer = self._factory()
                result = self._recognizer(rgb)
            except Exception as exc:
                # Model downloads, ONNX Runtime and OpenCV each raise their own exception types.
                logger.exception("RapidOCR failed")
                raise OcrError() from exc
        lines = text_lines(result)
        return OcrOutput(text=normalize_text(arrange(lines)), confidence=mean_confidence(lines))


def text_lines(result: Any) -> list[TextLine]:
    """The lines of a RapidOCR result, without those that hold no letter or digit.

    Edges, icons and bullets are sometimes read as "..", "*" or "|"; they are not text.
    """
    texts = getattr(result, "txts", None) or ()
    scores = getattr(result, "scores", None) or ()
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return []
    return [
        TextLine(
            text=text,
            score=float(score),
            corners=tuple((float(x), float(y)) for x, y in box),
        )
        for text, score, box in zip(texts, scores, boxes, strict=False)
        if any(char.isalnum() for char in text)
    ]


def _load_rapidocr(models_dir: Path | None) -> Recognizer:
    from rapidocr import RapidOCR

    if models_dir is not None:
        # Missing models are downloaded into it; it must exist first.
        models_dir.mkdir(parents=True, exist_ok=True)
    engine: Recognizer = RapidOCR(params=engine_params(models_dir))
    return engine
