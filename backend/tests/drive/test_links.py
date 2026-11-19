import pytest

from drive_text_extractor.domain.errors import InvalidLinkError
from drive_text_extractor.drive.links import FolderLink, parse_folder_link

FOLDER_ID = "1AbCdEfGhIjKlMnOpQrStUvWxYz_-012"


@pytest.mark.parametrize(
    "link",
    [
        f"https://drive.google.com/drive/folders/{FOLDER_ID}",
        f"https://drive.google.com/drive/folders/{FOLDER_ID}?usp=sharing",
        f"https://drive.google.com/drive/folders/{FOLDER_ID}/",
        f"https://drive.google.com/drive/u/0/folders/{FOLDER_ID}",
        f"https://drive.google.com/drive/u/1/mobile/folders/{FOLDER_ID}?usp=drive_link",
        f"https://drive.google.com/open?id={FOLDER_ID}",
        f"https://drive.google.com/folderview?id={FOLDER_ID}",
        f"https://drive.google.com/embeddedfolderview?id={FOLDER_ID}#list",
        f"drive.google.com/drive/folders/{FOLDER_ID}",
        f"  https://drive.google.com/drive/folders/{FOLDER_ID}  ",
        FOLDER_ID,
    ],
)
def test_accepts_common_folder_link_formats(link: str) -> None:
    assert parse_folder_link(link) == FolderLink(folder_id=FOLDER_ID)


def test_keeps_resource_key_when_present() -> None:
    link = f"https://drive.google.com/drive/folders/{FOLDER_ID}?resourcekey=0-abc123&usp=sharing"

    assert parse_folder_link(link) == FolderLink(folder_id=FOLDER_ID, resource_key="0-abc123")


@pytest.mark.parametrize(
    ("link", "hint"),
    [
        ("", "Paste the link"),
        ("   ", "Paste the link"),
        (f"https://drive.google.com/file/d/{FOLDER_ID}/view", "single file"),
        (f"https://docs.google.com/document/d/{FOLDER_ID}/edit", "Google document"),
    ],
)
def test_explains_why_a_link_is_rejected(link: str, hint: str) -> None:
    with pytest.raises(InvalidLinkError, match=hint):
        parse_folder_link(link)


@pytest.mark.parametrize(
    "link",
    [
        "not a link",
        f"https://evil.example.com/drive/folders/{FOLDER_ID}",
        f"https://drive.google.com.evil.example/drive/folders/{FOLDER_ID}",
        f"ftp://drive.google.com/drive/folders/{FOLDER_ID}",
        "https://drive.google.com/drive/my-drive",
        "https://drive.google.com/drive/folders/short",
        "https://drive.google.com/drive/folders/has'quote_in_the_id",
        "https://drive.google.com/open",
    ],
)
def test_rejects_anything_that_is_not_a_drive_folder_link(link: str) -> None:
    with pytest.raises(InvalidLinkError):
        parse_folder_link(link)
