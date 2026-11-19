"""Google Drive implementation of the ``FileSource`` port (Drive API v3, API key, no OAuth)."""

import asyncio
from collections import deque
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import httpx

from drive_text_extractor.domain.errors import (
    FileNotAccessibleError,
    FileTooLargeError,
    FolderNotFoundError,
    InvalidLinkError,
    RateLimitedError,
    SourceError,
    SourceNotConfiguredError,
    SourceUnavailableError,
)
from drive_text_extractor.domain.models import FolderListing, SkippedFile, SourceFile
from drive_text_extractor.drive.links import DriveLink, is_valid_id, parse_drive_link

API_ROOT = "https://www.googleapis.com/drive/v3"
FOLDER_MIME = "application/vnd.google-apps.folder"
SHORTCUT_MIME = "application/vnd.google-apps.shortcut"

_ITEM_FIELDS = "id,name,mimeType,size,modifiedTime,shortcutDetails(targetId,targetMimeType)"
_RATE_LIMIT_REASONS = {"rateLimitExceeded", "userRateLimitExceeded", "RATE_LIMIT_EXCEEDED"}
_CONFIG_MESSAGES = {
    "API_KEY_INVALID": "The Google Drive API key is invalid. Check GOOGLE_API_KEY.",
    "keyInvalid": "The Google Drive API key is invalid. Check GOOGLE_API_KEY.",
    "SERVICE_DISABLED": "The Google Drive API is not enabled for this API key's project.",
    "accessNotConfigured": "The Google Drive API is not enabled for this API key's project.",
    "API_KEY_SERVICE_BLOCKED": "This API key is not allowed to call the Google Drive API.",
}

