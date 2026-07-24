"""Tests for server lifecycle management.

Behaviour tests use the ``fake_uvicorn`` fixture (see ``conftest.py``) so the
ChartServer thread/lifecycle machinery is exercised without binding a real
socket, and ``wait_until`` polling replaces fixed sleeps. Only the two explicit
integration tests at the bottom start a real HTTP server.
"""

import asyncio
import threading
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi import WebSocketDisconnect

from pycharting.core.lifecycle import ChartServer


def _heartbeat_endpoint(server):
    """Return the registered ``/ws/heartbeat`` websocket endpoint callable."""
    for route in server.app.routes:
        if getattr(route, "path", None) == "/ws/heartbeat":
            return route.endpoint
    return pytest.fail("heartbeat route not registered")


class _ScriptedWebSocket:
    """Minimal fake WebSocket that replays scripted messages then raises.

    ``receive_text`` yields each queued message in turn; once exhausted it raises
    ``final_exc``. This drives the heartbeat handler through its ping/pong,
    disconnect, and generic-error paths without a real connection.
    """

    def __init__(self, incoming, final_exc):
        self._incoming = list(incoming)
        self._final_exc = final_exc
        self.sent: list[str] = []
        self.accepted = False

    async def accept(self):
        """Record that the connection was accepted."""
        self.accepted = True

    async def receive_text(self):
        """Return the next scripted message, or raise the terminal exception."""
        if self._incoming:
            return self._incoming.pop(0)
        raise self._final_exc

    async def send_text(self, message):
        """Record an outbound message."""
        self.sent.append(message)


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

    def test_start_server(self, fake_uvicorn):
        """Test starting the server."""
        server = ChartServer()

        try:
            info = server.start_server()

            assert server.is_running
            assert "url" in info
            assert "ws_url" in info
            assert info["running"]
            assert info["port"] == server.port
        finally:
            server.stop_server()

    def test_stop_server(self, fake_uvicorn):
        """Test stopping the server."""
        server = ChartServer()

        server.start_server()
        assert server.is_running

        server.stop_server()
        assert not server.is_running

    def test_cannot_start_twice(self, fake_uvicorn):
        """Test that server cannot be started twice."""
        server = ChartServer()

        try:
            server.start_server()

            with pytest.raises(RuntimeError, match="already running"):
                server.start_server()
        finally:
            server.stop_server()

    def test_stop_when_not_running(self):
        """Test stopping server when it's not running (should not error)."""
        server = ChartServer()
        # Should not raise an error
        server.stop_server()

    def test_server_info(self, fake_uvicorn):
        """Test server_info property."""
        server = ChartServer()

        info = server.server_info
        assert "host" in info
        assert "port" in info
        assert "running" in info
        assert not info["running"]

        try:
            server.start_server()

            info = server.server_info
            assert info["running"]
            assert "websocket_connected" in info
            assert "last_heartbeat" in info
        finally:
            server.stop_server()

    def test_context_manager(self, fake_uvicorn):
        """Test using ChartServer as context manager."""
        with ChartServer() as server:
            assert server.is_running

        # Server should be stopped after context exit
        assert not server.is_running

    def test_repr(self):
        """Test string representation."""
        server = ChartServer(host="127.0.0.1", port=8888)
        repr_str = repr(server)

        assert "ChartServer" in repr_str
        assert "127.0.0.1" in repr_str
        assert "8888" in repr_str
        assert "stopped" in repr_str

    def test_background_thread_created(self, fake_uvicorn, wait_until):
        """Test that server runs in background thread."""
        server = ChartServer()

        # Get initial thread count
        initial_threads = threading.active_count()

        try:
            server.start_server()

            # Should have additional threads
            wait_until(lambda: threading.active_count() > initial_threads)
        finally:
            server.stop_server()

    def test_auto_shutdown_timeout_configured(self):
        """Test that auto_shutdown_timeout is configurable."""
        server = ChartServer(auto_shutdown_timeout=10.0)
        assert server.auto_shutdown_timeout == 10.0

    def test_websocket_endpoint_added(self):
        """Test that WebSocket endpoint is added to app."""
        server = ChartServer()

        # Check that the WebSocket route exists. Newer FastAPI/Starlette mix
        # route objects that lack a ``.path`` attribute (e.g. ``_IncludedRouter``)
        # into ``app.routes``, so read paths defensively.
        routes = [path for route in server.app.routes if (path := getattr(route, "path", None))]
        assert "/ws/heartbeat" in routes

    def test_websocket_heartbeat_ping_pong_and_disconnect(self):
        """Heartbeat endpoint replies ``pong`` to ``ping`` and resets on disconnect.

        Exercises accept, the ping/pong branch, a non-ping message (no reply), and
        the ``WebSocketDisconnect`` cleanup path — previously ``# pragma: no cover``.
        """
        server = ChartServer()
        endpoint = _heartbeat_endpoint(server)

        ws = _ScriptedWebSocket(["ping", "not-a-ping"], WebSocketDisconnect())
        asyncio.run(endpoint(ws))

        assert ws.accepted
        assert ws.sent == ["pong"]  # only "ping" is answered
        assert server._websocket_connected is False
        assert server._last_heartbeat is not None

    def test_websocket_heartbeat_generic_error_resets_state(self):
        """A non-disconnect error in the heartbeat loop resets the connection flag."""
        server = ChartServer()
        endpoint = _heartbeat_endpoint(server)

        ws = _ScriptedWebSocket([], RuntimeError("kaboom"))
        asyncio.run(endpoint(ws))

        assert server._websocket_connected is False

    def test_monitor_connection_stale_heartbeat_triggers_shutdown(self):
        """A stale heartbeat (elapsed > timeout) triggers auto-shutdown."""
        server = ChartServer(auto_shutdown_timeout=0.1)
        server._running = True
        server._websocket_connected = True
        server._last_heartbeat = datetime.now() - timedelta(seconds=5)

        with patch("pycharting.core.lifecycle.time.sleep"), patch.object(server, "stop_server") as stop:
            server._monitor_connection()

        stop.assert_called_once()
        assert server._websocket_connected is False

    def test_monitor_connection_client_disconnect_triggers_shutdown(self):
        """A disconnected client (no reconnect) triggers auto-shutdown after the wait."""
        server = ChartServer(auto_shutdown_timeout=0.1)
        server._running = True
        server._websocket_connected = False
        server._last_heartbeat = datetime.now()

        with patch("pycharting.core.lifecycle.time.sleep"), patch.object(server, "stop_server") as stop:
            server._monitor_connection()

        stop.assert_called_once()

    def test_run_server_handles_exception(self):
        """``_run_server`` swallows a server crash and clears the running flag."""
        server = ChartServer()
        server._running = True

        with patch("pycharting.core.lifecycle.uvicorn.Server") as mock_server_cls:
            mock_server_cls.return_value.run.side_effect = RuntimeError("server boom")
            server._run_server()  # must not raise

        assert server._running is False


