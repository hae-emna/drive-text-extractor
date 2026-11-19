"""Small helpers to build image files in memory for tests."""

import io

from PIL import Image


def encode(image: Image.Image, image_format: str = "PNG", **params: object) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format=image_format, **params)
    return buffer.getvalue()


def png_bytes(width: int = 200, height: int = 100, mode: str = "RGB") -> bytes:
    color: int | tuple[int, ...] = 255 if mode == "L" else (255,) * len(mode)
    return encode(Image.new(mode, (width, height), color=color))
