import pytest
from fastapi.testclient import TestClient

class TestBasicAPI:
    def test_health_check(self, client):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "services" in data

    def test_store_note(self, client, sample_note):
        """Test note storage"""
        response = client.post("/tools/notes", json=sample_note)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "note_id" in data
        assert len(data["entities"]) > 0

    def test_search_notes(self, client, sample_note):
        """Test complete workflow"""
        # Store a note first
        store_response = client.post("/tools/notes", json=sample_note)
        assert store_response.status_code == 200
        
        # Search for it
        search_response = client.get("/tools/notes/search", params={
            "query": "John ProjectX",
            "limit": 5
        })
        assert search_response.status_code == 200
        data = search_response.json()
        assert data["success"] is True
        assert len(data["results"]) > 0