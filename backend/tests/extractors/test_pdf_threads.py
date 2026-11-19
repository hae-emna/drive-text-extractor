"""Regression test: PDFium crashed the process when two threads extracted PDFs at once."""

from concurrent.futures import ThreadPoolExecutor

from drive_text_extractor.domain.models import ExtractionMethod, ExtractionOptions
from drive_text_extractor.extractors.pdf import PdfExtractor
from tests.fakes import FakeOcrEngine
from tests.pdf_factory import make_pdf


def test_concurrent_extractions_are_safe() -> None:
    extractor = PdfExtractor(ocr=FakeOcrEngine())
    documents = [make_pdf([f"Document {n} has a proper text layer", None]) for n in range(40)]

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(
            pool.map(lambda data: extractor.extract(data, ExtractionOptions()), documents)
        )

    assert [r.pages[0].text for r in results] == [
        f"Document {n} has a proper text layer" for n in range(40)
    ]
    assert all(r.method is ExtractionMethod.MIXED for r in results)
