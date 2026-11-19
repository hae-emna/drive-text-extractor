"""Ports: the small interfaces the services depend on.

Concrete implementations (Google Drive, pypdfium2, Tesseract...) live in other packages and are
plugged in at a single composition root. Services and tests only ever see these protocols.
"""

from typing import Protocol

from drive_text_extractor.domain.models import (
    ExtractionOptions,
    ExtractionResult,
    FolderListing,
    SourceFile,
)


class FileSource(Protocol):
    """Somewhere files can be listed and downloaded from.

    Implementations raise only ``SourceError`` subclasses.
    """

    async def list_folder(self, link: str, *, recursive: bool = False) -> FolderListing:
        """List every file in the folder the link points to.

        The listing is unfiltered: deciding what can be extracted is the caller's job.
        """
        ...

    async def download(self, file: SourceFile) -> bytes: ...


class Extractor(Protocol):
    """Turns the bytes of one kind of document into text.

    Implementations are synchronous and CPU-bound; callers run them off the event loop.
    They raise only ``ExtractionError`` subclasses.
    """

    @property
    def media_types(self) -> frozenset[str]:
        """MIME types this extractor is offered, as declared by the source (used for listing)."""
        ...

    def accepts(self, head: bytes) -> bool:
        """Whether the content, judged from its first bytes, is something this extractor reads.

        Routing is done on content, not on the declared MIME type, which can be wrong.
        """
        ...

    def extract(self, data: bytes, options: ExtractionOptions) -> ExtractionResult: ...
