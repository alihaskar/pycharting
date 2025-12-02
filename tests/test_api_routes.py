"""Tests for API chart data endpoint routing."""
import pytest
from fastapi.testclient import TestClient
from charting.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_chart_data_endpoint_exists(client):
    """Test that /chart-data endpoint exists."""
    response = client.get("/chart-data")
    
    # Should return error (missing required params) but endpoint exists
    assert response.status_code in [400, 422]  # Bad request or validation error


def test_chart_data_requires_filename(client):
    """Test that filename parameter is required."""
    response = client.get("/chart-data")
    
    assert response.status_code == 422
    assert "filename" in response.text.lower()


def test_chart_data_accepts_filename(client):
    """Test that endpoint accepts filename parameter."""
    response = client.get("/chart-data?filename=test.csv")
    
    # May fail for other reasons (file not found) but should accept parameter
    assert response.status_code in [200, 404, 500]


def test_chart_data_optional_indicators(client):
    """Test that indicators parameter is optional."""
    response = client.get("/chart-data?filename=test.csv")
    
    # Should not fail due to missing indicators
    assert "indicators" not in response.json().get("detail", "")


def test_chart_data_accepts_multiple_indicators(client):
    """Test that endpoint accepts multiple indicators."""
    params = {
        "filename": "test.csv",
        "indicators": ["RSI", "SMA"]
    }
    response = client.get("/chart-data", params=params)
    
    # Should accept parameter format
    assert response.status_code in [200, 404, 500]


def test_chart_data_indicator_parameters(client):
    """Test that indicator parameters can be passed."""
    params = {
        "filename": "test.csv",
        "indicators": ["RSI:14", "SMA:20"]
    }
    response = client.get("/chart-data", params=params)
    
    # Should accept parameter format
    assert response.status_code in [200, 404, 500]


def test_chart_data_time_range_params(client):
    """Test that time range parameters work."""
    params = {
        "filename": "test.csv",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
    response = client.get("/chart-data", params=params)
    
    # Should accept time range
    assert response.status_code in [200, 404, 500]


def test_chart_data_timeframe_param(client):
    """Test that timeframe parameter works."""
    params = {
        "filename": "test.csv",
        "timeframe": "1h"
    }
    response = client.get("/chart-data", params=params)
    
    # Should accept timeframe
    assert response.status_code in [200, 404, 500]


def test_chart_data_response_structure(client, tmp_path):
    """Test that successful response has correct structure."""
    # This test will need actual file handling (covered in integration)
    # For now, just verify endpoint structure
    response = client.get("/chart-data?filename=test.csv")
    
    # Should return JSON
    assert response.headers["content-type"] == "application/json"


def test_chart_data_invalid_timeframe(client):
    """Test that invalid timeframe is rejected."""
    params = {
        "filename": "test.csv",
        "timeframe": "invalid"
    }
    response = client.get("/chart-data", params=params)
    
    # Should reject invalid timeframe
    assert response.status_code in [400, 422]


def test_chart_data_returns_json(client):
    """Test that response is always JSON."""
    response = client.get("/chart-data?filename=test.csv")
    
    # Should always return JSON
    assert "application/json" in response.headers["content-type"]


def test_chart_data_get_method_only(client):
    """Test that only GET method is allowed."""
    response = client.post("/chart-data", json={"filename": "test.csv"})
    
    # Should not allow POST
    assert response.status_code == 405


def test_chart_data_cors_headers(client):
    """Test that CORS headers are present."""
    response = client.get(
        "/chart-data?filename=test.csv",
        headers={"Origin": "http://localhost:3000"}
    )
    
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers

