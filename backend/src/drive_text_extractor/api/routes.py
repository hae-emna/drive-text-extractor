"""HTTP endpoints. Each one validates input, calls one service method and maps the result."""

import re
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from drive_text_extractor import __version__
from drive_text_extractor.api.schemas import (
    ErrorResponse,
    FolderListingOut,
    HealthOut,
    JobOut,
    LanguageOut,
    ListFolderRequest,
    StartJobRequest,
    export_out,
    job_out,
    listing_out,
)
from drive_text_extractor.container import Container
from drive_text_extractor.domain.jobs import Job
from drive_text_extractor.domain.languages import SUPPORTED_LANGUAGES


def get_container(request: Request) -> Container:
    return cast(Container, request.app.state.container)


ContainerDep = Annotated[Container, Depends(get_container)]

_ERRORS: dict[int | str, dict[str, Any]] = {
    code: {"model": ErrorResponse} for code in (400, 404, 422, 429, 502, 503)
}

router = APIRouter(responses=_ERRORS)


@router.get("/health", response_model=HealthOut, tags=["meta"])
def health(container: ContainerDep) -> HealthOut:
    installed = set(container.installed_languages)
    return HealthOut(
        version=__version__,
        source=container.source_type,
        languages=[
            LanguageOut(code=code, name=name, installed=code in installed)
            for code, name in SUPPORTED_LANGUAGES.items()
        ],
    )


@router.post("/folders/list", response_model=FolderListingOut, tags=["folders"])
async def list_files(body: ListFolderRequest, container: ContainerDep) -> FolderListingOut:
    listing = await container.browser.browse(body.link, recursive=body.recursive)
    return listing_out(listing)


@router.post("/jobs", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED, tags=["jobs"])
async def start_job(body: StartJobRequest, container: ContainerDep) -> JobOut:
    job = await container.jobs.start(
        body.link, body.file_ids, languages=body.languages, recursive=body.recursive
    )
    return _job_out(job, container)


@router.get("/jobs/{job_id}", response_model=JobOut, tags=["jobs"])
def get_job(job_id: str, container: ContainerDep) -> JobOut:
    return _job_out(container.jobs.get(job_id), container)


@router.post("/jobs/{job_id}/cancel", response_model=JobOut, tags=["jobs"])
def cancel_job(job_id: str, container: ContainerDep) -> JobOut:
    return _job_out(container.jobs.cancel(job_id), container)


@router.get("/jobs/{job_id}/export", tags=["jobs"])
def export_job(job_id: str, container: ContainerDep) -> JSONResponse:
    """The batch results as a downloadable, versioned JSON document."""
    job = container.jobs.get(job_id)
    export = export_out(
        job,
        source_type=container.source_type,
        low_confidence_below=container.settings.low_confidence_threshold,
    )
    return JSONResponse(
        content=export.model_dump(mode="json"),
        headers={"Content-Disposition": f'attachment; filename="{_export_filename(job)}"'},
    )


def _job_out(job: Job, container: Container) -> JobOut:
    return job_out(job, low_confidence_below=container.settings.low_confidence_threshold)


def _export_filename(job: Job) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", job.folder_name).strip("-").lower() or "folder"
    return f"extraction-{slug}-{job.created_at:%Y%m%d-%H%M%S}.json"
