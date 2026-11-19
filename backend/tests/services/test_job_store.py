from datetime import UTC, datetime

from drive_text_extractor.domain.jobs import FileTask, Job
from drive_text_extractor.domain.models import ExtractionOptions, SourceFile
from drive_text_extractor.services.job_store import InMemoryJobStore


def make_job(job_id: str, *, finished: bool) -> Job:
    task = FileTask(SourceFile(id=f"{job_id}-f", name="a.pdf", mime_type="application/pdf"))
    if finished:
        task.cancel()
    return Job(job_id, "link", "folder", "Folder", ExtractionOptions(), [task], datetime.now(UTC))


def test_stores_and_returns_jobs() -> None:
    store = InMemoryJobStore()
    job = make_job("a", finished=False)

    store.add(job)

    assert store.get("a") is job
    assert store.get("missing") is None


def test_evicts_oldest_finished_jobs_beyond_the_limit() -> None:
    store = InMemoryJobStore(max_jobs=2)
    for job_id in ["old", "mid", "new"]:
        store.add(make_job(job_id, finished=True))

    assert store.get("old") is None
    assert store.get("mid") is not None
    assert len(store) == 2


def test_never_evicts_a_running_job() -> None:
    store = InMemoryJobStore(max_jobs=1)
    store.add(make_job("running", finished=False))
    store.add(make_job("done", finished=True))

    assert store.get("running") is not None
    assert store.get("done") is None
