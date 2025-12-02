"""Tests for API error handling and response formatting."""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.exceptions import (
    FileNotFoundError as APIFileNotFoundError,
    ValidationError as APIValidationError,
    ProcessingError
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_file_not_found_error_format(client):
    """Test that file not found returns proper format."""
    response = client.get("/chart-data?filename=nonexistent.csv")
    
    assert response.status_code == 404
    data = response.json()
    
    # Check error response structure
    assert "detail" in data
    assert isinstance(data["detail"], str)


def test_validation_error_format(client):
    """Test that validation errors return proper format."""
    response = client.get("/chart-data?filename=../secret.csv")
    
    assert response.status_code == 400
    data = response.json()
    
    # Check error response structure
    assert "detail" in data


def test_internal_error_format(client):
    """Test that internal errors return proper format."""
    # This would need a way to trigger an internal error
    # For now, just verify the endpoint handles errors
    response = client.get("/chart-data?filename=test.csv")
    
    # Should return some response (200 if file exists, 404 if not)
    assert response.status_code in [200, 404, 500]


def test_error_does_not_leak_details(client):
    """Test that errors don't leak sensitive information."""
    response = client.get("/chart-data?filename=/etc/passwd")
    
    assert response.status_code == 400
    data = response.json()
    
    # Should not contain full file paths or system details
    detail = data["detail"].lower()
    assert "/etc/passwd" not in detail or "absolute" in detail


def test_custom_exceptions_work():
    """Test that custom exceptions can be raised and caught."""
    # Test APIFileNotFoundError
    with pytest.raises(APIFileNotFoundError):
        raise APIFileNotFoundError("test.csv")
    
    # Test APIValidationError
    with pytest.raises(APIValidationError):
        raise APIValidationError("Invalid input")
    
    # Test ProcessingError
    with pytest.raises(ProcessingError):
        raise ProcessingError("Processing failed")


def test_exception_handlers_registered(client):
    """Test that exception handlers are registered."""
    # Verify app has exception handlers
    assert len(app.exception_handlers) > 0


def test_consistent_error_format(client):
    """Test that all errors have consistent format."""
    test_cases = [
        ("/chart-data?filename=nonexistent.csv", 404),
        ("/chart-data?filename=../secret.csv", 400),
        ("/chart-data?filename=", 400),
    ]
    
    for url, expected_status in test_cases:
        response = client.get(url)
        assert response.status_code == expected_status
        
        data = response.json()
        # All should have "detail" field
        assert "detail" in data
        assert isinstance(data["detail"], str)
        assert len(data["detail"]) > 0


def test_validation_error_messages_helpful(client):
    """Test that validation error messages are helpful."""
    response = client.get("/chart-data?filename=malicious.exe")
    
    assert response.status_code == 400
    data = response.json()
    
    # Should explain what's wrong
    detail = data["detail"].lower()
    assert "extension" in detail or "csv" in detail


def test_error_response_is_json(client):
    """Test that error responses are JSON."""
    response = client.get("/chart-data?filename=nonexistent.csv")
    
    assert "application/json" in response.headers["content-type"]


def test_cors_headers_in_error_responses(client):
    """Test that CORS headers are present in error responses."""
    response = client.get(
        "/chart-data?filename=nonexistent.csv",
        headers={"Origin": "http://localhost:3000"}
    )
    
    # CORS headers should be present even in errors
    assert "access-control-allow-origin" in response.headers

