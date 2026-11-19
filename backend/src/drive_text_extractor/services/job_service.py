"""Use cases around batch jobs: start one, follow it, cancel it."""

import asyncio
import logging
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from uuid import uuid4

from drive_text_extractor.domain.errors import InvalidSelectionError, JobNotFoundError
from drive_text_extractor.domain.jobs import FileTask, Job
from drive_text_extractor.domain.languages import validate_languages
from drive_text_extractor.domain.models import ExtractionOptions
from drive_text_extractor.services.batch_runner import BatchRunner
from drive_text_extractor.services.folder_browser import FolderBrowser
from drive_text_extractor.services.job_store import InMemoryJobStore

logger = logging.getLogger(__name__)


def _new_id() -> str:
    return uuid4().hex


def _utc_now() -> datetime:
    return datetime.now(UTC)


class JobService:
    def __init__(
        self,
        browser: FolderBrowser,
        runner: BatchRunner,
        store: InMemoryJobStore,
        *,
        new_id: Callable[[], str] = _new_id,
        now: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._browser = browser
        self._runner = runner
        self._store = store
        self._new_id = new_id
        self._now = now
        self._running: set[asyncio.Task[None]] = set()

    async def start(
        self,
        link: str,
        file_ids: Sequence[str],
        *,
        languages: Sequence[str],
        recursive: bool = False,
    ) -> Job:
        """Create a job for the selected files and start processing it in the background.

        The folder is listed again on the server so that only files which really belong to it,
        with their authoritative metadata, can be processed: the client only sends ids.
        """
        options = ExtractionOptions(languages=validate_languages(languages))
        wanted = list(dict.fromkeys(file_ids))
        if not wanted:
            raise InvalidSelectionError()

        listing = await self._browser.browse(link, recursive=recursive)
        available = {file.id: file for file in listing.files}
        missing = [file_id for file_id in wanted if file_id not in available]
        if missing:
            raise InvalidSelectionError(
                f"{len(missing)} selected file(s) are no longer in this folder. Reload the list."
            )

        job = Job(
            id=self._new_id(),
            link=link,
            folder_id=listing.folder_id,
            folder_name=listing.folder_name,
            options=options,
            tasks=[FileTask(available[file_id]) for file_id in wanted],
            created_at=self._now(),
            link_kind=listing.kind,
        )
        self._store.add(job)
        self._run_in_background(job)
        logger.info("Job %s started: %d file(s), languages=%s", job.id, len(wanted), languages)
        return job

    def get(self, job_id: str) -> Job:
        job = self._store.get(job_id)
        if job is None:
            raise JobNotFoundError()
        return job

    def cancel(self, job_id: str) -> Job:
        """Files not started yet are skipped; files already being processed finish normally."""
        job = self.get(job_id)
        job.cancel_requested = True
        return job

    async def shutdown(self) -> None:
        for task in self._running:
            task.cancel()
        await asyncio.gather(*self._running, return_exceptions=True)

    def _run_in_background(self, job: Job) -> None:
        task = asyncio.create_task(self._runner.run(job), name=f"job-{job.id}")
        # Keep a reference: the event loop only holds weak references to tasks.
        self._running.add(task)
        task.add_done_callback(self._running.discard)
        task.add_done_callback(_log_crash)


def _log_crash(task: asyncio.Task[None]) -> None:
    if not task.cancelled() and task.exception() is not None:
        logger.error("Background %s crashed", task.get_name(), exc_info=task.exception())
