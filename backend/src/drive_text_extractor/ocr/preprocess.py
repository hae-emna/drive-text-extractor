"""Prepare images for OCR, using Pillow only.

Each step fixes a common cause of bad OCR on real-world files without heavy dependencies:
phone photos stored sideways, transparent PNGs that turn black, low contrast, small screenshots.
"""

from PIL import Image, ImageOps

TARGET_LONG_SIDE = 2000
"""Tesseract is most accurate around 300 DPI; small images are scaled up towards this size."""

MAX_UPSCALE = 3.0


def prepare_for_ocr(image: Image.Image) -> Image.Image:
    prepared = ImageOps.exif_transpose(image)
    prepared = _flatten_transparency(prepared)
    prepared = prepared.convert("L")
    prepared = ImageOps.autocontrast(prepared, cutoff=1)
    return _upscale_small(prepared)


def _flatten_transparency(image: Image.Image) -> Image.Image:
    """Put transparent images on white; converting them directly would make the background black."""
    has_alpha = image.mode in {"RGBA", "LA", "PA"}
    if not has_alpha and not (image.mode == "P" and "transparency" in image.info):
        return image
    rgba = image.convert("RGBA")
    background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    return Image.alpha_composite(background, rgba)


def _upscale_small(image: Image.Image) -> Image.Image:
    long_side = max(image.size)
    if long_side >= TARGET_LONG_SIDE:
        return image
    factor = min(TARGET_LONG_SIDE / long_side, MAX_UPSCALE)
    size = (round(image.width * factor), round(image.height * factor))
    return image.resize(size, Image.Resampling.LANCZOS)
