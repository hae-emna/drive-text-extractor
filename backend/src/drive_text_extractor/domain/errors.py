"""Error taxonomy.

Every failure a user can run into has its own exception. ``code`` is stable and machine-readable
(the API and the JSON export carry it); ``message`` is written for the person using the app and
never contains internals. Anything that is *not* a ``DomainError`` is a bug.
"""

from typing import ClassVar


class DomainError(Exception):
    code: ClassVar[str] = "error"
    default_message: ClassVar[str] = "Something went wrong."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


# --- Source errors: reaching the folder and its files --------------------------------------


class SourceError(DomainError):
    """Raised by file sources while listing a folder or downloading a file."""


class InvalidLinkError(SourceError):
    code = "invalid_link"
    default_message = "This does not look like a Google Drive folder link."


class FolderNotFoundError(SourceError):
    code = "folder_not_found"
    default_message = (
        "Folder not found or not public. Check the link and share the folder as "
        "'Anyone with the link'."
    )


class FileNotAccessibleError(SourceError):
    code = "file_not_accessible"
    default_message = "This file could not be downloaded: it was removed or is not public."


class RateLimitedError(SourceError):
    code = "rate_limited"
    default_message = "Google Drive is rate-limiting requests. Wait a minute and try again."


class SourceUnavailableError(SourceError):
    code = "source_unavailable"
    default_message = "Google Drive could not be reached. Try again in a moment."


class SourceNotConfiguredError(SourceError):
    code = "source_not_configured"
    default_message = "The server is missing its Google Drive API key. See the README setup."


class FileTooLargeError(SourceError):
    code = "file_too_large"
    default_message = "This file is larger than the configured size limit."


# --- Extraction errors: turning bytes into text --------------------------------------------


class ExtractionError(DomainError):
    """The only errors an extractor may raise; the batch runner relies on this contract."""


class UnsupportedFileError(ExtractionError):
    code = "unsupported_file"
    default_message = "This file type is not supported. Only PDF, PNG and JPEG files are."


class CorruptFileError(ExtractionError):
    code = "corrupt_file"
    default_message = "This file is damaged or is not what its extension says."


class EncryptedFileError(ExtractionError):
    code = "encrypted_file"
    default_message = "This PDF is password-protected."


class TooManyPagesError(ExtractionError):
    code = "too_many_pages"
    default_message = "This PDF has more pages than the configured limit."


class ImageTooLargeError(ExtractionError):
    code = "image_too_large"
    default_message = "This image has too many pixels to process safely."


class OcrError(ExtractionError):
    code = "ocr_failed"
    default_message = "Text recognition failed on this file."


class OcrTimeoutError(OcrError):
    code = "ocr_timeout"
    default_message = "Text recognition took too long and was stopped."
