"""Ports: the small interfaces the services depend on.

Concrete implementations (Google Drive, pypdfium2, Tesseract...) live in other packages and are
plugged in at a single composition root. Services and tests only ever see these protocols.
"""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol

from drive_text_extractor.domain.models import (
    ExtractionOptions,
    ExtractionResult,
    FolderListing,
    OcrOutput,
    SourceFile,
)

if TYPE_CHECKING:
    # Pillow images are the lingua franca of Python imaging; depending on the type (not the
    # library) keeps OCR engines interchangeable without inventing an image abstraction.
    from PIL.Image import Image

DEFAULT_MAX_LISTED_FILES = 1000
"""File sources stop listing after this many files and flag the listing as truncated."""


class FileSource(Protocol):
    """Somewhere files can be listed and downloaded from.

    Implementations raise only ``SourceError`` subclasses.
    """

    async def list_files(self, link: str, *, recursive: bool = False) -> FolderListing:
        """List the files a link points to: every file of a folder, or the single file itself.

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


class OcrEngine(Protocol):
    """Recognises text in an image. Shared by the image extractor and the scanned-PDF fallback.

    Implementations raise only ``OcrError`` subclasses.
    """

    def recognize(self, image: "Image", languages: Sequence[str]) -> OcrOutput: ...
