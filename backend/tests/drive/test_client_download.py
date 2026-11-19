import pytest

from drive_text_extractor.domain.errors import FileNotAccessibleError, FileTooLargeError
from drive_text_extractor.domain.models import SourceFile
from drive_text_extractor.drive.client import GoogleDriveSource
from tests.drive.fake_drive import API_KEY, FakeDrive, drive_error

pytestmark = pytest.mark.anyio

ROOT = "RootFolderId0001"
LIMIT = 100


async def no_sleep(_: float) -> None:
    return None


@pytest.fixture
def drive() -> FakeDrive:
    fake = FakeDrive()
    fake.add_folder(ROOT, "Invoices")
    return fake


def make_source(drive: FakeDrive) -> GoogleDriveSource:
    return GoogleDriveSource(drive.client(), API_KEY, max_file_bytes=LIMIT, sleep=no_sleep)


def file_ref(id: str = "FileId000001", size: int | None = None) -> SourceFile:
    return SourceFile(id=id, name="a.pdf", mime_type="application/pdf", size_bytes=size)


async def test_downloads_file_content(drive: FakeDrive) -> None:
    drive.add_file("FileId000001", "a.pdf", "application/pdf", ROOT, b"%PDF-1.7 body")

    assert await make_source(drive).download(file_ref()) == b"%PDF-1.7 body"
    assert drive.requests[0].url.params["alt"] == "media"


async def test_refuses_files_declared_over_the_limit_without_downloading(drive: FakeDrive) -> None:
    with pytest.raises(FileTooLargeError, match="limit"):
        await make_source(drive).download(file_ref(size=LIMIT + 1))

    assert drive.requests == []


async def test_enforces_the_limit_while_streaming_when_size_is_unknown(drive: FakeDrive) -> None:
    drive.add_file(
        "FileId000001", "a.pdf", "application/pdf", ROOT, b"x" * (LIMIT + 1), report_size=False
    )

    with pytest.raises(FileTooLargeError):
        await make_source(drive).download(file_ref(size=None))


async def test_missing_file_is_not_accessible(drive: FakeDrive) -> None:
    with pytest.raises(FileNotAccessibleError):
        await make_source(drive).download(file_ref("MissingFile01"))


async def test_explains_when_the_owner_disabled_downloads(drive: FakeDrive) -> None:
    drive.then_respond(drive_error(403, "cannotDownloadFile"))

    with pytest.raises(FileNotAccessibleError, match="disabled downloads"):
        await make_source(drive).download(file_ref())


async def test_never_requests_a_malformed_id(drive: FakeDrive) -> None:
    with pytest.raises(FileNotAccessibleError):
        await make_source(drive).download(file_ref("../../evil"))

    assert drive.requests == []
