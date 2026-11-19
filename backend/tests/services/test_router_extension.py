"""Open/closed in practice: a new format is supported without editing existing code."""

from drive_text_extractor.domain.models import (
    ExtractionMethod,
    ExtractionOptions,
    ExtractionResult,
    PageText,
)
from drive_text_extractor.extractors.image import ImageExtractor
from drive_text_extractor.extractors.pdf import PdfExtractor
from drive_text_extractor.services.router import ExtractorRouter
from tests.fakes import FakeOcrEngine

WEBP = b"RIFF\x24\x00\x00\x00WEBPVP8 "


class WebpExtractor:
    """What adding WebP support would look like: one new class, registered at startup."""

    media_types = frozenset({"image/webp"})

    def accepts(self, head: bytes) -> bool:
        return head[:4] == b"RIFF" and head[8:12] == b"WEBP"

    def extract(self, data: bytes, options: ExtractionOptions) -> ExtractionResult:
        return ExtractionResult(pages=(PageText(1, ExtractionMethod.OCR, "from webp", 88.0),))


def test_a_new_extractor_plugs_in_without_touching_the_router() -> None:
    router = ExtractorRouter([PdfExtractor(), ImageExtractor(FakeOcrEngine()), WebpExtractor()])

    assert router.supports("image/webp")
    assert router.select(WEBP).extract(WEBP, ExtractionOptions()).text == "from webp"
