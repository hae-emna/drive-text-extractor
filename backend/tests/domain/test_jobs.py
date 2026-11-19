from datetime import UTC, datetime

import pytest

from drive_text_extractor.domain.jobs import Failure, FileStatus, FileTask, Job
from drive_text_extractor.domain.models import (
    ExtractionMethod,
    ExtractionOptions,
    ExtractionResult,
    PageText,
    SourceFile,
)

RESULT = ExtractionResult(pages=(PageText(1, ExtractionMethod.PDF_PARSER, "text"),))


def task(file_id: str = "a") -> FileTask:
    return FileTask(SourceFile(id=file_id, name=f"{file_id}.pdf", mime_type="application/pdf"))


def job(*tasks: FileTask) -> Job:
    return Job(
        id="job-1",
        link="link",
        folder_id="folder",
        folder_name="Folder",
        options=ExtractionOptions(),
        tasks=list(tasks),
        created_at=datetime(2026, 11, 19, tzinfo=UTC),
    )


def test_happy_path_ends_done_with_result() -> None:
    t = task()

    t.start()
    t.succeed(RESULT, duration_ms=120)

    assert t.status is FileStatus.DONE
    assert t.result is RESULT
    assert t.duration_ms == 120
    assert t.is_final


def test_failure_keeps_code_and_message() -> None:
    t = task()

    t.start()
    t.fail(Failure("corrupt_file", "Damaged."), duration_ms=5)

    assert t.status is FileStatus.FAILED
    assert t.failure == Failure("corrupt_file", "Damaged.")


def test_only_pending_tasks_can_be_cancelled() -> None:
    pending, running = task("a"), task("b")
    running.start()

    pending.cancel()

    assert pending.status is FileStatus.CANCELLED
    with pytest.raises(ValueError, match="cannot go from processing to cancelled"):
        running.cancel()


def test_a_task_cannot_finish_twice() -> None:
    t = task()
    t.start()
    t.succeed(RESULT, duration_ms=1)

    with pytest.raises(ValueError, match="cannot go from done to failed"):
        t.fail(Failure("x", "y"), duration_ms=1)


def test_a_task_must_start_before_finishing() -> None:
    with pytest.raises(ValueError, match="cannot go from pending to done"):
        task().succeed(RESULT, duration_ms=1)


def test_job_counts_every_status_and_knows_when_it_is_finished() -> None:
    done, failed, pending = task("a"), task("b"), task("c")
    done.start()
    done.succeed(RESULT, duration_ms=1)
    failed.start()
    failed.fail(Failure("x", "y"), duration_ms=1)
    batch = job(done, failed, pending)

    assert batch.counts() == {
        FileStatus.PENDING: 1,
        FileStatus.PROCESSING: 0,
        FileStatus.DONE: 1,
        FileStatus.FAILED: 1,
        FileStatus.CANCELLED: 0,
    }
    assert not batch.is_finished

    pending.cancel()
    assert batch.is_finished


def test_job_finds_tasks_by_file_id() -> None:
    a, b = task("a"), task("b")

    assert job(a, b).task_for("b") is b