Json = dict[str, Any]
Sleep = Callable[[float], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Exponential backoff for rate limits and transient failures."""

    attempts: int = 4
    base_delay: float = 0.5
    max_delay: float = 8.0

    def delay(self, attempt: int, retry_after: float | None = None) -> float:
        backoff = self.base_delay * 2.0 ** (attempt - 1)
        return min(max(backoff, retry_after or 0.0), self.max_delay)


class GoogleDriveSource:
    def __init__(
        self,
        http: httpx.AsyncClient,
        api_key: str | None,
        *,
        max_file_bytes: int,
        max_items: int = 1000,
        page_size: int = 1000,
        retry: RetryPolicy | None = None,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        self._http = http
        self._api_key = api_key
        self._max_file_bytes = max_file_bytes
        self._max_items = max_items
        self._page_size = page_size
        self._retry = retry or RetryPolicy()
        self._sleep = sleep

    async def list_folder(self, link: str, *, recursive: bool = False) -> FolderListing:
        ref = parse_drive_link(link)
        headers = _resource_key_header(ref)
        folder = await self._get_json(
            f"{API_ROOT}/files/{ref.id}",
            {"fields": "id,name,mimeType", "supportsAllDrives": "true"},
            headers,
            not_found=FolderNotFoundError,
        )
        if folder.get("mimeType") != FOLDER_MIME:
            raise InvalidLinkError("This link points to a file, not a folder. Paste a folder link.")

        files: list[SourceFile] = []
        skipped: list[SkippedFile] = []
        pending = deque([(ref.id, "")])
        visited = {ref.id}
        while pending:
            folder_id, prefix = pending.popleft()
            async for item in self._children(folder_id, headers):
                path = prefix + item["name"]
                mime_type = item["mimeType"]
                if mime_type == FOLDER_MIME:
                    if not recursive:
                        skipped.append(
                            SkippedFile(
                                path + "/",
                                mime_type,
                                "Subfolder: turn on 'Include subfolders' to list its files.",
                            )
                        )
                    elif item["id"] not in visited:
                        visited.add(item["id"])
                        pending.append((item["id"], path + "/"))
                    continue
                if mime_type == SHORTCUT_MIME:
                    target = _resolve_shortcut(item)
                    if target is None:
                        skipped.append(
                            SkippedFile(path, mime_type, "Shortcut to a folder is not followed.")
                        )
                        continue
                    item = target
                if len(files) >= self._max_items:
                    return _listing(ref, folder, files, skipped, truncated=True)
                files.append(_to_source_file(item, path if prefix else ""))
        return _listing(ref, folder, files, skipped, truncated=False)

    async def download(self, file: SourceFile) -> bytes:
        limit = self._max_file_bytes
        if file.size_bytes is not None and file.size_bytes > limit:
            raise FileTooLargeError(_too_large(file.size_bytes, limit))
        if not is_valid_id(file.id):
            raise FileNotAccessibleError()

        response = await self._send(
            f"{API_ROOT}/files/{file.id}",
            {"alt": "media", "supportsAllDrives": "true"},
            {},
            not_found=FileNotAccessibleError,
            stream=True,
        )
        received = bytearray()
        try:
            async for chunk in response.aiter_bytes():
                received += chunk
                if len(received) > limit:
                    raise FileTooLargeError(_too_large(None, limit))
        except httpx.TransportError as exc:
            raise SourceUnavailableError("The download was interrupted. Try again.") from exc
        finally:
            await response.aclose()
        return bytes(received)

    async def _children(self, folder_id: str, headers: dict[str, str]) -> AsyncIterator[Json]:
        # folder_id matched a strict [A-Za-z0-9_-] pattern, so it is safe inside the query.
        params = {
            "q": f"'{folder_id}' in parents and trashed = false",
            "fields": f"nextPageToken,files({_ITEM_FIELDS})",
            "pageSize": str(self._page_size),
            "orderBy": "folder,name_natural",
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
        }
        while True:
            page = await self._get_json(
                f"{API_ROOT}/files", params, headers, not_found=FolderNotFoundError
            )
            for item in page.get("files", []):
                yield item
            token = page.get("nextPageToken")
            if not token:
                return
            params = {**params, "pageToken": token}

    async def _get_json(
        self,
        url: str,
        params: dict[str, str],
        headers: dict[str, str],
        *,
        not_found: type[SourceError],
    ) -> Json:
        response = await self._send(url, params, headers, not_found=not_found, stream=False)
        body: Json = response.json()
        return body

    async def _send(
        self,
        url: str,
        params: dict[str, str],
        headers: dict[str, str],
        *,
        not_found: type[SourceError],
        stream: bool,
    ) -> httpx.Response:
        if not self._api_key:
            raise SourceNotConfiguredError()
        # The key travels in a header, never in the URL, so it cannot leak into access logs.
        request = self._http.build_request(
            "GET", url, params=params, headers={**headers, "X-Goog-Api-Key": self._api_key}
        )
        for attempt in range(1, self._retry.attempts + 1):
            is_last = attempt == self._retry.attempts
            try:
                response = await self._http.send(request, stream=stream)
            except httpx.TransportError as exc:
                if is_last:
                    raise SourceUnavailableError() from exc
                await self._sleep(self._retry.delay(attempt))
                continue
            if response.is_success:
                return response

            await response.aread()
            await response.aclose()
            error, retryable = _classify(response, not_found)
            if not retryable or is_last:
                raise error
            await self._sleep(self._retry.delay(attempt, _retry_after(response)))
        raise AssertionError("unreachable: the last attempt always returns or raises")


def _classify(response: httpx.Response, not_found: type[SourceError]) -> tuple[SourceError, bool]:
    """Map a Drive error response onto the domain taxonomy. Returns (error, retryable)."""
    status = response.status_code
    reasons = _error_reasons(response)
    if status == 429 or reasons & _RATE_LIMIT_REASONS:
        return RateLimitedError(), True
    for reason in reasons:
        if reason in _CONFIG_MESSAGES:
            return SourceNotConfiguredError(_CONFIG_MESSAGES[reason]), False
    if "cannotDownloadFile" in reasons:
        return FileNotAccessibleError("The owner has disabled downloads for this file."), False
    if status in {401, 403, 404}:
        return not_found(), False
    if status >= 500:
        return SourceUnavailableError(), True
    return SourceUnavailableError(f"Google Drive rejected the request (HTTP {status})."), False


def _error_reasons(response: httpx.Response) -> set[str]:
    try:
        error = response.json().get("error", {})
    except ValueError:
        return set()
    if not isinstance(error, dict):
        return set()
    entries = [*error.get("errors", []), *error.get("details", [])]
    return {entry["reason"] for entry in entries if isinstance(entry, dict) and "reason" in entry}


def _retry_after(response: httpx.Response) -> float | None:
    value = response.headers.get("Retry-After", "")
    return float(value) if value.isdigit() else None


def _resource_key_header(ref: DriveLink) -> dict[str, str]:
    if ref.resource_key is None:
        return {}
    return {"X-Goog-Drive-Resource-Keys": f"{ref.id}/{ref.resource_key}"}


def _resolve_shortcut(item: Json) -> Json | None:
    details = item.get("shortcutDetails") or {}
    target_id = details.get("targetId")
    target_mime = details.get("targetMimeType")
    if not target_id or not target_mime or target_mime == FOLDER_MIME:
        return None
    # The shortcut's own size/modifiedTime describe the shortcut, not the target.
    return {"id": target_id, "name": item["name"], "mimeType": target_mime}


def _to_source_file(item: Json, path: str) -> SourceFile:
    size = item.get("size")
    return SourceFile(
        id=item["id"],
        name=item["name"],
        mime_type=item["mimeType"],
        size_bytes=int(size) if size is not None else None,
        modified_time=item.get("modifiedTime"),
        path=path,
    )


def _listing(
    ref: DriveLink,
    folder: Json,
    files: list[SourceFile],
    skipped: list[SkippedFile],
    *,
    truncated: bool,
) -> FolderListing:
    return FolderListing(
        folder_id=ref.id,
        folder_name=folder.get("name", ""),
        files=tuple(files),
        skipped=tuple(skipped),
        truncated=truncated,
    )


def _too_large(size: int | None, limit: int) -> str:
    limit_mb = limit / 1_000_000
    if size is None:
        return f"This file is larger than the {limit_mb:g} MB limit."
    return f"This file is {size / 1_000_000:.1f} MB; the limit is {limit_mb:g} MB."
