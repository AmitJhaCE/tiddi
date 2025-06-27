import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture
def client():
    """Sync test client - much simpler"""
    with TestClient(app) as c:
        yield c

@pytest.fixture
def sample_note():
    return {
        "text": "Meeting with John about ProjectX React components",
        "tags": ["meeting"],
        "session_id": "test-session"
    }