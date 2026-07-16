"""Tests for Python API interface."""

from unittest.mock import patch

import numpy as np
import pytest

from pycharting.api.interface import _repr_html_, get_server_status, plot, stop_server
from pycharting.api.routes import _data_managers


@pytest.fixture(autouse=True)
def cleanup_globals():
    """Clean up global state between tests.

    Operates on the live ``interface`` module global rather than a name
    imported into this module — a plain ``global _active_server`` here would
    rebind the test module's own copy and leave the running server (and the
    real ``interface._active_server``) untouched, leaking state between tests.
    """
    import pycharting.api.interface as iface

    def _reset() -> None:
        if iface._active_server and iface._active_server.is_running:
            iface._active_server.stop_server()
        iface._active_server = None
        _data_managers.clear()

    _reset()
    yield
    _reset()


class TestPlotFunction:
    """Tests for the main plot() function."""

    def test_plot_basic_usage(self):
        """Test basic plot creation with minimal arguments."""
        # Generate sample data
        n = 100
        index = np.arange(n)
        close = np.cumsum(np.random.randn(n)) + 100
        open_data = close + np.random.randn(n) * 0.5
        high = np.maximum(open_data, close) + np.abs(np.random.randn(n))
        low = np.minimum(open_data, close) - np.abs(np.random.randn(n))

        # Create chart without opening browser
        result = plot(index, open_data, high, low, close, open_browser=False, block=False)

        assert result["status"] == "success"
        assert "url" in result
        assert result["data_points"] == n
        assert result["server_running"] is True
        assert "default" in result["session_id"]

    def test_plot_with_custom_session(self):
        """Test plot with custom session ID."""
        n = 50
        index = np.arange(n)
        data = np.random.randn(n) + 100

        result = plot(
            index, data, data + 1, data - 1, data, session_id="custom_session", open_browser=False, block=False
        )

        assert result["status"] == "success"
        assert result["session_id"] == "custom_session"
        assert "custom_session" in _data_managers

    def test_plot_with_overlays(self):
        """Test plot with overlay data."""
        n = 100
        index = np.arange(n)
        close = np.cumsum(np.random.randn(n)) + 100
        open_data = close + np.random.randn(n) * 0.5
        high = np.maximum(open_data, close) + np.abs(np.random.randn(n))
        low = np.minimum(open_data, close) - np.abs(np.random.randn(n))

        # Add moving average overlay
        ma = np.convolve(close, np.ones(10) / 10, mode="same")

        result = plot(index, open_data, high, low, close, overlays={"MA10": ma}, open_browser=False, block=False)

        assert result["status"] == "success"
        # Check that data manager has overlay
        dm = _data_managers["default"]
        assert "MA10" in dm.overlays

    def test_plot_reuses_server(self):
        """Test that multiple plots reuse the same server."""
        n = 50
        data = np.random.randn(n) + 100
        index = np.arange(n)

        # First plot
        result1 = plot(index, data, data + 1, data - 1, data, session_id="session1", open_browser=False, block=False)

        first_server_url = result1["server_url"]

        # Second plot should reuse server
        result2 = plot(index, data, data + 1, data - 1, data, session_id="session2", open_browser=False, block=False)

        assert result2["server_url"] == first_server_url
        assert result1["status"] == "success"
        assert result2["status"] == "success"

    def test_plot_with_invalid_data(self):
        """Test plot with invalid data returns error."""
        # Try with mismatched array lengths
        result = plot(
            np.arange(10),
            np.random.randn(10),
            np.random.randn(10),
            np.random.randn(10),
            np.random.randn(5),  # Wrong length!
            open_browser=False,
            block=False,
        )

        assert result["status"] == "error"
        assert "error" in result

    @patch("webbrowser.open")
    def test_plot_opens_browser(self, mock_browser):
        """Test that plot opens browser when requested."""
        n = 50
        data = np.random.randn(n) + 100
        index = np.arange(n)

        result = plot(index, data, data + 1, data - 1, data, open_browser=True, block=False)

        assert result["status"] == "success"
        # Check that browser.open was called
        mock_browser.assert_called_once()
        call_args = mock_browser.call_args[0][0]
        assert "http://" in call_args

    @patch("webbrowser.open", side_effect=Exception("Browser error"))
    def test_plot_handles_browser_error(self, mock_browser):
        """Test that plot handles browser opening errors gracefully."""
        n = 50
        data = np.random.randn(n) + 100
        index = np.arange(n)

        # Should still succeed even if browser fails
        result = plot(index, data, data + 1, data - 1, data, open_browser=True, block=False)

        assert result["status"] == "success"
        assert result["server_running"] is True


class TestStopServer:
    """Tests for stop_server() function."""

    def test_stop_server_when_running(self):
        """Test stopping an active server."""
        # Start a server first
        n = 50
        data = np.random.randn(n) + 100
        index = np.arange(n)

        plot(index, data, data + 1, data - 1, data, open_browser=False, block=False)

        # Now stop it
        stop_server()

        status = get_server_status()
        assert status["running"] is False

    def test_stop_server_when_not_running(self, capsys):
        """Test stopping when no server is active reports the no-op message."""
        import pycharting.api.interface as iface

        # Force the module global to None so the "no active server" branch is
        # exercised deterministically, regardless of test execution order /
        # xdist worker state.
        original = iface._active_server
        iface._active_server = None
        try:
            stop_server()  # Should not raise; should emit the info message
            assert "No active server to stop" in capsys.readouterr().out
        finally:
            iface._active_server = original


