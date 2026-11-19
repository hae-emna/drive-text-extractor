from PIL import Image

from drive_text_extractor.ocr.routing import PreferredOcrEngine
from tests.fakes import FakeOcrEngine


def test_uses_the_preferred_engine_when_it_reads_every_language() -> None:
    preferred, fallback = FakeOcrEngine(text="preferred"), FakeOcrEngine(text="fallback")
    engine = PreferredOcrEngine(preferred, frozenset({"eng", "fra"}), fallback=fallback)
    image = Image.new("L", (10, 10), 255)

    assert engine.recognize(image, ["fra", "eng"]).text == "preferred"
    assert engine.recognize(image, ["eng", "ara"]).text == "fallback"
    assert [call.languages for call in fallback.calls] == [("eng", "ara")]
