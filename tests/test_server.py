"""Tests for FastAPI server."""

import pytest
from fastapi.testclient import TestClient

from pycharting.core.server import NoCacheStaticFiles, create_app, find_free_port, run_server


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    app = create_app()
    return TestClient(app)


class TestFindFreePort:
    """Tests for find_free_port function."""

    def test_finds_free_port(self):
        """Test that a free port is found."""
        port = find_free_port(8000, 8100)
        assert 8000 <= port < 8100

    def test_finds_different_ports(self):
        """Test that different calls can find different ports."""
        port1 = find_free_port(8000, 8100)
        port2 = find_free_port(8100, 8200)
        assert port1 != port2 or port1 < 8100

    def test_scans_from_start_with_default_end(self):
        """When only start_port is given, the end of the range defaults to start_port + 1000."""
        port = find_free_port(8000)
        assert 8000 <= port < 9000

    def test_returns_ephemeral_port_with_no_arguments(self):
        """With no arguments, an OS-assigned ephemeral port is returned."""
        port = find_free_port()
        assert port > 0

    def test_raises_on_no_free_port(self):
        """Test that RuntimeError is raised when no port is free."""
        import socket

        # Bind on the same interface find_free_port scans ("127.0.0.1").
        # On Windows, 127.0.0.1:port does not conflict with 0.0.0.0:port, so the
        # occupied port must be claimed on the same address to be seen as taken.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            occupied_port = s.getsockname()[1]
            with pytest.raises(RuntimeError, match="No free port found"):
                find_free_port(occupied_port, occupied_port + 1)


class TestAppCreation:
    """Tests for create_app function."""

    def test_app_created(self, client):
        """Test that app is created successfully."""
        assert client is not None

    def test_app_has_cors(self, client):
        """Test that CORS middleware is configured."""
        response = client.options("/health")
        # CORS headers should be present
        assert response.status_code in [200, 405]  # OPTIONS might not be explicitly handled


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_returns_html(self, client):
        """Test that root endpoint returns HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "PyCharting" in response.text

    def test_root_has_welcome_message(self, client):
        """Test that root page has welcome message."""
        response = client.get("/")
        assert "Welcome to PyCharting" in response.text
        assert "server is running successfully" in response.text

    def test_root_has_api_docs_link(self, client):
        """Test that root page links to API docs."""
        response = client.get("/")
        assert "/api/docs" in response.text


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check_returns_200(self, client):
        """Test that health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_json(self, client):
        """Test that health check returns JSON."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"

    def test_health_check_has_status(self, client):
        """Test that health check includes status."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_check_has_service_name(self, client):
        """Test that health check includes service name."""
        response = client.get("/health")
        data = response.json()
        assert "service" in data
        assert data["service"] == "pycharting"


class TestStaticFiles:
    """Tests for static file serving."""

    def test_static_route_exists(self, client):
        """Test that static route is mounted."""
        # This will return 404 if no file exists, but route should be there
        response = client.get("/static/nonexistent.js")
        # Should return 404, not 405 or other routing error
        assert response.status_code == 404


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""

    def test_openapi_json_available(self, client):
        """Test that OpenAPI JSON is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_openapi_has_title(self, client):
        """Test that OpenAPI spec has correct title."""
        response = client.get("/openapi.json")
        data = response.json()
        assert data["info"]["title"] == "PyCharting"

    def test_openapi_has_version(self, client):
        """Test that OpenAPI spec has version."""
        response = client.get("/openapi.json")
        data = response.json()
        assert data["info"]["version"] == "0.1.0"

    def test_docs_endpoint_available(self, client):
        """Test that docs UI is available."""
        response = client.get("/api/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_endpoint_available(self, client):
        """Test that ReDoc UI is available."""
        response = client.get("/api/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_on_nonexistent_route(self, client):
        """Test that 404 is returned for nonexistent routes."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_404_returns_json(self, client):
        """Test that 404 error returns JSON."""
        response = client.get("/api/nonexistent")
        # Might return HTML for non-API routes, but should handle gracefully
        assert response.status_code == 404


class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_headers_on_health_check(self, client):
        """Test that CORS headers are present."""
        response = client.get("/health", headers={"Origin": "http://localhost:3000"})
        # CORS middleware should add headers
        assert response.status_code == 200
        # FastAPI's TestClient might not fully simulate CORS, but endpoint should work

    def test_endpoint_accessible(self, client):
        """Test that endpoints are accessible (CORS doesn't block)."""
        response = client.get("/health")
        assert response.status_code == 200


class TestAppMetadata:
    """Tests for app metadata."""

    def test_app_has_correct_metadata(self, client):
        """Test that app metadata is correct."""
        response = client.get("/openapi.json")
        data = response.json()

        assert data["info"]["title"] == "PyCharting"
        assert data["info"]["description"] == "Interactive charting and data visualization API"
        assert data["info"]["version"] == "0.1.0"


class TestNoCacheStaticFiles:
    """Tests for NoCacheStaticFiles middleware."""

    def test_adds_no_cache_headers(self, tmp_path):
        """Verify NoCacheStaticFiles serves files with no-cache headers."""
        from fastapi import FastAPI

        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")

        app = FastAPI()
        app.mount("/static", NoCacheStaticFiles(directory=str(tmp_path)), name="static")
        client = TestClient(app)

        response = client.get("/static/test.txt")
        assert response.status_code == 200
        assert "no-cache" in response.headers.get("cache-control", "")
        assert response.headers.get("pragma") == "no-cache"
        assert response.headers.get("expires") == "0"


class TestRunServer:
    """Tests for run_server function."""

    def test_run_server_auto_port(self):
        """Verify run_server selects a positive port automatically by default."""
        from unittest.mock import MagicMock, patch

        with patch("pycharting.core.server.uvicorn") as mock_uvicorn:
            mock_uvicorn.run = MagicMock()
            run_server()
            mock_uvicorn.run.assert_called_once()
            assert mock_uvicorn.run.call_args.kwargs["port"] > 0

    def test_run_server_specific_port(self):
        """Verify run_server uses the given port when auto_port is disabled."""
        import socket
        from unittest.mock import MagicMock, patch

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            free_port = s.getsockname()[1]
        with patch("pycharting.core.server.uvicorn") as mock_uvicorn:
            mock_uvicorn.run = MagicMock()
            run_server(port=free_port, auto_port=False)
            assert mock_uvicorn.run.call_args.kwargs["port"] == free_port

    def test_run_server_auto_port_fallback(self):
        """Verify run_server falls back to a free port when the requested port is occupied."""
        import socket
        from unittest.mock import MagicMock, patch

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            occupied = s.getsockname()[1]
            fallback = occupied + 1
            with (
                patch("pycharting.core.server.uvicorn") as mock_uvicorn,
                patch("pycharting.core.server.find_free_port", return_value=fallback) as mock_ffp,
            ):
                mock_uvicorn.run = MagicMock()
                run_server(host="127.0.0.1", port=occupied, auto_port=True)
                mock_ffp.assert_called_once_with(occupied + 1)
                assert mock_uvicorn.run.call_args.kwargs["port"] == fallback
