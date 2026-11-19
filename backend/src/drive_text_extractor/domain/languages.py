"""OCR languages offered to users. Each needs its Tesseract language pack installed."""

from collections.abc import Mapping, Sequence

from drive_text_extractor.domain.errors import UnsupportedLanguageError

SUPPORTED_LANGUAGES: Mapping[str, str] = {
    "eng": "English",
    "fra": "French",
    "ara": "Arabic",
}


def validate_languages(codes: Sequence[str]) -> tuple[str, ...]:
    """Return the codes without duplicates, in order (Tesseract favours the first one)."""
    chosen = tuple(dict.fromkeys(codes))
    if not chosen:
        raise UnsupportedLanguageError()
    unknown = [code for code in chosen if code not in SUPPORTED_LANGUAGES]
    if unknown:
        supported = ", ".join(SUPPORTED_LANGUAGES)
        raise UnsupportedLanguageError(
            f"Unsupported OCR language: {', '.join(unknown)}. Choose from {supported}."
        )
    return chosen
