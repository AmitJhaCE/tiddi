import pytest
import asyncio
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
    
@pytest.fixture(autouse=True)
async def cleanup_async_clients():
    """Auto cleanup async clients after each test to prevent event loop issues"""
    yield
    # Cleanup after each test
    try:
        from src.services.openai_service import openai_service
        from src.services.entity_service import entity_service
        
        # Close clients to prevent event loop closure errors
        await openai_service.close()
        await entity_service.close()
        
        # Small delay to allow cleanup to complete
        await asyncio.sleep(0.01)
        
    except Exception as e:
        # Don't fail tests due to cleanup issues, just log
        print(f"Cleanup warning: {e}")

@pytest.fixture
def sample_bulk_request():
    """Sample bulk request for testing"""
    return {
        "notes": [
            {
                "text": "First test note with John and ProjectX",
                "tags": ["test"],
                "session_id": "bulk-test"
            },
            {
                "text": "Second test note about React development",
                "tags": ["development"],
                "session_id": "bulk-test"
            }
        ],
        "session_id": "bulk-test-session"
    }