def test_multiple_operations(fake_uvicorn):
    """Test multiple start/stop operations."""
    server = ChartServer()

    for _i in range(3):
        server.start_server()
        assert server.is_running

        server.stop_server()
        assert not server.is_running


def test_server_cleanup(fake_uvicorn, wait_until):
    """Test that server properly cleans up resources."""
    server = ChartServer()

    server.start_server()

    # Get thread references
    server_thread = server._server_thread
    monitor_thread = server._monitor_thread

    server.stop_server()

    # Threads should be finished
    if server_thread:
        wait_until(lambda: not server_thread.is_alive())
    if monitor_thread:
        wait_until(lambda: not monitor_thread.is_alive())


def test_server_responds_after_start(wait_until):
    """Integration: a real server answers the health endpoint after starting."""
    import httpx

    server = ChartServer()

    def _healthy():
        try:
            response = httpx.get(f"http://{server.host}:{server.port}/health", timeout=1)
        except httpx.HTTPError:
            return None
        return response if response.status_code == 200 else None

    try:
        server.start_server()
        response = wait_until(_healthy, timeout=10)
        assert response.json()["status"] == "healthy"
    finally:
        server.stop_server()


def test_server_accessible_in_background(wait_until):
    """Integration: the main thread stays responsive while the server runs."""
    import httpx

    server = ChartServer()

    def _healthy():
        try:
            response = httpx.get(f"http://{server.host}:{server.port}/health", timeout=1)
        except httpx.HTTPError:
            return None
        return response if response.status_code == 200 else None

    try:
        server.start_server()
        wait_until(_healthy, timeout=10)

        # Main thread should not be blocked: multiple requests succeed.
        for _ in range(3):
            response = httpx.get(f"http://{server.host}:{server.port}/health", timeout=5)
            assert response.status_code == 200
    finally:
        server.stop_server()
