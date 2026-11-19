import pytest

from drive_text_extractor.domain.errors import InvalidLinkError
from drive_text_extractor.domain.models import LinkKind
from drive_text_extractor.drive.links import DriveLink, parse_drive_link

DRIVE_ID = "1AbCdEfGhIjKlMnOpQrStUvWxYz_-012"


@pytest.mark.parametrize(
    "link",
    [
        f"https://drive.google.com/drive/folders/{DRIVE_ID}",
        f"https://drive.google.com/drive/folders/{DRIVE_ID}?usp=sharing",
        f"https://drive.google.com/drive/folders/{DRIVE_ID}/",
        f"https://drive.google.com/drive/u/0/folders/{DRIVE_ID}",
        f"https://drive.google.com/drive/u/1/mobile/folders/{DRIVE_ID}?usp=drive_link",
        f"https://drive.google.com/folderview?id={DRIVE_ID}",
        f"https://drive.google.com/embeddedfolderview?id={DRIVE_ID}#list",
        f"drive.google.com/drive/folders/{DRIVE_ID}",
        f"  https://drive.google.com/drive/folders/{DRIVE_ID}  ",
    ],
)
def test_accepts_folder_links(link: str) -> None:
    assert parse_drive_link(link) == DriveLink(id=DRIVE_ID, kind=LinkKind.FOLDER)


@pytest.mark.parametrize(
    "link",
    [
        f"https://drive.google.com/file/d/{DRIVE_ID}/view?usp=sharing",
        f"https://drive.google.com/file/d/{DRIVE_ID}/view?usp=drive_link",
        f"https://drive.google.com/file/d/{DRIVE_ID}/edit",
        f"https://drive.google.com/file/d/{DRIVE_ID}/preview",
        f"https://drive.google.com/file/u/0/d/{DRIVE_ID}/view",
        f"https://drive.google.com/uc?id={DRIVE_ID}&export=download",
        f"https://drive.google.com/u/0/uc?id={DRIVE_ID}&export=download",
        f"https://drive.usercontent.google.com/download?id={DRIVE_ID}&export=download",
    ],
)
def test_accepts_file_links(link: str) -> None:
    assert parse_drive_link(link) == DriveLink(id=DRIVE_ID, kind=LinkKind.FILE)


@pytest.mark.parametrize("link", [f"https://drive.google.com/open?id={DRIVE_ID}", DRIVE_ID])
def test_leaves_ambiguous_links_for_drive_to_resolve(link: str) -> None:
    assert parse_drive_link(link) == DriveLink(id=DRIVE_ID, kind=None)


def test_keeps_resource_key_when_present() -> None:
    link = f"https://drive.google.com/file/d/{DRIVE_ID}/view?resourcekey=0-abc123"

    assert parse_drive_link(link).resource_key == "0-abc123"


@pytest.mark.parametrize(
    ("link", "hint"),
    [
        ("", "Paste the link"),
        ("   ", "Paste the link"),
        (f"https://docs.google.com/document/d/{DRIVE_ID}/edit", "Download the document as PDF"),
        (f"https://docs.google.com/spreadsheets/d/{DRIVE_ID}/edit", "Download the document as PDF"),
    ],
)
def test_explains_why_a_link_is_rejected(link: str, hint: str) -> None:
    with pytest.raises(InvalidLinkError, match=hint):
        parse_drive_link(link)


@pytest.mark.parametrize(
    "link",
    [
        "not a link",
        f"https://evil.example.com/drive/folders/{DRIVE_ID}",
        f"https://drive.google.com.evil.example/file/d/{DRIVE_ID}/view",
        f"ftp://drive.google.com/drive/folders/{DRIVE_ID}",
        "https://drive.google.com/drive/my-drive",
        "https://drive.google.com/drive/folders/short",
        "https://drive.google.com/file/d/has'quote_in_the_id/view",
        "https://drive.google.com/open",
        "https://drive.google.com/uc?export=download",
    ],
)
def test_rejects_anything_that_is_not_a_drive_link(link: str) -> None:
    with pytest.raises(InvalidLinkError):
        parse_drive_link(link)
