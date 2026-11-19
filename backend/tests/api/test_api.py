"""End-to-end through HTTP: real routes, services and extractors; fake Drive and OCR."""

import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from drive_text_extractor.config import Settings
from drive_text_extractor.domain.errors import FolderNotFoundError, InvalidLinkError
from drive_text_extractor.domain.models import SourceFile
from drive_text_extractor.main import create_app
from tests.fakes import FakeFileSource, FakeOcrEngine
from tests.images import png_bytes
from tests.pdf_factory import make_pdf

LINK = "https://drive.google.com/drive/folders/FakeFolderId01"
FILES = [
    SourceFile("pdf-1", "invoice.pdf", "application/pdf", 1200, "2026-11-01T10:00:00Z"),
    SourceFile("png-1", "receipt.png", "image/png", 800, "2026-11-01T10:00:00Z"),
    SourceFile("bad-1", "broken.pdf", "application/pdf", 20, "2026-11-01T10:00:00Z"),
    SourceFile("doc-1", "notes", "application/vnd.google-apps.document"),
]


def settings(**overrides: Any) -> Settings:
    return Settings(_env_file=None, google_api_key=None, **overrides)  # type: ignore[call-arg]


@pytest.fixture
def source() -> FakeFileSource:
    return FakeFileSource(
        files=FILES,
        contents={
            "pdf-1": make_pdf(["Invoice 2026-001 total 120 TND"]),
            "png-1": png_bytes(),
            "bad-1": b"%PDF-1.7 truncated",
        },
    )


@pytest.fixture
def client(source: FakeFileSource) -> Iterator[TestClient]:
    app = create_app(
        settings(),
        file_source=source,
        ocr_engine=FakeOcrEngine(text="إيصال receipt", confidence=55.0),
        installed_languages=("eng", "fra"),
    )
    with TestClient(app) as test_client:
        yield test_client


def wait_until_finished(client: TestClient, job_id: str) -> dict[str, Any]:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        job: dict[str, Any] = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] == "finished":
            return job
        time.sleep(0.01)
    raise AssertionError("job did not finish in time")


def start(client: TestClient, file_ids: list[str], languages: list[str] | None = None) -> Any:
    body = {"link": LINK, "file_ids": file_ids, "languages": languages or ["eng"]}
    return client.post("/api/jobs", json=body)


def test_health_reports_version_source_and_languages(client: TestClient) -> None:
    body = client.get("/api/health").json()

    assert body["status"] == "ok"
    assert body["source"] == "google_drive"
    assert body["languages"] == [
        {"code": "eng", "name": "English", "installed": True},
        {"code": "fra", "name": "French", "installed": True},
        {"code": "ara", "name": "Arabic", "installed": False},
    ]


def test_lists_supported_files_and_explains_skipped_ones(client: TestClient) -> None:
    response = client.post("/api/folders/list", json={"link": LINK})

    assert response.status_code == 200
    body = response.json()
    assert body["folder"] == {"id": "FakeFolderId01", "name": "Fake folder"}
    assert [f["name"] for f in body["files"]] == ["invoice.pdf", "receipt.png", "broken.pdf"]
    assert body["files"][0] == {
        "id": "pdf-1",
        "name": "invoice.pdf",
        "path": "invoice.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 1200,
        "modified_time": "2026-11-01T10:00:00Z",
    }
    assert body["skipped"][0]["name"] == "notes"
    assert body["truncated"] is False


@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (InvalidLinkError(), 400, "invalid_link"),
        (FolderNotFoundError(), 404, "folder_not_found"),
    ],
)
def test_listing_errors_use_the_error_envelope(
    client: TestClient, source: FakeFileSource, error: Exception, status: int, code: str
) -> None:
    source.list_error = error

    response = client.post("/api/folders/list", json={"link": LINK})

    assert response.status_code == status
    assert response.json() == {"error": {"code": code, "message": str(error)}}


def test_invalid_request_bodies_use_the_error_envelope(client: TestClient) -> None:
    response = client.post("/api/folders/list", json={})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "invalid_request"
    assert error["message"].startswith("link:")


