"""The wired services the HTTP layer works with. Built once, in ``main.create_app``."""

from dataclasses import dataclass

from drive_text_extractor.config import Settings, SourceType
from drive_text_extractor.services.folder_browser import FolderBrowser
from drive_text_extractor.services.job_service import JobService


@dataclass(frozen=True, slots=True)
class Container:
    settings: Settings
    browser: FolderBrowser
    jobs: JobService
    source_type: SourceType
    installed_languages: tuple[str, ...]
