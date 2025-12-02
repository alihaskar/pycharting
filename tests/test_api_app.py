"""Tests for FastAPI application setup and configuration."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api.main import app, get_app


def test_app_instance():
    """Test that app is a FastAPI instance."""
    assert isinstance(app, FastAPI)


def test_app_title():
    """Test that app has the correct title."""
    assert app.title == "Financial Charting API"


def test_app_version():
    """Test that app has a version."""
    assert hasattr(app, "version")
    assert app.version is not None


def test_cors_middleware_configured():
    """Test that CORS middleware is configured."""
    # Check if CORSMiddleware is in the middleware stack
    middleware_types = [m.cls.__name__ for m in app.user_middleware]
    assert "CORSMiddleware" in middleware_types


def test_app_lifespan():
    """Test that app has lifespan configuration."""
    # Check lifespan is configured
    assert app.router.lifespan_context is not None


def test_root_endpoint_exists():
    """Test that root endpoint exists and returns info."""
    client = TestClient(app)
    response = client.get("/")
    
    assert response.status_code == 200
    assert "name" in response.json()
    assert "version" in response.json()


def test_health_check_endpoint():
    """Test that health check endpoint exists."""
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_cors_headers_present():
    """Test that CORS headers are present in responses."""
    client = TestClient(app)
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    
    # Check for CORS headers
    assert "access-control-allow-origin" in response.headers


def test_app_factory():
    """Test that get_app factory function works."""
    test_app = get_app()
    assert isinstance(test_app, FastAPI)


def test_error_handler_404():
    """Test that 404 errors are handled properly."""
    client = TestClient(app)
    response = client.get("/nonexistent")
    
    assert response.status_code == 404
    assert "detail" in response.json()


def test_openapi_docs_available():
    """Test that OpenAPI documentation is available."""
    client = TestClient(app)
    response = client.get("/docs")
    
    # Should redirect or return docs
    assert response.status_code in [200, 307]


def test_openapi_schema_available():
    """Test that OpenAPI schema is available."""
    client = TestClient(app)
    response = client.get("/openapi.json")
    
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema

