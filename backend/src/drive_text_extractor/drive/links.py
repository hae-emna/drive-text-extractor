"""Turn whatever the user pasted into a validated Drive folder id.

The link is only ever *parsed*. The server never requests the URL it was given: it builds Drive
API URLs itself from an id that matched a strict pattern, which rules out request forgery.
"""

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from drive_text_extractor.domain.errors import InvalidLinkError

_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{10,}")
_FOLDER_IN_PATH = re.compile(r"/folders/([^/?#]+)")
_ID_QUERY_PATHS = {"/open", "/folderview", "/embeddedfolderview", "/drive/folderview"}
_DOCUMENT_HOSTS = {"docs.google.com"}
_DRIVE_HOSTS = {"drive.google.com"}


@dataclass(frozen=True, slots=True)
class FolderLink:
    folder_id: str
    resource_key: str | None = None
    """Needed for some folders shared by link before 2021 (Drive security update)."""


def parse_folder_link(link: str) -> FolderLink:
    text = link.strip()
    if not text:
        raise InvalidLinkError("Paste the link of a public Google Drive folder.")
    if _ID_PATTERN.fullmatch(text):
        return FolderLink(folder_id=text)

    parsed = urlparse(text if "://" in text else f"https://{text}")
    host = (parsed.hostname or "").lower()
    if host in _DOCUMENT_HOSTS:
        raise InvalidLinkError("This is a link to a Google document. Paste a folder link instead.")
    if parsed.scheme not in {"http", "https"} or host not in _DRIVE_HOSTS:
        raise InvalidLinkError()
    if "/file/d/" in parsed.path:
        raise InvalidLinkError(
            "This link points to a single file. Paste the link of the folder that contains it."
        )

    query = parse_qs(parsed.query)
    folder_id = _folder_id_from(parsed.path, query)
    if folder_id is None or not _ID_PATTERN.fullmatch(folder_id):
        raise InvalidLinkError()
    return FolderLink(folder_id=folder_id, resource_key=_first(query.get("resourcekey")))


def is_valid_id(value: str) -> bool:
    """Whether ``value`` looks like a Drive id and is therefore safe to put in an API URL."""
    return _ID_PATTERN.fullmatch(value) is not None


def _folder_id_from(path: str, query: dict[str, list[str]]) -> str | None:
    if match := _FOLDER_IN_PATH.search(path):
        return match.group(1)
    if path.rstrip("/") in _ID_QUERY_PATHS:
        return _first(query.get("id"))
    return None


def _first(values: list[str] | None) -> str | None:
    return values[0] if values else None
