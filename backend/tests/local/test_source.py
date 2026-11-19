from pathlib import Path

import pytest

from drive_text_extractor.domain.errors import (
    FileNotAccessibleError,
    FileTooLargeError,
    FolderNotFoundError,
    InvalidLinkError,
)
from drive_text_extractor.domain.models import LinkKind, SourceFile
from drive_text_extractor.local.source import LocalFolderSource

pytestmark = pytest.mark.anyio


@pytest.fixture
def root(tmp_path: Path) -> Path:
    (tmp_path / "invoice.pdf").write_bytes(b"%PDF-1.7 invoice")
    (tmp_path / "scan.png").write_bytes(b"\x89PNG scan")
    (tmp_path / "2024").mkdir()
    (tmp_path / "2024" / "old.pdf").write_bytes(b"%PDF-1.7 old")
    return tmp_path


@pytest.fixture
def source(root: Path) -> LocalFolderSource:
    return LocalFolderSource(root, max_file_bytes=100)


async def test_lists_files_with_type_and_size_and_skips_subfolders(
    source: LocalFolderSource,
) -> None:
    listing = await source.list_files("local:")

    assert [(f.id, f.mime_type, f.size_bytes) for f in listing.files] == [
        ("invoice.pdf", "application/pdf", 16),
        ("scan.png", "image/png", 9),
    ]
    assert [s.name for s in listing.skipped] == ["2024/"]


async def test_walks_subfolders_when_recursive(source: LocalFolderSource) -> None:
    listing = await source.list_files("local:", recursive=True)

    assert [f.display_path for f in listing.files] == ["invoice.pdf", "scan.png", "2024/old.pdf"]


async def test_lists_a_subfolder_by_its_path(source: LocalFolderSource) -> None:
    listing = await source.list_files("local:2024")

    assert listing.folder_name == "2024"
    assert [f.id for f in listing.files] == ["2024/old.pdf"]


async def test_lists_a_single_file_by_its_path(source: LocalFolderSource) -> None:
    listing = await source.list_files("local:2024/old.pdf")

    assert listing.kind is LinkKind.FILE
    assert (listing.folder_id, listing.folder_name) == ("2024/old.pdf", "old.pdf")
    assert [f.id for f in listing.files] == ["2024/old.pdf"]
    assert await source.download(listing.files[0]) == b"%PDF-1.7 old"


async def test_missing_paths_are_reported(source: LocalFolderSource) -> None:
    with pytest.raises(FolderNotFoundError, match="does not exist"):
        await source.list_files("local:nope.pdf")


async def test_downloads_by_id(source: LocalFolderSource) -> None:
    listing = await source.list_files("local:")

    assert await source.download(listing.files[0]) == b"%PDF-1.7 invoice"


@pytest.mark.parametrize("link", ["local:../", "local:../../etc", "local:2024/../.."])
async def test_refuses_folders_outside_the_root(source: LocalFolderSource, link: str) -> None:
    with pytest.raises(FolderNotFoundError):
        await source.list_files(link)


async def test_refuses_files_outside_the_root(source: LocalFolderSource, root: Path) -> None:
    (root.parent / "secret.txt").write_text("nope")
    outside = SourceFile(id="../secret.txt", name="secret.txt", mime_type="text/plain")

    with pytest.raises(FileNotAccessibleError):
        await source.download(outside)


async def test_explains_the_link_syntax(source: LocalFolderSource) -> None:
    with pytest.raises(InvalidLinkError, match="local:"):
        await source.list_files("https://drive.google.com/drive/folders/abc")


async def test_enforces_the_size_limit(root: Path) -> None:
    (root / "big.pdf").write_bytes(b"x" * 200)
    source = LocalFolderSource(root, max_file_bytes=100)

    with pytest.raises(FileTooLargeError):
        await source.download(SourceFile(id="big.pdf", name="big.pdf", mime_type="application/pdf"))
