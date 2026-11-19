import pytest

from drive_text_extractor.domain.errors import (
    FileNotAccessibleError,
    FolderNotFoundError,
    InvalidLinkError,
)
from drive_text_extractor.domain.models import LinkKind
from drive_text_extractor.drive.client import GoogleDriveSource
from tests.drive.fake_drive import API_KEY, FOLDER, FakeDrive

pytestmark = pytest.mark.anyio

FOLDER_ID = "RootFolderId0001"
FILE_ID = "InvoiceFileId01"
PDF = "application/pdf"


async def no_sleep(_: float) -> None:
    return None


@pytest.fixture
def drive() -> FakeDrive:
    fake = FakeDrive()
    fake.add_folder(FOLDER_ID, "Invoices")
    fake.add_file(FILE_ID, "invoice.pdf", PDF, FOLDER_ID, b"%PDF-1.7 twelve")
    return fake


def source(drive: FakeDrive) -> GoogleDriveSource:
    return GoogleDriveSource(drive.client(), API_KEY, max_file_bytes=1000, sleep=no_sleep)


async def test_a_file_link_lists_just_that_file(drive: FakeDrive) -> None:
    link = f"https://drive.google.com/file/d/{FILE_ID}/view?usp=sharing"

    listing = await source(drive).list_files(link)

    assert listing.kind is LinkKind.FILE
    assert (listing.folder_id, listing.folder_name) == (FILE_ID, "invoice.pdf")
    assert [(f.id, f.mime_type, f.size_bytes) for f in listing.files] == [(FILE_ID, PDF, 15)]
    assert listing.skipped == ()
    assert len(drive.requests) == 1, "a single file needs no folder listing"


async def test_ambiguous_links_are_resolved_by_drive(drive: FakeDrive) -> None:
    as_file = await source(drive).list_files(f"https://drive.google.com/open?id={FILE_ID}")
    as_folder = await source(drive).list_files(f"https://drive.google.com/open?id={FOLDER_ID}")

    assert as_file.kind is LinkKind.FILE
    assert as_folder.kind is LinkKind.FOLDER
    assert [f.id for f in as_folder.files] == [FILE_ID]


async def test_unsupported_files_are_still_listed_for_the_caller_to_judge(
    drive: FakeDrive,
) -> None:
    drive.add_file("NotesDocId0001", "notes", "application/vnd.google-apps.document", FOLDER_ID)

    listing = await source(drive).list_files("https://drive.google.com/file/d/NotesDocId0001/view")

    assert [f.mime_type for f in listing.files] == ["application/vnd.google-apps.document"]


async def test_a_file_shortcut_resolves_to_its_target(drive: FakeDrive) -> None:
    drive.add_shortcut("ShortcutId001", "invoice (shortcut).pdf", FOLDER_ID, FILE_ID, PDF)

    listing = await source(drive).list_files("https://drive.google.com/file/d/ShortcutId001/view")

    assert [f.id for f in listing.files] == [FILE_ID]


async def test_a_shortcut_to_a_folder_is_explained(drive: FakeDrive) -> None:
    drive.add_shortcut("ShortcutId002", "Invoices", FOLDER_ID, FOLDER_ID, FOLDER)

    with pytest.raises(InvalidLinkError, match="shortcut to a folder"):
        await source(drive).list_files("https://drive.google.com/file/d/ShortcutId002/view")


async def test_a_missing_or_private_file(drive: FakeDrive) -> None:
    with pytest.raises(FileNotAccessibleError, match="share the file"):
        await source(drive).list_files("https://drive.google.com/file/d/MissingFileId1/view")


async def test_a_trashed_file_counts_as_missing(drive: FakeDrive) -> None:
    drive.add_file("TrashedFileId1", "old.pdf", PDF, FOLDER_ID)
    drive.items["TrashedFileId1"].trashed = True

    with pytest.raises(FileNotAccessibleError):
        await source(drive).list_files("https://drive.google.com/file/d/TrashedFileId1/view")


async def test_a_missing_folder_keeps_the_folder_message(drive: FakeDrive) -> None:
    with pytest.raises(FolderNotFoundError):
        await source(drive).list_files("https://drive.google.com/drive/folders/MissingFolder1")
