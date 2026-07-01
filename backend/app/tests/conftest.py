import asyncio
import pytest

@pytest.fixture(scope="session")
def event_loop():
    """Overrides the default event_loop fixture to run all tests in the same session loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    # Let pytest clean up the loop or close it if we created a new one
    if not loop.is_closed():
        try:
            loop.close()
        except RuntimeError:
            pass
