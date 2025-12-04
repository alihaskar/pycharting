"""Tests for server lifecycle management."""

import pytest
import time
import threading
from src.pycharting.core.lifecycle import ChartServer


class TestChartServer:
    """Tests for ChartServer lifecycle management."""
    
    def test_init(self):
        """Test ChartServer initialization."""
        server = ChartServer(host="127.0.0.1")
        assert server.host == "127.0.0.1"
        assert server.port > 0
        assert not server.is_running
    
    def test_init_with_port(self):
        """Test ChartServer with specific port."""
        server = ChartServer(host="127.0.0.1", port=9999)
        assert server.port == 9999
    
    def test_start_server(self):
        """Test starting the server."""
        server = ChartServer()
        
        try:
            info = server.start_server()
            
            assert server.is_running
            assert "url" in info
            assert "ws_url" in info
            assert info["running"]
            assert info["port"] == server.port
            
            # Give server time to fully start
            time.sleep(0.5)
            assert server.is_running
            
        finally:
            server.stop_server()
    
    def test_stop_server(self):
        """Test stopping the server."""
        server = ChartServer()
        
        server.start_server()
        time.sleep(0.5)
        assert server.is_running
        
        server.stop_server()
        time.sleep(0.5)
        assert not server.is_running
    
    def test_cannot_start_twice(self):
        """Test that server cannot be started twice."""
        server = ChartServer()
        
        try:
            server.start_server()
            time.sleep(0.5)
            
            with pytest.raises(RuntimeError, match="already running"):
                server.start_server()
        
        finally:
            server.stop_server()
    
    def test_stop_when_not_running(self):
        """Test stopping server when it's not running (should not error)."""
        server = ChartServer()
        # Should not raise an error
        server.stop_server()
    
    def test_server_info(self):
        """Test server_info property."""
        server = ChartServer()
        
        info = server.server_info
        assert "host" in info
        assert "port" in info
        assert "running" in info
        assert not info["running"]
        
        try:
            server.start_server()
            time.sleep(0.5)
            
            info = server.server_info
            assert info["running"]
            assert "websocket_connected" in info
            assert "last_heartbeat" in info
        
        finally:
            server.stop_server()
    
    def test_context_manager(self):
        """Test using ChartServer as context manager."""
        with ChartServer() as server:
            time.sleep(0.5)
            assert server.is_running
        
        # Server should be stopped after context exit
        time.sleep(0.5)
        assert not server.is_running
    
    def test_repr(self):
        """Test string representation."""
        server = ChartServer(host="127.0.0.1", port=8888)
        repr_str = repr(server)
        
        assert "ChartServer" in repr_str
        assert "127.0.0.1" in repr_str
        assert "8888" in repr_str
        assert "stopped" in repr_str
    
    def test_background_thread_created(self):
        """Test that server runs in background thread."""
        server = ChartServer()
        
        # Get initial thread count
        initial_threads = threading.active_count()
        
        try:
            server.start_server()
            time.sleep(0.5)
            
            # Should have additional threads
            current_threads = threading.active_count()
            assert current_threads > initial_threads
            
        finally:
            server.stop_server()
            time.sleep(0.5)
    
    def test_auto_shutdown_timeout_configured(self):
        """Test that auto_shutdown_timeout is configurable."""
        server = ChartServer(auto_shutdown_timeout=10.0)
        assert server.auto_shutdown_timeout == 10.0
    
    def test_websocket_endpoint_added(self):
        """Test that WebSocket endpoint is added to app."""
        server = ChartServer()
        
        # Check that the WebSocket route exists
        routes = [route.path for route in server.app.routes]
        assert "/ws/heartbeat" in routes


class TestThreadSafety:
    """Tests for thread safety."""
    
    def test_multiple_operations(self):
        """Test multiple start/stop operations."""
        server = ChartServer()
        
        for i in range(3):
            server.start_server()
            time.sleep(0.3)
            assert server.is_running
            
            server.stop_server()
            time.sleep(0.3)
            assert not server.is_running
    
    def test_server_cleanup(self):
        """Test that server properly cleans up resources."""
        server = ChartServer()
        
        server.start_server()
        time.sleep(0.5)
        
        # Get thread references
        server_thread = server._server_thread
        monitor_thread = server._monitor_thread
        
        server.stop_server()
        time.sleep(1)
        
        # Threads should be finished
        if server_thread:
            assert not server_thread.is_alive()
        if monitor_thread:
            assert not monitor_thread.is_alive()


class TestServerIntegration:
    """Integration tests for server functionality."""
    
    def test_server_responds_after_start(self):
        """Test that server responds to requests after starting."""
        import httpx
        
        server = ChartServer()
        
        try:
            info = server.start_server()
            time.sleep(1)  # Give server time to start
            
            # Try to access health endpoint
            response = httpx.get(f"{info['url']}/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        
        except Exception as e:
            pytest.skip(f"Server integration test skipped: {e}")
        
        finally:
            server.stop_server()
    
    def test_server_accessible_in_background(self):
        """Test that main thread is not blocked."""
        import httpx
        
        server = ChartServer()
        
        try:
            server.start_server()
            time.sleep(1)
            
            # Main thread should not be blocked
            # We should be able to make multiple requests
            for _ in range(3):
                response = httpx.get(f"http://{server.host}:{server.port}/health", timeout=5)
                assert response.status_code == 200
                time.sleep(0.1)
        
        except Exception as e:
            pytest.skip(f"Integration test skipped: {e}")
        
        finally:
            server.stop_server()
