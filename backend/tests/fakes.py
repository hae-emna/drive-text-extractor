"""Test doubles for the domain ports. They let services be tested without network or OCR."""

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ClassVar

from PIL.Image import Image

from drive_text_extractor.domain.models import FolderListing, OcrOutput, SkippedFile, SourceFile


@dataclass
class RecordedOcrCall:
    size: tuple[int, int]
    mode: str
    languages: tuple[str, ...]


@dataclass
class FakeOcrEngine:
    """Returns canned text and records what it was asked to read."""

    text: str = "recognised text"
    confidence: float | None = 91.0
    calls: list[RecordedOcrCall] = field(default_factory=list)

    def recognize(self, image: Image, languages: Sequence[str]) -> OcrOutput:
        self.calls.append(RecordedOcrCall(image.size, image.mode, tuple(languages)))
        return OcrOutput(text=self.text, confidence=self.confidence)


@dataclass
class FakeFileSource:
    """In-memory folder. ``contents`` maps a file id to its bytes, or to an error to raise."""

    FOLDER_ID: ClassVar[str] = "FakeFolderId01"
    FOLDER_NAME: ClassVar[str] = "Fake folder"

    files: list[SourceFile] = field(default_factory=list)
    skipped: list[SkippedFile] = field(default_factory=list)
    truncated: bool = False
    contents: dict[str, bytes | Exception] = field(default_factory=dict)
    download_delay: float = 0.0
    list_error: Exception | None = None

    listed_recursively: list[bool] = field(default_factory=list)
    downloads: list[str] = field(default_factory=list)
    in_flight: int = 0
    max_in_flight: int = 0

    async def list_folder(self, link: str, *, recursive: bool = False) -> FolderListing:
        self.listed_recursively.append(recursive)
        if self.list_error is not None:
            raise self.list_error
        return FolderListing(
            folder_id=self.FOLDER_ID,
            folder_name=self.FOLDER_NAME,
            files=tuple(self.files),
            skipped=tuple(self.skipped),
            truncated=self.truncated,
        )

    async def download(self, file: SourceFile) -> bytes:
        self.downloads.append(file.id)
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            await asyncio.sleep(self.download_delay)
            content = self.contents.get(file.id, b"")
            if isinstance(content, Exception):
                raise content
            return content
        finally:
            self.in_flight -= 1
