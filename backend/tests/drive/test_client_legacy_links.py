"""Items shared by link before 2021 need their resource key on every request."""

import pytest

from drive_text_extractor.domain.errors import FileNotAccessibleError, FolderNotFoundError
from drive_text_extractor.drive.client import GoogleDriveSource
from tests.drive.fake_drive import API_KEY, FakeDrive

pytestmark = pytest.mark.anyio

ROOT, ROOT_KEY = "0BwLegacyFolder01", "0-rootKey"
LINK = f"https://drive.google.com/drive/folders/{ROOT}?resourcekey={ROOT_KEY}&usp=drive_link"


async def no_sleep(_: float) -> None:
    return None


@pytest.fixture
def drive() -> FakeDrive:
    fake = FakeDrive()
    fake.add_folder(ROOT, "Archive", resource_key=ROOT_KEY)
    fake.add_file("0BwLegacyFile001", "scan.png", "image/png", ROOT, b"png!", resource_key="0-a")
    fake.add_folder("0BwLegacySub0001", "2019", parent=ROOT, resource_key="0-sub")
    fake.add_file(
        "0BwLegacyFile002",
        "old.pdf",
        "application/pdf",
        "0BwLegacySub0001",
        b"pdf!",
        resource_key="0-b",
    )
    return fake


def source(drive: FakeDrive) -> GoogleDriveSource:
    return GoogleDriveSource(drive.client(), API_KEY, max_file_bytes=1000, sleep=no_sleep)


async def test_the_link_key_opens_the_folder(drive: FakeDrive) -> None:
    listing = await source(drive).list_files(LINK)

    assert [f.name for f in listing.files] == ["scan.png"]
    assert drive.requests[0].headers["X-Goog-Drive-Resource-Keys"] == f"{ROOT}/{ROOT_KEY}"


async def test_without_the_key_the_folder_is_not_found(drive: FakeDrive) -> None:
    with pytest.raises(FolderNotFoundError):
        await source(drive).list_files(f"https://drive.google.com/drive/folders/{ROOT}")


async def test_subfolders_are_opened_with_their_own_keys(drive: FakeDrive) -> None:
    listing = await source(drive).list_files(LINK, recursive=True)

    assert [f.display_path for f in listing.files] == ["scan.png", "2019/old.pdf"]


async def test_files_are_downloaded_with_the_keys_learnt_from_the_listing(
    drive: FakeDrive,
) -> None:
    drive_source = source(drive)
    listing = await drive_source.list_files(LINK, recursive=True)

    contents = [await drive_source.download(file) for file in listing.files]

    assert contents == [b"png!", b"pdf!"]


async def test_a_file_cannot_be_read_without_its_key(drive: FakeDrive) -> None:
    listing = await source(drive).list_files(LINK)

    with pytest.raises(FileNotAccessibleError):
        await source(drive).download(listing.files[0])  # a fresh source never saw the key
