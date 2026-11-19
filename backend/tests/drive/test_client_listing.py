import httpx
import pytest

from drive_text_extractor.domain.errors import (
    FolderNotFoundError,
    InvalidLinkError,
    RateLimitedError,
    SourceNotConfiguredError,
    SourceUnavailableError,
)
from drive_text_extractor.drive.client import GoogleDriveSource, RetryPolicy
from tests.drive.fake_drive import API_KEY, FOLDER, FakeDrive, drive_error

pytestmark = pytest.mark.anyio

ROOT = "RootFolderId0001"
LINK = f"https://drive.google.com/drive/folders/{ROOT}?usp=sharing"
PDF = "application/pdf"
PNG = "image/png"


class SleepRecorder:
    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


@pytest.fixture
def drive() -> FakeDrive:
    fake = FakeDrive()
    fake.add_folder(ROOT, "Invoices")
    return fake


@pytest.fixture
def sleep() -> SleepRecorder:
    return SleepRecorder()


def make_source(
    drive: FakeDrive,
    sleep: SleepRecorder,
    *,
    api_key: str | None = API_KEY,
    max_items: int = 1000,
    page_size: int = 1000,
) -> GoogleDriveSource:
    return GoogleDriveSource(
        drive.client(),
        api_key,
        max_file_bytes=10_000,
        max_items=max_items,
        page_size=page_size,
        retry=RetryPolicy(attempts=3, base_delay=0.5, max_delay=4.0),
        sleep=sleep,
    )


async def test_lists_files_with_metadata_and_folder_name(
    drive: FakeDrive, sleep: SleepRecorder
) -> None:
    drive.add_file("FileId000001", "scan.png", PNG, ROOT, b"12345")
    drive.add_file("FileId000002", "report.pdf", PDF, ROOT, b"123")

    listing = await make_source(drive, sleep).list_folder(LINK)

    assert listing.folder_id == ROOT
    assert listing.folder_name == "Invoices"
    assert [(f.name, f.mime_type, f.size_bytes) for f in listing.files] == [
        ("report.pdf", PDF, 3),
        ("scan.png", PNG, 5),
    ]
    assert listing.files[0].modified_time == "2026-11-01T10:00:00.000Z"
    assert listing.files[0].path == ""
    assert not listing.truncated


async def test_follows_pagination(drive: FakeDrive, sleep: SleepRecorder) -> None:
    for n in range(5):
        drive.add_file(f"FileId00000{n}", f"{n}.pdf", PDF, ROOT)

    listing = await make_source(drive, sleep, page_size=2).list_folder(LINK)

    assert [f.name for f in listing.files] == ["0.pdf", "1.pdf", "2.pdf", "3.pdf", "4.pdf"]
    assert sum(r.url.path == "/drive/v3/files" for r in drive.requests) == 3


async def test_reports_subfolders_as_skipped_when_not_recursive(
    drive: FakeDrive, sleep: SleepRecorder
) -> None:
    drive.add_folder("SubFolderId01", "2024", parent=ROOT)
    drive.add_file("FileId000001", "inner.pdf", PDF, "SubFolderId01")

    listing = await make_source(drive, sleep).list_folder(LINK)

    assert listing.files == ()
    assert [(s.name, s.mime_type) for s in listing.skipped] == [("2024/", FOLDER)]
    assert "Include subfolders" in listing.skipped[0].reason


async def test_walks_subfolders_when_recursive(drive: FakeDrive, sleep: SleepRecorder) -> None:
    drive.add_file("FileId000001", "top.pdf", PDF, ROOT)
    drive.add_folder("SubFolderId01", "2024", parent=ROOT)
    drive.add_folder("SubFolderId02", "q1", parent="SubFolderId01")
    drive.add_file("FileId000002", "deep.png", PNG, "SubFolderId02")

    listing = await make_source(drive, sleep).list_folder(LINK, recursive=True)

    assert [f.display_path for f in listing.files] == ["top.pdf", "2024/q1/deep.png"]
    assert listing.skipped == ()


async def test_resolves_file_shortcuts_and_skips_folder_shortcuts(
    drive: FakeDrive, sleep: SleepRecorder
) -> None:
    drive.add_shortcut("ShortcutId01", "linked.pdf", ROOT, "TargetFileId1", PDF)
    drive.add_shortcut("ShortcutId02", "Other folder", ROOT, "TargetFolder1", FOLDER)

    listing = await make_source(drive, sleep).list_folder(LINK)

    assert [(f.id, f.name, f.mime_type) for f in listing.files] == [
        ("TargetFileId1", "linked.pdf", PDF)
    ]
    assert [s.name for s in listing.skipped] == ["Other folder"]


