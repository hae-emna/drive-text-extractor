import pytest

from drive_text_extractor.extractors.text import normalize_text


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # Arabic presentation forms (what many PDFs store) fold into regular letters.
        ("\ufefb\ufe8e", "\u0644\u0627\u0627"),
        ("\ufeed\ufeae\ufed8\ufe94", "\u0648\u0631\u0642\u0629"),
        # Ligatures and full-width digits.
        ("\ufb01nal \uff11\uff12\uff13", "final 123"),
        # Windows and old-Mac newlines.
        ("one\r\ntwo\rthree", "one\ntwo\nthree"),
        # Trailing spaces and blank-line runs.
        ("title   \n\n\n\nbody\t\n", "title\n\nbody"),
        # Control characters go, tabs stay.
        ("a\x00b\x0cc\td", "abc\td"),
    ],
)
def test_normalizes_text(raw: str, expected: str) -> None:
    assert normalize_text(raw) == expected


def test_keeps_zero_width_non_joiner() -> None:
    persian = "\u0645\u06cc\u200c\u062e\u0648\u0627\u0647\u0645"

    assert normalize_text(persian) == persian


def test_blank_input_becomes_empty() -> None:
    assert normalize_text(" \r\n \n ") == ""
