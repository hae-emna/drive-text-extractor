"""``FileSource`` over a directory on the server, for trying the app without a Drive API key."""

import asyncio
import mimetypes
from datetime import UTC, datetime
from pathlib import Path

from drive_text_extractor.domain.errors import (
    FileNotAccessibleError,
    FileTooLargeError,
    FolderNotFoundError,
    InvalidLinkError,
)
from drive_text_extractor.domain.models import FolderListing, SkippedFile, SourceFile

LINK_PREFIX = "local:"
FOLDER_MIME = "inode/directory"


class LocalFolderSource:
    """Lists and reads files under ``root``.

    Links look like ``local:`` (the root itself) or ``local:invoices/2024``. File ids are paths
    relative to the root. Anything that would resolve outside the root is refused.
    """

    def __init__(self, root: Path, *, max_file_bytes: int, max_items: int = 1000) -> None:
        self._root = root.resolve()
        self._max_file_bytes = max_file_bytes
        self._max_items = max_items

    async def list_files(self, link: str, *, recursive: bool = False) -> FolderListing:
        folder = self._folder_from(link)
        return await asyncio.to_thread(self._list, folder, recursive)

    async def download(self, file: SourceFile) -> bytes:
        path = self._inside_root(file.id)
        if path is None or not path.is_file():
            raise FileNotAccessibleError()
        size = path.stat().st_size
        if size > self._max_file_bytes:
            limit_mb = self._max_file_bytes / 1_000_000
            raise FileTooLargeError(
                f"This file is {size / 1_000_000:.1f} MB; the limit is {limit_mb:g} MB."
            )
        return await asyncio.to_thread(path.read_bytes)

    def _list(self, folder: Path, recursive: bool) -> FolderListing:
        files: list[SourceFile] = []
        skipped: list[SkippedFile] = []
        pending = [folder]
        while pending:
            current = pending.pop(0)
            for entry in sorted(current.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
                relative = entry.relative_to(folder).as_posix()
                if entry.is_dir():
                    if recursive:
                        pending.append(entry)
                    else:
                        skipped.append(
                            SkippedFile(
                                relative + "/",
                                FOLDER_MIME,
                                "Subfolder: turn on 'Include subfolders' to list its files.",
                            )
                        )
                    continue
                if len(files) >= self._max_items:
                    return self._listing(folder, files, skipped, truncated=True)
                files.append(self._source_file(entry, relative))
        return self._listing(folder, files, skipped, truncated=False)

    def _source_file(self, path: Path, relative: str) -> SourceFile:
        stat = path.stat()
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return SourceFile(
            id=path.relative_to(self._root).as_posix(),
            name=path.name,
            mime_type=mime_type,
            size_bytes=stat.st_size,
            modified_time=datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
            path=relative if "/" in relative else "",
        )

    def _listing(
        self, folder: Path, files: list[SourceFile], skipped: list[SkippedFile], *, truncated: bool
    ) -> FolderListing:
        relative = folder.relative_to(self._root).as_posix()
        return FolderListing(
            folder_id=relative,
            folder_name=folder.name if relative != "." else self._root.name,
            files=tuple(files),
            skipped=tuple(skipped),
            truncated=truncated,
        )

    def _folder_from(self, link: str) -> Path:
        text = link.strip()
        if not text.startswith(LINK_PREFIX):
            raise InvalidLinkError(
                "The server runs in demo mode and reads local folders: "
                "type 'local:' for the sample folder."
            )
        folder = self._inside_root(text.removeprefix(LINK_PREFIX).strip("/"))
        if folder is None or not folder.is_dir():
            raise FolderNotFoundError("This folder does not exist on the server.")
        return folder

    def _inside_root(self, relative: str) -> Path | None:
        candidate = (self._root / relative).resolve()
        return candidate if candidate.is_relative_to(self._root) else None