async def test_stops_at_item_limit_and_flags_truncation(
    drive: FakeDrive, sleep: SleepRecorder
) -> None:
    for n in range(4):
        drive.add_file(f"FileId00000{n}", f"{n}.pdf", PDF, ROOT)

    listing = await make_source(drive, sleep, max_items=3).list_folder(LINK)

    assert len(listing.files) == 3
    assert listing.truncated


async def test_sends_the_api_key_in_a_header_not_in_the_url(
    drive: FakeDrive, sleep: SleepRecorder
) -> None:
    await make_source(drive, sleep).list_folder(LINK)

    for request in drive.requests:
        assert request.headers["X-Goog-Api-Key"] == API_KEY
        assert API_KEY not in str(request.url)


async def test_forwards_the_resource_key_of_legacy_links(
    drive: FakeDrive, sleep: SleepRecorder
) -> None:
    await make_source(drive, sleep).list_folder(f"{LINK}&resourcekey=0-legacy")

    assert drive.requests[0].headers["X-Goog-Drive-Resource-Keys"] == f"{ROOT}/0-legacy"


async def test_rejects_a_link_to_a_file(drive: FakeDrive, sleep: SleepRecorder) -> None:
    drive.add_file("FileId000001", "a.pdf", PDF, ROOT)

    with pytest.raises(InvalidLinkError, match="not a folder"):
        await make_source(drive, sleep).list_folder("https://drive.google.com/open?id=FileId000001")


async def test_private_or_missing_folder(drive: FakeDrive, sleep: SleepRecorder) -> None:
    with pytest.raises(FolderNotFoundError):
        await make_source(drive, sleep).list_folder("MissingFolderId")


async def test_missing_api_key_fails_before_any_request(
    drive: FakeDrive, sleep: SleepRecorder
) -> None:
    with pytest.raises(SourceNotConfiguredError):
        await make_source(drive, sleep, api_key=None).list_folder(LINK)

    assert drive.requests == []


@pytest.mark.parametrize(
    ("reason", "hint"),
    [
        ("API_KEY_INVALID", "invalid"),
        ("SERVICE_DISABLED", "not enabled"),
        ("API_KEY_SERVICE_BLOCKED", "not allowed"),
    ],
)
async def test_configuration_problems_are_explained(
    drive: FakeDrive, sleep: SleepRecorder, reason: str, hint: str
) -> None:
    drive.then_respond(drive_error(403, reason))

    with pytest.raises(SourceNotConfiguredError, match=hint):
        await make_source(drive, sleep).list_folder(LINK)

    assert sleep.delays == []


async def test_retries_rate_limits_with_exponential_backoff(
    drive: FakeDrive, sleep: SleepRecorder
) -> None:
    drive.then_respond(
        drive_error(429, "rateLimitExceeded"), drive_error(403, "userRateLimitExceeded")
    )

    listing = await make_source(drive, sleep).list_folder(LINK)

    assert listing.folder_name == "Invoices"
    assert sleep.delays == [0.5, 1.0]


async def test_honours_retry_after_up_to_the_cap(drive: FakeDrive, sleep: SleepRecorder) -> None:
    drive.then_respond(
        drive_error(429, "rateLimitExceeded", headers={"Retry-After": "3"}),
        drive_error(429, "rateLimitExceeded", headers={"Retry-After": "60"}),
    )

    await make_source(drive, sleep).list_folder(LINK)

    assert sleep.delays == [3.0, 4.0]


async def test_gives_up_after_the_last_attempt(drive: FakeDrive, sleep: SleepRecorder) -> None:
    drive.then_respond(*[drive_error(429, "rateLimitExceeded")] * 3)

    with pytest.raises(RateLimitedError):
        await make_source(drive, sleep).list_folder(LINK)

    assert len(drive.requests) == 3


async def test_retries_server_and_network_errors(drive: FakeDrive, sleep: SleepRecorder) -> None:
    drive.then_respond(httpx.ConnectError("boom"), drive_error(503, "backendError"))

    listing = await make_source(drive, sleep).list_folder(LINK)

    assert listing.folder_id == ROOT


async def test_persistent_outage_is_reported_as_unavailable(
    drive: FakeDrive, sleep: SleepRecorder
) -> None:
    drive.then_respond(*[httpx.ReadTimeout("slow")] * 3)

    with pytest.raises(SourceUnavailableError):
        await make_source(drive, sleep).list_folder(LINK)
