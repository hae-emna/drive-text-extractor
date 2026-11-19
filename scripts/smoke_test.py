"""End-to-end check against a running server in demo mode (FILE_SOURCE=local).

Lists the sample folder, extracts every supported file, waits for the batch and checks the
outcome and the export. Standard library only, so it runs anywhere Python 3 does:

    python scripts/smoke_test.py http://localhost:8000
"""

import json
import sys
import time
import urllib.request
from typing import Any

EXPECTED = {"done": 7, "failed": 1}  # samples/input: corrupted.pdf is meant to fail


def call(base: str, path: str, body: dict[str, Any] | None = None) -> Any:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        base + path, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read()
    return (
        json.loads(raw)
        if response.headers.get_content_type() == "application/json"
        else raw
    )


def wait_for_health(base: str, seconds: int = 60) -> dict[str, Any]:
    deadline = time.monotonic() + seconds
    while True:
        try:
            health: dict[str, Any] = call(base, "/api/health")
            return health
        except OSError:
            if time.monotonic() > deadline:
                raise
            time.sleep(1)


def main(base: str) -> None:
    health = wait_for_health(base)
    print("health:", health)
    assert health["source"] == "local", "start the server with FILE_SOURCE=local"
    assert all(language["installed"] for language in health["languages"]), (
        "missing OCR packs"
    )

    listing = call(base, "/api/files/list", {"link": "local:"})
    file_ids = [file["id"] for file in listing["files"]]
    print(
        f"listed {len(file_ids)} files, skipped {[s['name'] for s in listing['skipped']]}"
    )

    job = call(
        base,
        "/api/jobs",
        {"link": "local:", "file_ids": file_ids, "languages": ["eng", "fra", "ara"]},
    )
    deadline = time.monotonic() + 180
    while job["status"] != "finished":
        assert time.monotonic() < deadline, "batch did not finish in time"
        time.sleep(1)
        job = call(base, f"/api/jobs/{job['id']}")

    for result in job["files"]:
        print(f"  {result['file']['name']:24} {result['status']:7} {result['method']}")
    summary = job["summary"]
    assert {k: summary[k] for k in EXPECTED} == EXPECTED, summary

    export = call(base, f"/api/jobs/{job['id']}/export")
    assert export["schema_version"] == "1.1"
    assert b'<div id="root">' in call(base, "/"), "web page not served"
    print("smoke test passed")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000")
