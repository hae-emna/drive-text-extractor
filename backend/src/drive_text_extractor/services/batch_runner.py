"""Run a job: each file goes through download -> route -> extract on its own."""

import asyncio
import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime

from drive_text_extractor.domain.errors import DomainError
from drive_text_extractor.domain.jobs import Failure, FileTask, Job
from drive_text_extractor.domain.models import ExtractionOptions, ExtractionResult, SourceFile
from drive_text_extractor.domain.ports import FileSource
from drive_text_extractor.domain.units import MS_PER_SECOND
from drive_text_extractor.services.router import ExtractorRouter

logger = logging.getLogger(__name__)

DEFAULT_CONCURRENCY = 2

UNEXPECTED_FAILURE = Failure(
    code="internal_error",
    message="An unexpected error occurred while processing this file.",
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class BatchRunner:
    """Processes the files of a job with bounded concurrency.

    Every file is isolated: an expected failure (a ``DomainError``) is recorded with its code and
    message, anything else is logged with its traceback and recorded as ``internal_error``. Either
    way the other files carry on.
    """

    def __init__(
        self,
        source: FileSource,
        router: ExtractorRouter,
        *,
        concurrency: int = DEFAULT_CONCURRENCY,
        clock: Callable[[], float] = time.perf_counter,
        now: Callable[[], datetime] = _utc_now,
    ) -> None:
        if concurrency < 1:
            raise ValueError("concurrency must be at least 1")
        self._source = source
        self._router = router
        self._concurrency = concurrency
        self._clock = clock
        self._now = now

    async def run(self, job: Job) -> None:
        slots = asyncio.Semaphore(self._concurrency)

        async def process_in_slot(task: FileTask) -> None:
            async with slots:
                await self._process(job, task)

        await asyncio.gather(*(process_in_slot(task) for task in job.tasks))
        job.finished_at = self._now()
        logger.info("Job %s finished: %s", job.id, {k.value: v for k, v in job.counts().items()})

    async def _process(self, job: Job, task: FileTask) -> None:
        if job.cancel_requested:
            task.cancel()
            return
        task.start()
        started = self._clock()
        try:
            result = await self._extract(task.file, job.options)
        except DomainError as error:
            task.fail(Failure(error.code, error.message), duration_ms=self._since(started))
            logger.info("Job %s: %s failed (%s)", job.id, task.file.display_path, error.code)
        except Exception:
            task.fail(UNEXPECTED_FAILURE, duration_ms=self._since(started))
            logger.exception("Job %s: unexpected error on %s", job.id, task.file.display_path)
        else:
            task.succeed(result, duration_ms=self._since(started))
            logger.info(
                "Job %s: %s done via %s in %s ms",
                job.id,
                task.file.display_path,
                result.method,
                task.duration_ms,
            )

    async def _extract(self, file: SourceFile, options: ExtractionOptions) -> ExtractionResult:
        data = await self._source.download(file)
        extractor = self._router.select(data)
        # Parsing and OCR are CPU-bound: run them in a worker thread, off the event loop.
        return await asyncio.to_thread(extractor.extract, data, options)

    def _since(self, started: float) -> int:
        return round((self._clock() - started) * MS_PER_SECOND)
