"""Turn a raw folder listing into what the user can actually extract."""

from dataclasses import replace

from drive_text_extractor.domain.models import FolderListing, SkippedFile, SourceFile
from drive_text_extractor.domain.ports import FileSource
from drive_text_extractor.services.router import ExtractorRouter

_GOOGLE_WORKSPACE_PREFIX = "application/vnd.google-apps."


class FolderBrowser:
    def __init__(self, source: FileSource, router: ExtractorRouter) -> None:
        self._source = source
        self._router = router

    async def browse(self, link: str, *, recursive: bool = False) -> FolderListing:
        """List the folder, keep the files an extractor supports, and explain the others."""
        listing = await self._source.list_files(link, recursive=recursive)
        supported: list[SourceFile] = []
        skipped = list(listing.skipped)
        for file in listing.files:
            if self._router.supports(file.mime_type):
                supported.append(file)
            else:
                skipped.append(
                    SkippedFile(file.display_path, file.mime_type, skip_reason(file.mime_type))
                )
        return replace(listing, files=tuple(supported), skipped=tuple(skipped))


def skip_reason(mime_type: str) -> str:
    if mime_type.startswith(_GOOGLE_WORKSPACE_PREFIX):
        return "Google Docs, Sheets and Slides files are not supported. Export them to PDF first."
    if mime_type.startswith("image/"):
        return "Only PNG and JPEG images are supported."
    return "This file type is not supported."
