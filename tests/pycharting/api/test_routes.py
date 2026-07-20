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


def test_api_status(client):
    """Test API status endpoint."""
    response = client.get("/api/status")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "active_sessions" in data
    assert "endpoints" in data


def test_init_default_session(client):
    """Test initializing default session."""
    response = client.post("/api/data/init")
    assert response.status_code == 200

    data = response.json()
    assert data["session_id"] == "default"
    assert data["status"] == "initialized"
    assert data["data_points"] == 1000


def test_init_custom_session(client):
    """Test initializing custom session."""
    response = client.post("/api/data/init?session_id=test")
    assert response.status_code == 200

    data = response.json()
    assert data["session_id"] == "test"
    assert data["status"] == "initialized"


def test_get_data_without_session(client):
    """Test getting data without initializing session."""
    response = client.get("/api/data")
    assert response.status_code == 404
    response_json = response.json()
    # Check for error message in either 'detail' or 'error' key
    error_msg = response_json.get("detail") or response_json.get("error", "")
    assert "not found" in error_msg.lower()


def test_get_data_with_session(client):
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


def test_get_data_full_range(client):
    """Test getting all data."""
    client.post("/api/data/init")

    response = client.get("/api/data")
    assert response.status_code == 200

    data = response.json()
    assert data["total_length"] == 1000
    assert len(data["index"]) == 1000


def test_get_data_partial_range(client):
    """Test getting partial data range."""
    client.post("/api/data/init")

    response = client.get("/api/data?start_index=500&end_index=600")
    assert response.status_code == 200

    data = response.json()
    assert data["start_index"] == 500
    assert data["end_index"] == 600
    assert len(data["index"]) == 100


def test_get_data_with_custom_session(client):
    """Test getting data from custom session."""
    client.post("/api/data/init?session_id=custom")

    response = client.get("/api/data?session_id=custom&start_index=0&end_index=50")
    assert response.status_code == 200

    data = response.json()
    assert len(data["index"]) == 50


def test_list_sessions_empty(client):
    """Test listing sessions when none exist."""
    response = client.get("/api/sessions")
    assert response.status_code == 200

    data = response.json()
    assert data["count"] == 0
    assert len(data["sessions"]) == 0


def test_list_sessions_with_data(client):
    """Test listing sessions after initialization."""
    client.post("/api/data/init")
    client.post("/api/data/init?session_id=test")

    response = client.get("/api/sessions")
    assert response.status_code == 200

    data = response.json()
    assert data["count"] == 2
    assert len(data["sessions"]) == 2


def test_delete_session(client):
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


def test_delete_nonexistent_session(client):
    """Test deleting non-existent session."""
    response = client.delete("/api/sessions/nonexistent")
    assert response.status_code == 404


def test_negative_start_index(client):
    """Test that negative start index is rejected."""
    client.post("/api/data/init")

    response = client.get("/api/data?start_index=-1")
    assert response.status_code == 422  # Validation error


def test_overlays_and_subplots(client):
    """Test that response includes overlay/subplot fields."""
    client.post("/api/data/init")

    response = client.get("/api/data?start_index=0&end_index=10")
    assert response.status_code == 200

    data = response.json()
    assert "overlays" in data
    assert "subplots" in data
    assert isinstance(data["overlays"], dict)
    assert isinstance(data["subplots"], dict)


def test_full_workflow(client):
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


def test_multiple_sessions(client):
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


def test_get_data_internal_error_returns_500(client):
    """Verify the data endpoint returns 500 when get_chunk raises an error."""
    from unittest.mock import MagicMock

    from pycharting.api.routes import _data_managers

    mock_dm = MagicMock()
    mock_dm.get_chunk.side_effect = RuntimeError("disk failure")
    _data_managers["err"] = mock_dm
    try:
        response = client.get("/api/data?session_id=err")
        assert response.status_code == 500
    finally:
        _data_managers.pop("err", None)


def test_initialize_data_internal_error_returns_500(client):
    """Verify the data init endpoint returns 500 when DataManager raises."""
    from unittest.mock import patch

    with patch("pycharting.api.routes.DataManager", side_effect=RuntimeError("boom")):
        response = client.post("/api/data/init?session_id=err2")
        assert response.status_code == 500


class TestDataResponse:
    """Tests for the DataResponse pydantic model."""

    def test_minimal_construction(self):
        """DataResponse builds from the required index/range fields."""
        from pycharting.api.routes import DataResponse

        resp = DataResponse(index=[0, 1, 2], start_index=0, end_index=2, total_length=3)
        assert resp.index == [0, 1, 2]
        assert resp.overlays == {}
        assert resp.subplots == {}
        assert resp.close is None


class TestErrorResponse:
    """Tests for the ErrorResponse pydantic model."""

    def test_construction_with_detail(self):
        """ErrorResponse carries an error message and optional detail."""
        from pycharting.api.routes import ErrorResponse

        err = ErrorResponse(error="boom", detail="stack")
        assert err.error == "boom"
        assert err.detail == "stack"

    def test_detail_defaults_to_none(self):
        """The detail field is optional."""
        from pycharting.api.routes import ErrorResponse

        assert ErrorResponse(error="boom").detail is None