class TestGetServerStatus:
    """Tests for get_server_status() function."""

    def test_status_when_no_server(self):
        """Test status when no server has been started."""
        status = get_server_status()

        assert status["running"] is False
        # server_info may exist from previous server, just check it's not running
        assert status["active_sessions"] == 0

    def test_status_when_server_running(self):
        """Test status when server is active."""
        n = 50
        data = np.random.randn(n) + 100
        index = np.arange(n)

        # Start server
        plot(index, data, data + 1, data - 1, data, open_browser=False, block=False)

        status = get_server_status()

        assert status["running"] is True
        assert status["server_info"] is not None
        assert status["active_sessions"] >= 1
        assert "host" in status["server_info"]
        assert "port" in status["server_info"]


class TestDataTypes:
    """Tests for different data type inputs."""

    def test_plot_with_numpy_arrays(self):
        """Test plot with NumPy arrays."""
        n = 50
        index = np.arange(n)
        close = np.random.randn(n) + 100

        result = plot(index, close, close + 1, close - 1, close, open_browser=False, block=False)

        assert result["status"] == "success"

    def test_plot_with_lists(self):
        """Test plot with Python lists."""
        n = 50
        index = list(range(n))
        close = [100 + i * 0.1 for i in range(n)]

        result = plot(
            index, close, [c + 1 for c in close], [c - 1 for c in close], close, open_browser=False, block=False
        )

        assert result["status"] == "success"


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_workflow(self):
        """Test complete workflow: plot -> check status -> stop."""
        # Generate data
        n = 100
        index = np.arange(n)
        close = np.cumsum(np.random.randn(n)) + 100
        open_data = close + np.random.randn(n) * 0.5
        high = np.maximum(open_data, close) + np.abs(np.random.randn(n))
        low = np.minimum(open_data, close) - np.abs(np.random.randn(n))

        # 1. Create chart
        result = plot(index, open_data, high, low, close, session_id="workflow_test", open_browser=False, block=False)
        assert result["status"] == "success"

        # 2. Check status
        status = get_server_status()
        assert status["running"] is True
        assert status["active_sessions"] >= 1

        # 3. Stop server
        stop_server()

        # 4. Verify stopped
        status = get_server_status()
        assert status["running"] is False

    def test_multiple_sessions(self):
        """Test creating multiple chart sessions."""
        n = 50
        data = np.random.randn(n) + 100
        index = np.arange(n)

        # Create multiple sessions
        for i in range(3):
            result = plot(
                index, data, data + 1, data - 1, data, session_id=f"session_{i}", open_browser=False, block=False
            )
            assert result["status"] == "success"

        # Check all sessions exist
        assert len(_data_managers) >= 3
        for i in range(3):
            assert f"session_{i}" in _data_managers


class TestReprHtml:
    """Tests for _repr_html_ Jupyter integration."""

    def test_repr_html_when_no_server(self):
        """Verify _repr_html_() reports a stopped state when no server is active."""
        import pycharting.api.interface as iface

        original = iface._active_server
        iface._active_server = None
        try:
            html = _repr_html_()
            assert "Stopped" in html
        finally:
            iface._active_server = original

    def test_repr_html_when_server_running(self):
        """Verify _repr_html_() returns embeddable HTML markup while a server is running."""
        n = 50
        data = np.random.randn(n) + 100
        index = np.arange(n)
        plot(index, data, data + 1, data - 1, data, open_browser=False, block=False)
        html = _repr_html_()
        assert html is not None
        assert "<div" in html


class TestGetServerStatusNullServer:
    """Test get_server_status when _active_server is None."""

    def test_returns_not_running_with_none_info(self):
        """Verify get_server_status() reports not-running with null info when no server is active."""
        import pycharting.api.interface as iface

        original = iface._active_server
        iface._active_server = None
        try:
            status = get_server_status()
            assert status["running"] is False
            assert status["server_info"] is None
            assert status["active_sessions"] == 0
        finally:
            iface._active_server = original


class TestListInputConversion:
    """Test that list inputs for subplots and trades are converted in plot()."""

    def test_plot_with_list_subplots(self):
        """Verify plot() accepts a subplot whose value is a plain list and succeeds."""
        n = 50
        index = np.arange(n)
        data = np.random.randn(n) + 100
        subplots = {"RSI": list(range(n))}
        result = plot(
            index,
            data,
            data + 1,
            data - 1,
            data,
            subplots=subplots,
            open_browser=False,
            block=False,
        )
        assert result["status"] == "success"

    def test_plot_with_list_subplots_dict_format(self):
        """Verify plot() accepts a subplot dict with list data and a type and succeeds."""
        n = 50
        index = np.arange(n)
        data = np.random.randn(n) + 100
        subplots = {"Vol": {"data": list(range(n)), "type": "bar"}}
        result = plot(
            index,
            data,
            data + 1,
            data - 1,
            data,
            subplots=subplots,
            open_browser=False,
            block=False,
        )
        assert result["status"] == "success"

    def test_plot_with_list_subplots_multi_series(self):
        """Verify plot() accepts a subplot defined as a list of series dicts and succeeds."""
        n = 50
        index = np.arange(n)
        data = np.random.randn(n) + 100
        subplots = {"MACD": [{"data": list(range(n)), "type": "line"}, {"data": list(range(n)), "type": "bar"}]}
        result = plot(
            index,
            data,
            data + 1,
            data - 1,
            data,
            subplots=subplots,
            open_browser=False,
            block=False,
        )
        assert result["status"] == "success"

    def test_plot_with_list_trades(self):
        """Verify plot() accepts a plain list of trade markers and succeeds."""
        n = 50
        index = np.arange(n)
        data = np.random.randn(n) + 100
        trades = [0] * n
        result = plot(
            index,
            data,
            data + 1,
            data - 1,
            data,
            trades=trades,
            open_browser=False,
            block=False,
        )
        assert result["status"] == "success"
