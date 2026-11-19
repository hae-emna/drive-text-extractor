"""Image extractor: prepares PNG and JPEG files, then runs them through an OCR engine."""

import io

from PIL import Image, UnidentifiedImageError

from drive_text_extractor.domain.errors import CorruptFileError, ImageTooLargeError
from drive_text_extractor.domain.models import (
    ExtractionMethod,
    ExtractionOptions,
    ExtractionResult,
    PageText,
)
from drive_text_extractor.domain.ports import OcrEngine
from drive_text_extractor.ocr.preprocess import prepare_for_ocr

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8\xff"


class ImageExtractor:
    media_types = frozenset({"image/png", "image/jpeg"})

    def __init__(self, ocr: OcrEngine, *, max_pixels: int = 50_000_000) -> None:
        self._ocr = ocr
        self._max_pixels = max_pixels

    def accepts(self, head: bytes) -> bool:
        return head.startswith((PNG_SIGNATURE, JPEG_SIGNATURE))

    def extract(self, data: bytes, options: ExtractionOptions) -> ExtractionResult:
        with self._open(data) as image:
            prepared = prepare_for_ocr(image)
        output = self._ocr.recognize(prepared, options.languages)
        page = PageText(
            number=1, method=ExtractionMethod.OCR, text=output.text, confidence=output.confidence
        )
        return ExtractionResult(pages=(page,))

    def _open(self, data: bytes) -> Image.Image:
        try:
            image = Image.open(io.BytesIO(data))
        except Image.DecompressionBombError as exc:
            raise ImageTooLargeError() from exc
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise CorruptFileError() from exc

        # Image.open only reads the header: check the size before decoding any pixel.
        width, height = image.size
        if width * height > self._max_pixels:
            image.close()
            raise ImageTooLargeError(
                f"This image is {width} x {height} pixels; "
                f"the limit is {self._max_pixels / 1_000_000:g} megapixels."
            )
        try:
            image.load()
        except (OSError, ValueError) as exc:
            image.close()
            raise CorruptFileError("This image is damaged or truncated.") from exc
        return image
