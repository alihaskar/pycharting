"""Tests for Python API interface."""

from unittest.mock import patch

import numpy as np
import pytest

from pycharting.api.interface import _repr_html_, get_server_status, plot, stop_server
from pycharting.api.routes import _data_managers


@pytest.fixture(autouse=True)
def portless_fast_server(fake_uvicorn):
    """Make ``plot()`` fast and portless for interface tests.

    Depends on ``fake_uvicorn`` (portless server, see conftest) and additionally
    neutralises the ``time.sleep(server_timeout)`` readiness pause in
    ``interface`` so tests neither bind a socket nor wait on wall-clock sleeps.
    The blocking loop uses ``_shutdown_event.wait`` (not ``time.sleep``), so it is
    unaffected by this patch.
    """
    with patch("pycharting.api.interface.time.sleep"):
        yield


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
        """Stop any live server and clear module-global session state."""
        if iface._active_server and iface._active_server.is_running:
            iface._active_server.stop_server()
        iface._active_server = None
        _data_managers.clear()

    _reset()
    yield
    _reset()


def test_plot_basic_usage():
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


def test_plot_with_custom_session():
    """Test plot with custom session ID."""
    n = 50
    index = np.arange(n)
    data = np.random.randn(n) + 100

    result = plot(index, data, data + 1, data - 1, data, session_id="custom_session", open_browser=False, block=False)

    assert result["status"] == "success"
    assert result["session_id"] == "custom_session"
    assert "custom_session" in _data_managers


def test_plot_with_overlays():
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


def test_plot_reuses_server():
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


def test_plot_with_invalid_data():
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
    # A validation failure must be reported as such, distinct from server/runtime errors.
    assert result["stage"] == "validation"


def test_plot_server_startup_failure_reported_as_server_stage():
    """A non-validation failure (e.g. server startup) is reported with stage='server'."""
    n = 20
    data = np.random.randn(n) + 100
    index = np.arange(n)

    # Valid data passes validation, so the error must come from a later stage.
    with patch("pycharting.api.interface.ChartServer") as mock_server:
        mock_server.side_effect = RuntimeError("boom: could not start server")
        result = plot(index, close=data, open_browser=False, block=False)

    assert result["status"] == "error"
    assert result["stage"] == "server"
    assert "boom" in result["error"]


def test_plot_block_returns_when_shutdown_event_set():
    """With block=True, plot() waits on the shutdown event and returns when it fires.

    Covers the previously ``# pragma: no cover`` blocking loop. A fake shutdown
    event reports "not set" once (so the loop body runs) then "set" to release it.
    """

    class _Event:
        """Fake shutdown event that reports "not set" once, then "set"."""

        def __init__(self):
            self._checks = 0

        def is_set(self):
            """Return False on the first call, then True, yielding one loop iteration."""
            self._checks += 1
            return self._checks > 1  # False first, then True -> exactly one iteration

        def wait(self, timeout=None):
            """Return immediately — the wait duration is irrelevant to this test."""
            return None

    n = 10
    data = np.random.randn(n) + 100
    index = np.arange(n)

    with patch("pycharting.api.interface.ChartServer") as mock_cls:
        inst = mock_cls.return_value
        inst.is_running = True
        inst.start_server.return_value = {"host": "127.0.0.1", "port": 1234, "url": "http://127.0.0.1:1234"}
        inst._shutdown_event = _Event()
        result = plot(index, close=data, open_browser=False, block=True)

    assert result["status"] == "success"


def test_plot_block_handles_keyboard_interrupt():
    """A Ctrl+C during the blocking wait stops the server and still returns success."""

    class _InterruptingEvent:
        """Fake shutdown event whose wait raises ``KeyboardInterrupt``."""

        def is_set(self):
            """Report the event as never set, so ``plot()`` enters the blocking wait."""
            return False

        def wait(self, timeout=None):
            """Simulate a Ctrl+C arriving while the caller is blocked."""
            raise KeyboardInterrupt

    n = 10
    data = np.random.randn(n) + 100
    index = np.arange(n)

    with patch("pycharting.api.interface.ChartServer") as mock_cls:
        inst = mock_cls.return_value
        inst.is_running = True
        inst.start_server.return_value = {"host": "127.0.0.1", "port": 1234, "url": "http://127.0.0.1:1234"}
        inst._shutdown_event = _InterruptingEvent()
        result = plot(index, close=data, open_browser=False, block=True)

    inst.stop_server.assert_called_once()
    assert result["status"] == "success"


@patch("webbrowser.open")
def test_plot_opens_browser(mock_browser):
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
def test_plot_handles_browser_error(mock_browser):
    """Test that plot handles browser opening errors gracefully."""
    n = 50
    data = np.random.randn(n) + 100
    index = np.arange(n)

    # Should still succeed even if browser fails
    result = plot(index, data, data + 1, data - 1, data, open_browser=True, block=False)

    assert result["status"] == "success"
    assert result["server_running"] is True


def test_stop_server_when_running():
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


def test_stop_server_when_not_running(capsys):
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


def test_status_when_no_server():
    """Test status when no server has been started."""
    status = get_server_status()

    assert status["running"] is False
    # server_info may exist from previous server, just check it's not running
    assert status["active_sessions"] == 0


