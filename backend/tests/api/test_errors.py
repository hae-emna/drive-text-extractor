import pytest

from drive_text_extractor.api.errors import status_for
from drive_text_extractor.domain import errors


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (errors.InvalidLinkError(), 400),
        (errors.InvalidSelectionError(), 400),
        (errors.UnsupportedLanguageError(), 400),
        (errors.FolderNotFoundError(), 404),
        (errors.JobNotFoundError(), 404),
        (errors.RateLimitedError(), 429),
        (errors.SourceUnavailableError(), 502),
        (errors.SourceNotConfiguredError(), 503),
        (errors.OcrTimeoutError(), 500),
    ],
    ids=lambda value: type(value).__name__ if isinstance(value, Exception) else str(value),
)
def test_domain_errors_map_to_http_statuses(error: errors.DomainError, expected: int) -> None:
    assert status_for(error) == expected
