"""The RapidOCR models this project uses, and a way to fetch them ahead of time.

PP-OCRv5 "mobile" models (Apache-2.0, from PaddleOCR), about 14 MB in all:

- a DB text detector that finds text lines anywhere in an image, at any size or slant;
- a text-line orientation classifier that turns upside-down lines;
- the Latin recogniser, which reads English and French, accents included.

This module imports nothing from the rest of the package on purpose: the Docker build runs it on
its own to bake the models into the image before the application code is copied, so the layer
holding the models survives code changes.

    python rapid_models.py /opt/ocr-models
"""

import sys
from pathlib import Path
from typing import Any

LANGUAGES = frozenset({"eng", "fra"})
"""Tesseract codes of the languages the Latin recogniser reads."""


def engine_params(models_dir: Path | None = None) -> dict[str, Any]:
    """RapidOCR settings. Without ``models_dir``, models live inside the installed package."""
    # Imported here: rapidocr loads OpenCV and ONNX Runtime, which only image OCR needs.
    from rapidocr import LangRec, ModelType, OCRVersion

    params: dict[str, Any] = {
        "Global.log_level": "warning",
        "Det.ocr_version": OCRVersion.PPOCRV5,
        "Det.model_type": ModelType.MOBILE,
        "Cls.ocr_version": OCRVersion.PPOCRV5,
        "Cls.model_type": ModelType.MOBILE,
        "Rec.ocr_version": OCRVersion.PPOCRV5,
        "Rec.model_type": ModelType.MOBILE,
        "Rec.lang_type": LangRec.LATIN,
    }
    if models_dir is not None:
        params["Global.model_root_dir"] = str(models_dir)
    return params


def download(models_dir: Path | None = None) -> None:
    """Fetch every model by reading one line of text.

    RapidOCR downloads each model (and checks its SHA-256) the first time it is needed, and the
    orientation and recognition models are only needed once text has been detected.
    """
    from PIL import Image, ImageDraw, ImageFont
    from rapidocr import RapidOCR

    if models_dir is not None:
        models_dir.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (520, 100), "white")
    font = ImageFont.load_default(size=44)
    ImageDraw.Draw(image).text((20, 25), "Models ready", fill="black", font=font)
    result = RapidOCR(params=engine_params(models_dir))(image)
    if not getattr(result, "txts", None):
        raise RuntimeError("RapidOCR loaded its models but read nothing from the test image.")


if __name__ == "__main__":
    download(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