def test_status_when_server_running():
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


def test_plot_with_numpy_arrays():
    """Test plot with NumPy arrays."""
    n = 50
    index = np.arange(n)
    close = np.random.randn(n) + 100

    result = plot(index, close, close + 1, close - 1, close, open_browser=False, block=False)

    assert result["status"] == "success"


def test_plot_with_lists():
    """Test plot with Python lists."""
    n = 50
    index = list(range(n))
    close = [100 + i * 0.1 for i in range(n)]

    result = plot(index, close, [c + 1 for c in close], [c - 1 for c in close], close, open_browser=False, block=False)

    assert result["status"] == "success"


def test_full_workflow():
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


def test_multiple_sessions():
    """Test creating multiple chart sessions."""
    n = 50
    data = np.random.randn(n) + 100
    index = np.arange(n)

    # Create multiple sessions
    for i in range(3):
        result = plot(index, data, data + 1, data - 1, data, session_id=f"session_{i}", open_browser=False, block=False)
        assert result["status"] == "success"

    # Check all sessions exist
    assert len(_data_managers) >= 3
    for i in range(3):
        assert f"session_{i}" in _data_managers


def test_repr_html_when_no_server():
    """Verify _repr_html_() reports a stopped state when no server is active."""
    import pycharting.api.interface as iface

    original = iface._active_server
    iface._active_server = None
    try:
        html = _repr_html_()
        assert "Stopped" in html
    finally:
        iface._active_server = original


def test_repr_html_when_server_running():
    """Verify _repr_html_() returns embeddable HTML markup while a server is running."""
    n = 50
    data = np.random.randn(n) + 100
    index = np.arange(n)
    plot(index, data, data + 1, data - 1, data, open_browser=False, block=False)
    html = _repr_html_()
    assert html is not None
    assert "<div" in html


def test_returns_not_running_with_none_info():
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


def test_plot_with_list_subplots():
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


def test_plot_with_list_subplots_dict_format():
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


def test_plot_with_list_subplots_multi_series():
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


def test_plot_with_list_trades():
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


# --- package import smoke tests (folded from test_import.py) ---


def test_package_import():
    """Test that the main package can be imported."""
    import pycharting

    assert isinstance(pycharting.__version__, str)
    assert pycharting.__version__


def test_core_import():
    """Test that core module can be imported."""
    from pycharting import core

    assert core is not None


def test_data_import():
    """Test that data module can be imported."""
    from pycharting import data

    assert data is not None


def test_api_import():
    """Test that api module can be imported."""
    from pycharting import api

    assert api is not None


def test_web_import():
    """Test that web module can be imported."""
    from pycharting import web

    assert web is not None


def test_dependencies_available():
    """Test that core dependencies are available."""
    import fastapi
    import numpy as np
    import pandas as pd
    import uvicorn

    assert pd is not None
    assert np is not None
    assert fastapi is not None
    assert uvicorn is not None


class TestPlotResult:
    """Tests for the PlotResult TypedDict returned by ``plot``."""

    def test_declares_the_documented_keys(self):
        """The declared keys are the full documented result contract."""
        from pycharting.api.interface import PlotResult

        assert set(PlotResult.__annotations__) == {
            "status",
            "session_id",
            "url",
            "server_url",
            "data_points",
            "server_running",
            "stage",
            "error",
        }

    def test_every_key_is_optional(self):
        """``total=False`` means success and failure shapes share one type."""
        from pycharting.api.interface import PlotResult

        assert PlotResult.__total__ is False
        assert PlotResult.__required_keys__ == frozenset()

    def test_success_result_only_uses_declared_keys(self):
        """A real successful plot() result introduces no undeclared key."""
        from pycharting.api.interface import PlotResult

        n = 10
        result = plot(np.arange(n), close=np.random.randn(n) + 100, open_browser=False, block=False)

        assert result["status"] == "success"
        assert set(result) <= set(PlotResult.__annotations__)

    def test_validation_error_result_only_uses_declared_keys(self):
        """A validation failure also stays within the declared keys."""
        from pycharting.api.interface import PlotResult

        result = plot(np.arange(10), close=np.random.randn(5), open_browser=False, block=False)

        assert result["stage"] == "validation"
        assert set(result) <= set(PlotResult.__annotations__)


class TestServerStatus:
    """Tests for the ServerStatus TypedDict returned by ``get_server_status``."""

    def test_declares_the_documented_keys(self):
        """The declared keys are the full documented status contract."""
        from pycharting.api.interface import ServerStatus

        assert set(ServerStatus.__annotations__) == {"running", "server_info", "active_sessions"}

    def test_every_key_is_required(self):
        """Unlike PlotResult, the status shape is total."""
        from pycharting.api.interface import ServerStatus

        assert ServerStatus.__total__ is True

    def test_payload_matches_declaration_when_stopped(self):
        """get_server_status() returns exactly the declared keys with no server."""
        from pycharting.api.interface import ServerStatus

        status = get_server_status()

        assert set(status) == set(ServerStatus.__annotations__)
        assert status["running"] is False
        assert status["server_info"] is None
