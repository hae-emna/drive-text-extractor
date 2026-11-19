import pytest

from drive_text_extractor.domain.models import (
    ExtractionMethod,
    ExtractionResult,
    PageText,
    SourceFile,
)

PARSED = ExtractionMethod.PDF_PARSER
OCR = ExtractionMethod.OCR


def test_display_path_falls_back_to_name_for_top_level_files() -> None:
    assert SourceFile(id="1", name="a.pdf", mime_type="application/pdf").display_path == "a.pdf"
    nested = SourceFile(id="2", name="b.pdf", mime_type="application/pdf", path="2024/b.pdf")
    assert nested.display_path == "2024/b.pdf"


def test_result_requires_at_least_one_page() -> None:
    with pytest.raises(ValueError, match="at least one page"):
        ExtractionResult(pages=())


def test_text_joins_pages_and_skips_empty_ones() -> None:
    result = ExtractionResult(
        pages=(
            PageText(1, PARSED, "first"),
            PageText(2, PARSED, ""),
            PageText(3, PARSED, "third"),
        )
    )

    assert result.text == "first\n\nthird"
    assert result.char_count == len("first\n\nthird")


@pytest.mark.parametrize(
    ("methods", "expected"),
    [
        ((PARSED, PARSED), PARSED),
        ((OCR,), OCR),
        ((PARSED, OCR), ExtractionMethod.MIXED),
    ],
)
def test_method_summarises_page_methods(
    methods: tuple[ExtractionMethod, ...], expected: ExtractionMethod
) -> None:
    pages = tuple(PageText(i + 1, method, "x") for i, method in enumerate(methods))

    assert ExtractionResult(pages=pages).method is expected


def test_mean_confidence_only_counts_ocr_pages() -> None:
    result = ExtractionResult(
        pages=(
            PageText(1, PARSED, "parsed"),
            PageText(2, OCR, "scan", confidence=80.0),
            PageText(3, OCR, "scan", confidence=91.0),
        )
    )

    assert result.mean_confidence == 85.5


def test_mean_confidence_is_none_without_ocr_pages() -> None:
    assert ExtractionResult(pages=(PageText(1, PARSED, "x"),)).mean_confidence is None
