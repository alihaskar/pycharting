"""Tests for API routes."""

import pytest
from fastapi.testclient import TestClient
from pycharting.core.server import create_app


@pytest.fixture
def client():
    """Create test client."""
    # Clear session state before each test
    from pycharting.api.routes import _data_managers
    _data_managers.clear()
    
    app = create_app()
    return TestClient(app)


class TestAPIStatus:
    """Tests for API status endpoint."""
    
    def test_api_status(self, client):
        """Test API status endpoint."""
        response = client.get("/api/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "active_sessions" in data
        assert "endpoints" in data


class TestDataInitialization:
    """Tests for data initialization endpoint."""
    
    def test_init_default_session(self, client):
        """Test initializing default session."""
        response = client.post("/api/data/init")
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == "default"
        assert data["status"] == "initialized"
        assert data["data_points"] == 1000
    
    def test_init_custom_session(self, client):
        """Test initializing custom session."""
        response = client.post("/api/data/init?session_id=test")
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == "test"
        assert data["status"] == "initialized"


class TestDataFetching:
    """Tests for data fetching endpoint."""
    
    def test_get_data_without_session(self, client):
        """Test getting data without initializing session."""
        response = client.get("/api/data")
        assert response.status_code == 404
        response_json = response.json()
        # Check for error message in either 'detail' or 'error' key
        error_msg = response_json.get("detail") or response_json.get("error", "")
        assert "not found" in error_msg.lower()
    
    def test_get_data_with_session(self, client):
        """Test getting data after initialization."""
        # Initialize session
        client.post("/api/data/init")
        
        # Fetch data
        response = client.get("/api/data?start_index=0&end_index=100")
        assert response.status_code == 200
        
        data = response.json()
        assert "index" in data
        assert "open" in data
        assert "high" in data
        assert "low" in data
        assert "close" in data
        assert len(data["index"]) == 100
    
    def test_get_data_full_range(self, client):
        """Test getting all data."""
        client.post("/api/data/init")
        
        response = client.get("/api/data")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_length"] == 1000
        assert len(data["index"]) == 1000
    
    def test_get_data_partial_range(self, client):
        """Test getting partial data range."""
        client.post("/api/data/init")
        
        response = client.get("/api/data?start_index=500&end_index=600")
        assert response.status_code == 200
        
        data = response.json()
        assert data["start_index"] == 500
        assert data["end_index"] == 600
        assert len(data["index"]) == 100
    
    def test_get_data_with_custom_session(self, client):
        """Test getting data from custom session."""
        client.post("/api/data/init?session_id=custom")
        
        response = client.get("/api/data?session_id=custom&start_index=0&end_index=50")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["index"]) == 50


class TestSessionManagement:
    """Tests for session management endpoints."""
    
    def test_list_sessions_empty(self, client):
        """Test listing sessions when none exist."""
        response = client.get("/api/sessions")
        assert response.status_code == 200
        
        data = response.json()
        assert data["count"] == 0
        assert len(data["sessions"]) == 0
    
    def test_list_sessions_with_data(self, client):
        """Test listing sessions after initialization."""
        client.post("/api/data/init")
        client.post("/api/data/init?session_id=test")
        
        response = client.get("/api/sessions")
        assert response.status_code == 200
        
        data = response.json()
        assert data["count"] == 2
        assert len(data["sessions"]) == 2
    
    def test_delete_session(self, client):
        """Test deleting a session."""
        client.post("/api/data/init?session_id=to_delete")
        
        # Verify session exists
        response = client.get("/api/sessions")
        assert response.json()["count"] == 1
        
        # Delete session
        response = client.delete("/api/sessions/to_delete")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"
        
        # Verify session is gone
        response = client.get("/api/sessions")
        assert response.json()["count"] == 0
    
    def test_delete_nonexistent_session(self, client):
        """Test deleting non-existent session."""
        response = client.delete("/api/sessions/nonexistent")
        assert response.status_code == 404


class TestDataValidation:
    """Tests for data validation."""
    
    def test_negative_start_index(self, client):
        """Test that negative start index is rejected."""
        client.post("/api/data/init")
        
        response = client.get("/api/data?start_index=-1")
        assert response.status_code == 422  # Validation error
    
    def test_overlays_and_subplots(self, client):
        """Test that response includes overlay/subplot fields."""
        client.post("/api/data/init")
        
        response = client.get("/api/data?start_index=0&end_index=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "overlays" in data
        assert "subplots" in data
        assert isinstance(data["overlays"], dict)
        assert isinstance(data["subplots"], dict)


class TestAPIIntegration:
    """Integration tests for API."""
    
    def test_full_workflow(self, client):
        """Test complete workflow: init -> fetch -> delete."""
        # Initialize
        response = client.post("/api/data/init?session_id=workflow")
        assert response.status_code == 200
        
        # Fetch data
        response = client.get("/api/data?session_id=workflow&start_index=0&end_index=100")
        assert response.status_code == 200
        assert len(response.json()["index"]) == 100
        
        # List sessions
        response = client.get("/api/sessions")
        assert response.status_code == 200
        assert response.json()["count"] == 1
        
        # Delete session
        response = client.delete("/api/sessions/workflow")
        assert response.status_code == 200
        
        # Verify data is inaccessible
        response = client.get("/api/data?session_id=workflow")
        assert response.status_code == 404
    
    def test_multiple_sessions(self, client):
        """Test working with multiple sessions simultaneously."""
        # Create multiple sessions
        for i in range(3):
            response = client.post(f"/api/data/init?session_id=session{i}")
            assert response.status_code == 200
        
        # Fetch from each
        for i in range(3):
            response = client.get(f"/api/data?session_id=session{i}&start_index=0&end_index=10")
            assert response.status_code == 200
        
        # Verify all exist
        response = client.get("/api/sessions")
        assert response.json()["count"] == 3
