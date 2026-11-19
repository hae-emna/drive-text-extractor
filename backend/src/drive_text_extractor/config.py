"""Application settings.

Every tunable is read here, once, from environment variables or an optional ``.env`` file.
The rest of the code receives a ``Settings`` instance and never touches ``os.environ``.
"""

from typing import Literal

from pydantic import SecretStr
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
