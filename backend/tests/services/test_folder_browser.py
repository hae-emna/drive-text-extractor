import pytest

from drive_text_extractor.domain.models import SkippedFile, SourceFile
from drive_text_extractor.extractors.image import ImageExtractor
from drive_text_extractor.extractors.pdf import PdfExtractor
from drive_text_extractor.services.folder_browser import FolderBrowser
from drive_text_extractor.services.router import ExtractorRouter
from tests.fakes import FakeFileSource, FakeOcrEngine

pytestmark = pytest.mark.anyio


def file(name: str, mime_type: str) -> SourceFile:
    return SourceFile(id=f"id-{name}", name=name, mime_type=mime_type, size_bytes=10)


@pytest.fixture
def router() -> ExtractorRouter:
    return ExtractorRouter([PdfExtractor(), ImageExtractor(FakeOcrEngine())])


async def test_keeps_supported_files_and_explains_the_rest(router: ExtractorRouter) -> None:
    source = FakeFileSource(
        files=[
            file("report.pdf", "application/pdf"),
            file("scan.jpg", "image/jpeg"),
            file("notes", "application/vnd.google-apps.document"),
            file("anim.gif", "image/gif"),
            file("data.zip", "application/zip"),
        ]
    )

    listing = await FolderBrowser(source, router).browse("link")

    assert [f.name for f in listing.files] == ["report.pdf", "scan.jpg"]
    reasons = {s.name: s.reason for s in listing.skipped}
    assert "Export them to PDF" in reasons["notes"]
    assert "PNG and JPEG" in reasons["anim.gif"]
    assert reasons["data.zip"] == "This file type is not supported."


async def test_keeps_what_the_source_already_skipped(router: ExtractorRouter) -> None:
    subfolder = SkippedFile("2024/", "application/vnd.google-apps.folder", "Subfolder")
    source = FakeFileSource(files=[], skipped=[subfolder])

    listing = await FolderBrowser(source, router).browse("link")

    assert listing.skipped == (subfolder,)


async def test_passes_the_recursive_flag_and_keeps_folder_details(router: ExtractorRouter) -> None:
    source = FakeFileSource(files=[], truncated=True)

    listing = await FolderBrowser(source, router).browse("link", recursive=True)

    assert source.listed_recursively == [True]
    assert listing.folder_name == FakeFileSource.FOLDER_NAME
    assert listing.truncated
