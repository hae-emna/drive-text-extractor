"""Batch jobs: one task per selected file, each with its own lifecycle.

    pending --start--> processing --succeed--> done
       |                    `------fail------> failed
       `------cancel------> cancelled

Transitions are explicit methods so an impossible move (e.g. finishing a task twice) fails loudly
instead of silently corrupting the job's state.
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from drive_text_extractor.domain.models import ExtractionOptions, ExtractionResult, SourceFile


class FileStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


FINAL_STATUSES = frozenset({FileStatus.DONE, FileStatus.FAILED, FileStatus.CANCELLED})


@dataclass(frozen=True, slots=True)
class Failure:
    code: str
    message: str


@dataclass(slots=True)
class FileTask:
    file: SourceFile
    status: FileStatus = FileStatus.PENDING
    result: ExtractionResult | None = None
    failure: Failure | None = None
    duration_ms: int | None = None

    @property
    def is_final(self) -> bool:
        return self.status in FINAL_STATUSES

    def start(self) -> None:
        self._move(FileStatus.PENDING, FileStatus.PROCESSING)

    def succeed(self, result: ExtractionResult, *, duration_ms: int) -> None:
        self._move(FileStatus.PROCESSING, FileStatus.DONE)
        self.result = result
        self.duration_ms = duration_ms

    def fail(self, failure: Failure, *, duration_ms: int) -> None:
        self._move(FileStatus.PROCESSING, FileStatus.FAILED)
        self.failure = failure
        self.duration_ms = duration_ms

    def cancel(self) -> None:
        self._move(FileStatus.PENDING, FileStatus.CANCELLED)

    def _move(self, expected: FileStatus, target: FileStatus) -> None:
        if self.status is not expected:
            raise ValueError(f"cannot go from {self.status} to {target} (expected {expected})")
        self.status = target


@dataclass(slots=True)
class Job:
    id: str
    link: str
    folder_id: str
    folder_name: str
    options: ExtractionOptions
    tasks: list[FileTask]
    created_at: datetime
    finished_at: datetime | None = None
    cancel_requested: bool = False
    _by_file_id: dict[str, FileTask] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._by_file_id = {task.file.id: task for task in self.tasks}

    @property
    def is_finished(self) -> bool:
        return all(task.is_final for task in self.tasks)

    def counts(self) -> dict[FileStatus, int]:
        tally = Counter(task.status for task in self.tasks)
        return {status: tally.get(status, 0) for status in FileStatus}

    def task_for(self, file_id: str) -> FileTask:
        return self._by_file_id[file_id]
