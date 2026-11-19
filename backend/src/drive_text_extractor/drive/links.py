"""Turn whatever the user pasted into a validated Drive id.

The link is only ever *parsed*. The server never requests the URL it was given: it builds Drive
API URLs itself from an id that matched a strict pattern, which rules out request forgery.
"""

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from drive_text_extractor.domain.errors import InvalidLinkError
from drive_text_extractor.domain.models import LinkKind

_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{10,}")
_FOLDER_IN_PATH = re.compile(r"/folders/([^/?#]+)")
_FILE_IN_PATH = re.compile(r"/file/(?:u/\d+/)?d/([^/?#]+)")
_FOLDER_QUERY_PATHS = {"/folderview", "/embeddedfolderview", "/drive/folderview"}
_FILE_QUERY_PATHS = {"/uc", "/download"}
_DOCUMENT_HOSTS = {"docs.google.com"}
_DRIVE_HOSTS = {"drive.google.com", "drive.usercontent.google.com"}


@dataclass(frozen=True, slots=True)
class DriveLink:
    id: str
    resource_key: str | None = None
    """Needed for some items shared by link before 2021 (Drive security update)."""
    kind: LinkKind | None = None
    """What the URL says it points to; ``None`` when only Drive can tell (open?id=, bare ids)."""


def parse_drive_link(link: str) -> DriveLink:
    text = link.strip()
    if not text:
        raise InvalidLinkError("Paste the link of a public Google Drive folder or file.")
    if _ID_PATTERN.fullmatch(text):
        return DriveLink(id=text)

    parsed = urlparse(text if "://" in text else f"https://{text}")
    host = (parsed.hostname or "").lower()
    if host in _DOCUMENT_HOSTS:
        raise InvalidLinkError(
            "Google Docs, Sheets and Slides cannot be extracted directly. "
            "Download the document as PDF, share that file and paste its link."
        )
    if parsed.scheme not in {"http", "https"} or host not in _DRIVE_HOSTS:
        raise InvalidLinkError()

    query = parse_qs(parsed.query)
    drive_id, kind = _id_from(parsed.path.rstrip("/"), query)
    if drive_id is None or not _ID_PATTERN.fullmatch(drive_id):
        raise InvalidLinkError()
    return DriveLink(id=drive_id, resource_key=_first(query.get("resourcekey")), kind=kind)


def is_valid_id(value: str) -> bool:
    """Whether ``value`` looks like a Drive id and is therefore safe to put in an API URL."""
    return _ID_PATTERN.fullmatch(value) is not None


def _id_from(path: str, query: dict[str, list[str]]) -> tuple[str | None, LinkKind | None]:
    if match := _FOLDER_IN_PATH.search(path):
        return match.group(1), LinkKind.FOLDER
    if match := _FILE_IN_PATH.search(path):
        return match.group(1), LinkKind.FILE
    if path in _FOLDER_QUERY_PATHS:
        return _first(query.get("id")), LinkKind.FOLDER
    if path in _FILE_QUERY_PATHS or path.endswith("/uc"):
        return _first(query.get("id")), LinkKind.FILE
    if path == "/open":
        return _first(query.get("id")), None
    return None, None


def _first(values: list[str] | None) -> str | None:
    return values[0] if values else None
