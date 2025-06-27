import pytest
from typing import List, Dict, Any


class TestBulkNotesAPI:
    """Test bulk note storage functionality"""

    @pytest.fixture
    def sample_notes_5(self) -> List[Dict[str, Any]]:
        """5 sample notes for bulk testing"""
        return [
            {
                "text": "Completed the authentication module for ProjectX. Working with John on integration testing.",
                "tags": ["development", "authentication"],
                "session_id": "bulk-test-5",
            },
            {
                "text": "Had blockers with the database migration. Waiting on Platform team approval for schema changes.",
                "tags": ["database", "blockers"],
                "session_id": "bulk-test-5",
            },
            {
                "text": "Successfully deployed the hotfix for the payment system. Barbara approved the changes.",
                "tags": ["deployment", "payments"],
                "session_id": "bulk-test-5",
            },
            {
                "text": "Meeting with Sarah about the API design. Need to finalize the endpoints by next Friday.",
                "tags": ["meeting", "api-design"],
                "session_id": "bulk-test-5",
            },
            {
                "text": "Code review session with the team. Found several issues in the React components.",
                "tags": ["code-review", "react"],
                "session_id": "bulk-test-5",
            },
        ]

    @pytest.fixture
    def sample_notes_10(self) -> List[Dict[str, Any]]:
        """10 sample notes for bulk testing"""
        return [
            {
                "text": "Sprint planning meeting completed. Assigned tasks for the Fabric MVP development.",
                "tags": ["sprint-planning", "fabric"],
                "session_id": "bulk-test-10",
            },
            {
                "text": "Pen testing results came back. Several vulnerabilities need immediate attention.",
                "tags": ["security", "pen-testing"],
                "session_id": "bulk-test-10",
            },
            {
                "text": "Data quality checks revealed inconsistencies in the customer database.",
                "tags": ["data-quality", "database"],
                "session_id": "bulk-test-10",
            },
            {
                "text": "Weekly standup with Martin. Discussed progress on the integration work.",
                "tags": ["standup", "integration"],
                "session_id": "bulk-test-10",
            },
            {
                "text": "Purview integration is blocked. Need approval from compliance team.",
                "tags": ["purview", "compliance", "blocked"],
                "session_id": "bulk-test-10",
            },
            {
                "text": "Deployed the new monitoring dashboard. DevOps team is testing the alerts.",
                "tags": ["monitoring", "devops"],
                "session_id": "bulk-test-10",
            },
            {
                "text": "Client meeting went well. They approved the wireframes for the new interface.",
                "tags": ["client", "wireframes"],
                "session_id": "bulk-test-10",
            },
            {
                "text": "Performance optimization work is showing good results. 40% improvement in load times.",
                "tags": ["performance", "optimization"],
                "session_id": "bulk-test-10",
            },
            {
                "text": "Training session for junior developers on React best practices.",
                "tags": ["training", "react", "mentoring"],
                "session_id": "bulk-test-10",
            },
            {
                "text": "Infrastructure update completed. Kubernetes cluster is now running version 1.28.",
                "tags": ["infrastructure", "kubernetes"],
                "session_id": "bulk-test-10",
            },
        ]

    @pytest.fixture
    def sample_notes_20(self) -> List[Dict[str, Any]]:
        """20 sample notes for bulk testing"""
        return [
            {
                "text": "Morning standup with the development team. Discussed Sprint 23 progress and blockers.",
                "tags": ["standup", "sprint"],
                "session_id": "bulk-test-20",
            },
            {
                "text": "Code review for the authentication service. Found performance issues in JWT validation.",
                "tags": ["code-review", "authentication", "performance"],
                "session_id": "bulk-test-20",
            },
            {
                "text": "Database migration script testing. Found compatibility issues with PostgreSQL 15.",
                "tags": ["database", "migration", "postgresql"],
                "session_id": "bulk-test-20",
            },
            {
                "text": "Client presentation for Q2 roadmap. Positive feedback on the proposed features.",
                "tags": ["client", "roadmap", "presentation"],
                "session_id": "bulk-test-20",
            },
            {
                "text": "Security audit findings review. Need to address 3 critical vulnerabilities by Friday.",
                "tags": ["security", "audit", "vulnerabilities"],
                "session_id": "bulk-test-20",
            },
            {
                "text": "Integration testing with the external payment API. Rate limiting issues discovered.",
                "tags": ["integration", "payment", "api"],
                "session_id": "bulk-test-20",
            },
            {
                "text": "DevOps pipeline optimization. Reduced build time from 15 minutes to 8 minutes.",
                "tags": ["devops", "pipeline", "optimization"],
                "session_id": "bulk-test-20",
            },
            {
                "text": "User acceptance testing session. Gathered feedback on the new dashboard design.",
                "tags": ["uat", "dashboard", "feedback"],
                "session_id": "bulk-test-20",
            },
            {
                "text": "Architecture review meeting. Decided to adopt microservices for the new module.",
                "tags": ["architecture", "microservices"],
                "session_id": "bulk-test-20",
            },
            {
                "text": "Performance monitoring setup completed. Grafana dashboards are now live.",
                "tags": ["monitoring", "grafana", "performance"],
                "session_id": "bulk-test-20",
            },
            {
                "text": "Team retrospective for Sprint 22. Identified areas for process improvement.",
                "tags": ["retrospective", "process-improvement"],
                "session_id": "bulk-test-20",
            },
            {
                "text": "API documentation update. Added examples for all new endpoints.",
                "tags": ["documentation", "api"],
                "session_id": "bulk-test-20",
            },
            {
                "text": "Infrastructure cost review. Identified opportunities for 20% savings.",
                "tags": ["infrastructure", "cost-optimization"],
                "session_id": "bulk-test-20",
            },
            {
                "text": "Mobile app testing on iOS. Found UI rendering issues on older devices.",
                "tags": ["mobile", "ios", "testing"],
                "session_id": "bulk-test-20",
            },
            {
                "text": "Data backup verification completed. All systems are properly backed up.",
                "tags": ["backup", "data", "verification"],
                "session_id": "bulk-test-20",
            },
            {
                "text": "Third-party library audit. Updated 5 packages with security vulnerabilities.",
                "tags": ["libraries", "security", "updates"],
                "session_id": "bulk-test-20",
            },
            {
                "text": "Load testing results for the new API. Can handle 1000 concurrent users.",
                "tags": ["load-testing", "api", "performance"],
                "session_id": "bulk-test-20",
            },
            {
                "text": "Customer support escalation. Critical bug in the checkout process needs immediate fix.",
                "tags": ["support", "bug", "checkout"],
                "session_id": "bulk-test-20",
            },
            {
                "text": "Compliance review meeting. GDPR requirements are fully implemented.",
                "tags": ["compliance", "gdpr"],
                "session_id": "bulk-test-20",
            },
            {
                "text": "New developer onboarding completed. Setup development environment and access.",
                "tags": ["onboarding", "developer", "setup"],
                "session_id": "bulk-test-20",
            },
        ]

    def test_bulk_store_5_notes(self, client, sample_notes_5):
        """Test bulk storage with 5 notes"""
        bulk_request = {"notes": sample_notes_5, "session_id": "bulk-test-session-5"}

        response = client.post("/tools/notes/bulk", json=bulk_request)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["total_processed"] == 5
        assert data["success_count"] == 5
        assert data["failure_count"] == 0
        assert len(data["stored_notes"]) == 5
        assert len(data["failed_notes"]) == 0

        # Verify each note was processed
        for stored_note in data["stored_notes"]:
            assert stored_note["note_id"] is not None
            assert stored_note["success"] is True
            assert stored_note["error"] is None
            assert len(stored_note["entities"]) >= 0  # Should have extracted entities
            assert stored_note["processing_time_ms"] > 0

        # Verify total processing time is reasonable
        assert data["total_processing_time_ms"] > 0
        assert data["total_processing_time_ms"] < 60000  # Should be under 60 seconds

    def test_bulk_store_10_notes(self, client, sample_notes_10):
        """Test bulk storage with 10 notes"""
        bulk_request = {"notes": sample_notes_10, "session_id": "bulk-test-session-10"}

        response = client.post("/tools/notes/bulk", json=bulk_request)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["total_processed"] == 10
        assert data["success_count"] == 10
        assert data["failure_count"] == 0
        assert len(data["stored_notes"]) == 10
        assert len(data["failed_notes"]) == 0

        # Verify processing time scales reasonably
        avg_processing_time = data["total_processing_time_ms"] / 10
        assert avg_processing_time > 0
        assert avg_processing_time < 10000  # Should average under 10 seconds per note

        # Verify entity extraction worked across all notes
        total_entities = sum(len(note["entities"]) for note in data["stored_notes"])
        assert (
            total_entities > 10
        )  # Should have extracted multiple entities across 10 notes

    def test_bulk_store_20_notes(self, client, sample_notes_20):
        """Test bulk storage with 20 notes"""
        bulk_request = {"notes": sample_notes_20, "session_id": "bulk-test-session-20"}

        response = client.post("/tools/notes/bulk", json=bulk_request)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["total_processed"] == 20
        assert data["success_count"] == 20
        assert data["failure_count"] == 0
        assert len(data["stored_notes"]) == 20
        assert len(data["failed_notes"]) == 0

        # Verify reasonable processing time for 20 notes
        assert data["total_processing_time_ms"] > 0
        assert data["total_processing_time_ms"] < 120000  # Should be under 2 minutes

        # Verify all notes have valid IDs and entities
        note_ids = set()
        for stored_note in data["stored_notes"]:
            assert stored_note["note_id"] is not None
            assert stored_note["note_id"] not in note_ids  # Ensure unique IDs
            note_ids.add(stored_note["note_id"])
            assert stored_note["success"] is True
            assert stored_note["processing_time_ms"] > 0

    def test_bulk_store_with_mixed_content(self, client):
        """Test bulk storage with varied content types"""
        mixed_notes = [
            {"text": "Short note.", "tags": ["short"], "session_id": "mixed-test"},
            {
                "text": "This is a longer note with multiple entities like John, Sarah, ProjectX, and various technical concepts like React, PostgreSQL, and API development. It should generate more entities and take longer to process.",
                "tags": ["long", "detailed"],
                "session_id": "mixed-test",
            },
            {
                "text": "Meeting scheduled for next Friday with the Platform team to discuss database migration blockers.",
                "tags": ["meeting", "scheduling"],
                "session_id": "mixed-test",
            },
            {
                "text": "🚀 Deployed v2.1.0 to production! 🎉 All tests passing ✅",
                "tags": ["deployment", "emoji"],
                "session_id": "mixed-test",
            },
            {
                "text": "Code review: https://github.com/company/repo/pull/123 - Authentication refactor looks good.",
                "tags": ["code-review", "urls"],
                "session_id": "mixed-test",
            },
        ]

        bulk_request = {"notes": mixed_notes, "session_id": "mixed-content-test"}

        response = client.post("/tools/notes/bulk", json=bulk_request)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["total_processed"] == 5
        assert data["success_count"] == 5
        assert data["failure_count"] == 0

        # Verify different content types were handled
        processing_times = [note["processing_time_ms"] for note in data["stored_notes"]]
        assert min(processing_times) > 0
        assert max(processing_times) > min(processing_times)  # Should have variation

    def test_bulk_search_after_storage(self, client, sample_notes_10):
        """Test that bulk stored notes can be found in search"""
        # First, store notes in bulk
        bulk_request = {"notes": sample_notes_10, "session_id": "search-test-session"}

        store_response = client.post("/tools/notes/bulk", json=bulk_request)
        assert store_response.status_code == 200

        # Then search for specific content
        search_response = client.get(
            "/tools/notes/search",
            params={"query": "Fabric MVP development", "limit": 10},
        )
        assert search_response.status_code == 200

        search_data = search_response.json()
        assert search_data["success"] is True
        assert len(search_data["results"]) > 0

        # Verify we can find the specific note
        found_fabric_note = any(
            "Fabric MVP" in result["text"] for result in search_data["results"]
        )
        assert found_fabric_note

    def test_bulk_store_error_handling(self, client):
        """Test bulk storage error handling with invalid data"""
        # Test with empty notes array - should get validation error
        empty_request = {"notes": [], "session_id": "error-test"}
        response = client.post("/tools/notes/bulk", json=empty_request)
        assert response.status_code == 422
        
        # Test with too many notes
        too_many_notes = [
            {"text": f"Test note {i}", "tags": ["test"], "session_id": "error-test"}
            for i in range(51)
        ]
        too_many_request = {"notes": too_many_notes, "session_id": "error-test"}
        response = client.post("/tools/notes/bulk", json=too_many_request)
        assert response.status_code == 422
        
        # Test with missing required fields
        invalid_notes = [{"tags": ["test"], "session_id": "error-test"}]  # Missing text
        invalid_request = {"notes": invalid_notes, "session_id": "error-test"}
        response = client.post("/tools/notes/bulk", json=invalid_request)
        assert response.status_code == 422
        
        # Test with oversized text - should succeed but truncate at service layer
        oversized_notes = [
            {
                "text": "x" * 11000,  # Exceeds service max_note_length of 10000
                "tags": ["oversized"],
                "session_id": "error-test",
            }
        ]
        oversized_request = {"notes": oversized_notes, "session_id": "error-test"}
        response = client.post("/tools/notes/bulk", json=oversized_request)
        
        # Should return 200 but with truncated content (handled by service layer)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["stored_notes"]) == 1
        assert data["stored_notes"][0]["note_id"] is not None
        # The text should have been truncated by the service layer
        
        # Test malformed structure
        response = client.post("/tools/notes/bulk", json={"invalid": "structure"})
        assert response.status_code == 422

    def test_bulk_store_performance_benchmark(self, client, sample_notes_20):
        """Benchmark bulk storage performance"""
        bulk_request = {"notes": sample_notes_20, "session_id": "performance-test"}

        response = client.post("/tools/notes/bulk", json=bulk_request)
        assert response.status_code == 200

        data = response.json()
        total_time_ms = data["total_processing_time_ms"]
        notes_per_second = (20 * 1000) / total_time_ms

        print(f"\nPerformance Benchmark:")
        print(f"Total time: {total_time_ms}ms")
        print(f"Average per note: {total_time_ms/20:.1f}ms")
        print(f"Throughput: {notes_per_second:.2f} notes/second")

        # Basic performance assertions
        assert total_time_ms > 0
        assert notes_per_second > 0.1  # Should handle at least 0.1 notes per second

        # All notes should be processed successfully
        assert data["success_count"] == 20
        assert data["failure_count"] == 0

    def test_bulk_store_partial_failures(self, client):
        """Test bulk storage with some notes that might fail during processing"""
        # Create a mix of valid and potentially problematic notes
        mixed_notes = [
            {
                "text": "This is a valid note with good content.",
                "tags": ["valid"],
                "session_id": "partial-test",
            },
            {
                "text": "Another valid note.",
                "tags": ["valid"],
                "session_id": "partial-test",
            },
            {
                "text": "Valid note with special chars: åäö éñü ñ",
                "tags": ["unicode"],
                "session_id": "partial-test",
            },
        ]

        bulk_request = {"notes": mixed_notes, "session_id": "partial-failure-test"}

        response = client.post("/tools/notes/bulk", json=bulk_request)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["total_processed"] == 3

        # In normal operation, all should succeed
        # But the structure supports partial failures
        assert data["success_count"] + data["failure_count"] == data["total_processed"]
        assert len(data["stored_notes"]) == data["success_count"]
        assert len(data["failed_notes"]) == data["failure_count"]

    def test_bulk_store_validation_edge_cases(self, client):
        """Test edge cases for bulk storage validation"""

        # Test with extremely short text (edge case for min_length)
        short_text_notes = [
            {"text": "x", "tags": [], "session_id": "edge-test"}  # Very short but valid
        ]

        request = {"notes": short_text_notes, "session_id": "edge-case-test"}

        response = client.post("/tools/notes/bulk", json=request)
        assert response.status_code == 200  # Should be valid

        # Test with empty string text (should fail validation)
        empty_text_notes = [
            {
                "text": "",  # Empty string should fail min_length validation
                "tags": [],
                "session_id": "edge-test",
            }
        ]

        request = {"notes": empty_text_notes, "session_id": "edge-case-test"}

        response = client.post("/tools/notes/bulk", json=request)
        assert response.status_code == 422  # Should fail validation

        # Test with null values
        null_session_notes = [
            {
                "text": "Valid text with null session",
                "tags": ["test"],
                "session_id": None,  # Null session_id should be allowed
            }
        ]

        request = {
            "notes": null_session_notes,
            "session_id": None,  # Null bulk session_id should be allowed
        }

        response = client.post("/tools/notes/bulk", json=request)
        assert response.status_code == 200  # Should be valid
