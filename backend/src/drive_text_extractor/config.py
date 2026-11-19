"""Application settings.

Every tunable is read here, once, from environment variables or an optional ``.env`` file.
The rest of the code receives a ``Settings`` instance and never touches ``os.environ``.
"""

from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # The repository-level .env is shared with docker compose; a backend-local one wins.
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    google_api_key: SecretStr | None = None
    """Google Cloud API key with the Drive API enabled. Only needed for the Drive source."""

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # --- Source limits ---
    max_file_size_mb: int = Field(default=25, ge=1, le=500)
    """Files above this size are refused before (or while) downloading."""

    max_listed_files: int = Field(default=1000, ge=1)
    """Listing stops after this many files and the folder is flagged as truncated."""

    @property
    def max_file_bytes(self) -> int:
        return self.max_file_size_mb * 1_000_000
