"""Contract every ``Extractor`` must honour, run against each implementation.

The batch runner treats extractors as interchangeable. These tests are what makes that safe:
same result shape, content-based detection that does not overlap, and only ``ExtractionError``
on bad input.
"""

from collections.abc import Callable
from dataclasses import dataclass

import pytest

from drive_text_extractor.domain.errors import ExtractionError
from drive_text_extractor.domain.models import ExtractionOptions, ExtractionResult
from drive_text_extractor.domain.ports import Extractor
from drive_text_extractor.extractors.image import ImageExtractor
from drive_text_extractor.extractors.pdf import PdfExtractor
from tests.fakes import FakeOcrEngine
from tests.images import png_bytes
from tests.pdf_factory import make_pdf

OPTIONS = ExtractionOptions(languages=("eng",))


@dataclass(frozen=True)
class Case:
    build: Callable[[], Extractor]
    sample: bytes
    damaged: bytes


CASES = {
    "pdf": Case(PdfExtractor, make_pdf(["Hello", "World"]), b"%PDF-1.7 truncated"),
    "image": Case(lambda: ImageExtractor(FakeOcrEngine()), png_bytes(), png_bytes()[:30]),
}


@pytest.fixture(params=CASES.values(), ids=CASES.keys())
def case(request: pytest.FixtureRequest) -> Case:
    value: Case = request.param
    return value


def test_declares_at_least_one_media_type(case: Case) -> None:
    media_types = case.build().media_types

    assert media_types
    assert all("/" in media_type for media_type in media_types)


def test_accepts_its_own_sample(case: Case) -> None:
    assert case.build().accepts(case.sample[:2048])


def test_does_not_claim_other_formats(case: Case) -> None:
    others = [other.sample for other in CASES.values() if other is not case]

    assert not any(case.build().accepts(sample[:2048]) for sample in others)


def test_returns_pages_numbered_from_one(case: Case) -> None:
    result = case.build().extract(case.sample, OPTIONS)

    assert isinstance(result, ExtractionResult)
    assert [page.number for page in result.pages] == list(range(1, len(result.pages) + 1))
    assert all(isinstance(page.text, str) for page in result.pages)


def test_bad_input_raises_only_extraction_errors(case: Case) -> None:
    with pytest.raises(ExtractionError):
        case.build().extract(case.damaged, OPTIONS)
