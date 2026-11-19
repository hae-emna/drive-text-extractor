import pytest

from drive_text_extractor.domain import errors


def all_error_classes() -> list[type[errors.DomainError]]:
    found: list[type[errors.DomainError]] = []
    pending: list[type[errors.DomainError]] = [errors.DomainError]
    while pending:
        cls = pending.pop()
        found.append(cls)
        pending.extend(cls.__subclasses__())
    return found


CONCRETE = [
    cls
    for cls in all_error_classes()
    if cls
    not in (errors.DomainError, errors.SourceError, errors.ExtractionError, errors.RequestError)
]


def test_every_concrete_error_has_a_unique_code() -> None:
    codes = [cls.code for cls in CONCRETE]

    assert len(codes) == len(set(codes))
    assert "error" not in codes


@pytest.mark.parametrize("cls", CONCRETE, ids=lambda cls: cls.__name__)
def test_default_message_is_used_when_none_given(cls: type[errors.DomainError]) -> None:
    error = cls()

    assert error.message == cls.default_message
    assert str(error) == cls.default_message


def test_custom_message_overrides_default() -> None:
    error = errors.FileTooLargeError("File is 40 MB; the limit is 25 MB.")

    assert error.message == "File is 40 MB; the limit is 25 MB."
    assert error.code == "file_too_large"


def test_ocr_timeout_is_an_ocr_error() -> None:
    assert issubclass(errors.OcrTimeoutError, errors.OcrError)
    assert issubclass(errors.OcrError, errors.ExtractionError)
