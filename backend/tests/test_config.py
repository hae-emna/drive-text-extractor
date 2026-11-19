import pytest

from drive_text_extractor.config import Settings


def make_settings() -> Settings:
    # Ignore any developer .env file so tests only see what they set explicitly.
    return Settings(_env_file=None)  # type: ignore[call-arg]


def test_defaults_apply_when_environment_is_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("OCR_MODELS_DIR", raising=False)

    settings = make_settings()

    assert settings.google_api_key is None
    assert settings.log_level == "INFO"
    assert settings.image_ocr_engine == "rapidocr"
    assert settings.ocr_models_dir is None


def test_values_are_read_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = make_settings()

    assert settings.google_api_key is not None
    assert settings.google_api_key.get_secret_value() == "test-key"
    assert settings.log_level == "DEBUG"


def test_api_key_is_masked_when_printed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "super-secret")

    assert "super-secret" not in repr(make_settings())


def test_file_size_limit_is_exposed_in_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_FILE_SIZE_MB", "10")

    assert make_settings().max_file_bytes == 10_000_000


def test_rejects_nonsensical_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_FILE_SIZE_MB", "0")

    with pytest.raises(ValueError, match="max_file_size_mb"):
        make_settings()
