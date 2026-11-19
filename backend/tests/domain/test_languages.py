import pytest

from drive_text_extractor.domain.errors import UnsupportedLanguageError
from drive_text_extractor.domain.languages import validate_languages


def test_keeps_order_and_drops_duplicates() -> None:
    assert validate_languages(["ara", "fra", "ara"]) == ("ara", "fra")


def test_requires_at_least_one_language() -> None:
    with pytest.raises(UnsupportedLanguageError):
        validate_languages([])


def test_rejects_unknown_codes_and_lists_the_supported_ones() -> None:
    with pytest.raises(UnsupportedLanguageError, match=r"deu. Choose from eng, fra, ara"):
        validate_languages(["eng", "deu"])
