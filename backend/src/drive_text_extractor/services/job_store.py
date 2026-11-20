"""Where jobs live while they run and while the user reads their results."""

from collections import OrderedDict

from drive_text_extractor.domain.jobs import Job

DEFAULT_MAX_JOBS = 100
"""Older jobs are forgotten once this many are kept."""


class InMemoryJobStore:
    """Keeps the most recent jobs in process memory.

    Good enough for a single-process POC; jobs are lost on restart. A production version would
    implement the same three methods on Redis or a database.
    """

    def __init__(self, max_jobs: int = DEFAULT_MAX_JOBS) -> None:
        self._max_jobs = max_jobs
        self._jobs: OrderedDict[str, Job] = OrderedDict()

    def add(self, job: Job) -> None:
        self._jobs[job.id] = job
        self._evict_finished_overflow()

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def __len__(self) -> int:
        return len(self._jobs)

    def _evict_finished_overflow(self) -> None:
        """Drop the oldest finished jobs beyond the limit; a running job is never dropped."""
        overflow = len(self._jobs) - self._max_jobs
        for job_id in [job_id for job_id, job in self._jobs.items() if job.is_finished]:
            if overflow <= 0:
                return
            del self._jobs[job_id]
            overflow -= 1
