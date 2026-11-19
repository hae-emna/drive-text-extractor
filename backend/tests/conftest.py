import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Run ``@pytest.mark.anyio`` tests on asyncio only (the app does not use trio)."""
    return "asyncio"
