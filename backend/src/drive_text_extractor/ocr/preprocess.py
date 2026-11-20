"""Prepare images for OCR, using Pillow only.

Each step fixes a common cause of bad OCR on real-world files without heavy dependencies:
phone photos stored sideways, transparent PNGs that turn black, low contrast, small screenshots.
"""

from PIL import Image, ImageOps

UPSCALE_BELOW = 1000
"""Images whose long side is shorter than this (screenshots, thumbnails) are scaled up."""

TARGET_LONG_SIDE = 1600
"""Roughly a page at 200 DPI. Larger images are already at scan resolution and left alone:
enlarging them costs time and can move text out of the size range Tesseract reads best."""

MAX_UPSCALE = 3.0

_OPAQUE_WHITE = (255, 255, 255, 255)


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
    background = Image.new("RGBA", rgba.size, _OPAQUE_WHITE)
    return Image.alpha_composite(background, rgba)


def _upscale_small(image: Image.Image) -> Image.Image:
    long_side = max(image.size)
    if long_side >= UPSCALE_BELOW:
        return image
    factor = min(TARGET_LONG_SIDE / long_side, MAX_UPSCALE)
    size = (round(image.width * factor), round(image.height * factor))
    return image.resize(size, Image.Resampling.LANCZOS)