def test_runs_a_batch_and_reports_each_file(client: TestClient) -> None:
    response = start(client, ["pdf-1", "png-1", "bad-1"], languages=["ara", "fra"])

    assert response.status_code == 202
    job = wait_until_finished(client, response.json()["id"])
    assert job["languages"] == ["ara", "fra"]
    assert job["summary"] == {
        "total": 3,
        "pending": 0,
        "processing": 0,
        "done": 2,
        "failed": 1,
        "cancelled": 0,
    }
    pdf, png, bad = job["files"]
    assert (pdf["status"], pdf["method"], pdf["text"]) == (
        "done",
        "pdf_parser",
        "Invoice 2026-001 total 120 TND",
    )
    assert (png["method"], png["mean_confidence"], png["low_confidence"]) == ("ocr", 55.0, True)
    assert bad["status"] == "failed"
    assert bad["error"]["code"] == "corrupt_file"


def test_exports_results_as_a_versioned_json_download(client: TestClient) -> None:
    job_id = start(client, ["pdf-1"]).json()["id"]
    wait_until_finished(client, job_id)

    response = client.get(f"/api/jobs/{job_id}/export")

    assert response.status_code == 200
    assert response.headers["content-disposition"].startswith(
        'attachment; filename="extraction-fake-folder-'
    )
    export = response.json()
    assert export["schema_version"] == "1.0"
    assert export["source"]["type"] == "google_drive"
    assert export["source"]["link"] == LINK
    assert export["files"][0]["text"] == "Invoice 2026-001 total 120 TND"


def test_cancel_marks_the_job(client: TestClient) -> None:
    job_id = start(client, ["pdf-1", "png-1"]).json()["id"]

    response = client.post(f"/api/jobs/{job_id}/cancel")

    assert response.status_code == 200
    assert response.json()["cancel_requested"] is True
    wait_until_finished(client, job_id)


@pytest.mark.parametrize(
    ("file_ids", "languages", "code"),
    [
        (["doc-1"], ["eng"], "invalid_selection"),
        (["pdf-1"], ["deu"], "unsupported_language"),
    ],
)
def test_rejects_invalid_jobs(
    client: TestClient, file_ids: list[str], languages: list[str], code: str
) -> None:
    response = start(client, file_ids, languages)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == code


def test_unknown_job_is_not_found(client: TestClient) -> None:
    response = client.get("/api/jobs/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "job_not_found"


def test_unexpected_errors_return_a_generic_500(source: FakeFileSource) -> None:
    source.list_error = RuntimeError("database password is hunter2")
    app = create_app(
        settings(), file_source=source, ocr_engine=FakeOcrEngine(), installed_languages=()
    )

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/api/folders/list", json={"link": LINK})

    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Unexpected server error."}
    }


def test_without_api_key_the_real_drive_source_explains_the_setup() -> None:
    app = create_app(settings(), ocr_engine=FakeOcrEngine(), installed_languages=())

    with TestClient(app) as client:
        response = client.post("/api/folders/list", json={"link": LINK})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "source_not_configured"


def test_demo_mode_runs_the_whole_flow_on_a_local_folder(tmp_path: Path) -> None:
    (tmp_path / "invoice.pdf").write_bytes(make_pdf(["Local invoice 7 from the demo folder"]))
    (tmp_path / "readme.txt").write_text("not extracted")
    app = create_app(
        settings(file_source="local", local_folder=tmp_path),
        ocr_engine=FakeOcrEngine(),
        installed_languages=("eng",),
    )

    with TestClient(app) as client:
        assert client.get("/api/health").json()["source"] == "local"
        listing = client.post("/api/folders/list", json={"link": "local:"}).json()
        assert [f["name"] for f in listing["files"]] == ["invoice.pdf"]
        assert [s["name"] for s in listing["skipped"]] == ["readme.txt"]

        body = {"link": "local:", "file_ids": ["invoice.pdf"], "languages": ["eng"]}
        job = wait_until_finished(client, client.post("/api/jobs", json=body).json()["id"])

    assert job["files"][0]["text"] == "Local invoice 7 from the demo folder"
