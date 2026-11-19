"""Choose the extractor for a file."""

from collections.abc import Sequence

from drive_text_extractor.domain.errors import CorruptFileError, UnsupportedFileError
from drive_text_extractor.domain.ports import Extractor

HEAD_SIZE = 2048
"""How many leading bytes extractors get to recognise their format."""


class ExtractorRouter:
    """Routes a file to the first extractor that recognises its content.

    The router knows no file format itself: supporting a new one means writing an extractor and
    adding it to the list given at the composition root. The declared MIME type is only used to
    decide what to *offer* in a listing; routing trusts the bytes, which cannot lie.
    """

    def __init__(self, extractors: Sequence[Extractor]) -> None:
        if not extractors:
            raise ValueError("the router needs at least one extractor")
        self._extractors = tuple(extractors)

    @property
    def supported_media_types(self) -> frozenset[str]:
        return frozenset().union(*(extractor.media_types for extractor in self._extractors))

    def supports(self, media_type: str) -> bool:
        return media_type in self.supported_media_types

    def select(self, data: bytes) -> Extractor:
        if not data:
            raise CorruptFileError("This file is empty.")
        head = data[:HEAD_SIZE]
        for extractor in self._extractors:
            if extractor.accepts(head):
                return extractor
        raise UnsupportedFileError(
            "The content of this file is not in a supported format, whatever its extension says."
        )
