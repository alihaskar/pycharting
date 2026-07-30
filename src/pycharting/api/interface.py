"""Main User Interface for PyCharting.

This module exposes the high-level functions that users interact with to create charts,
manage the server, and check status. It bridges the gap between the user's data (numpy/pandas)
and the internal server/data management logic.

The primary function is `plot()`, which orchestrates:
1. Validating and ingesting user data via `DataManager`.
2. Starting (or reusing) the background `ChartServer`.
3. Constructing the visualization URL.
4. Opening the chart in the user's default web browser.

It also provides utilities for manual server control (`stop_server`, `get_server_status`)
and Jupyter notebook integration.
"""

import logging
import time
import webbrowser
from typing import Any, TypedDict, cast

import numpy as np
import pandas as pd

from pycharting.api.routes import _data_managers
from pycharting.core.lifecycle import ChartServer
from pycharting.data.ingestion import DataManager, DataValidationError, SubplotSpec

logger = logging.getLogger(__name__)

# Global server instance
_active_server: ChartServer | None = None


class PlotResult(TypedDict, total=False):
    """Structured result returned by :func:`plot`.

    ``status`` and ``session_id`` are always present. On success the URL/server
    fields are populated; on failure ``stage`` ("validation" or "server") and
    ``error`` describe what went wrong.
    """

    status: str
    session_id: str
    url: str
    server_url: str
    data_points: int
    server_running: bool
    stage: str
    error: str


class ServerStatus(TypedDict):
    """Structured result returned by :func:`get_server_status`."""

    running: bool
    server_info: dict[str, Any] | None
    active_sessions: int


def _notify(message: str) -> None:
    """Emit a user-facing console message.

    All direct, user-facing output (chart URLs, status banners) is funneled
    through this single helper rather than scattered ``print`` calls, so the
    output channel is consistent and can be changed in one place. Diagnostic
    detail continues to flow through ``logger``.

    Args:
        message (str): The message to display to the user.
    """
    print(message)


def plot(
    index: np.ndarray | pd.Series | list[Any],
    # `open` shadows the builtin, but Open/High/Low/Close is the domain vocabulary of
    # OHLC data and `plot(open=...)` is this library's documented public API. Renaming
    # it would break callers, so the shadowing is accepted here.
    open: np.ndarray | pd.Series | list[Any] | None = None,  # noqa: A002
    high: np.ndarray | pd.Series | list[Any] | None = None,
    low: np.ndarray | pd.Series | list[Any] | None = None,
    close: np.ndarray | pd.Series | list[Any] | None = None,
    overlays: dict[str, np.ndarray | pd.Series | list[Any]] | None = None,
    subplots: dict[str, SubplotSpec] | None = None,
    trades: np.ndarray | pd.Series | list[Any] | None = None,
    session_id: str = "default",
    port: int | None = None,
    open_browser: bool = True,
    server_timeout: float = 2.0,
    block: bool = True,
) -> PlotResult:
    """Generate and display an interactive OHLC (Open-High-Low-Close) or Line chart.

    This function is the primary interface for PyCharting. It performs the following steps:
    1.  **Data Ingestion:** Converts input lists, pandas Series, or numpy arrays into optimized
        internal formats.
    2.  **Server Management:** Checks if a background chart server is running. If not, it starts
        one on a separate thread.
    3.  **Session Registration:** Stores the provided data under a `session_id`. This allows multiple charts to coexist
        or data to be updated.
    4.  **Browser Launch:** Automatically opens the default web browser to the generated chart URL.

    The chart is rendered using a high-performance web frontend capable of handling millions of data points via
    dynamic data slicing.

    Args:
        index (Union[np.ndarray, pd.Series, list]): The x-axis data (timestamps or integer indices).
            Must have the same length as price arrays.
        open (Optional[Union[np.ndarray, pd.Series, list]]): Opening prices.
        high (Optional[Union[np.ndarray, pd.Series, list]]): Highest prices during the interval.
        low (Optional[Union[np.ndarray, pd.Series, list]]): Lowest prices during the interval.
        close (Optional[Union[np.ndarray, pd.Series, list]]): Closing prices. If only `close` is provided
            (without open/high/low), a line chart will be rendered instead of candlesticks.
        overlays (Optional[Dict[str, Union[np.ndarray, pd.Series, list]]]): A dictionary of additional series to
            plot *over* the main price chart. Keys are labels (e.g., "SMA 50"), values are data arrays.
            Useful for Moving Averages, Bollinger Bands, etc.
        subplots (Optional[Dict[str, Union[np.ndarray, pd.Series, list]]]): A dictionary of series to plot in
            separate panels *below* the main chart. Keys are labels (e.g., "RSI", "Volume"), values are data arrays.
        trades (Optional[Union[np.ndarray, pd.Series, list]]): Trade markers aligned with `index`, encoded as
            +1 (buy/long), -1 (sell/short), or 0 (no trade).
        session_id (str): A unique identifier for this dataset. Use different IDs to keep multiple charts active
            simultaneously. Defaults to "default".
        port (Optional[int]): Specific port to run the server on. If `None` (default), a free port is
            automatically found.
        open_browser (bool): If `True` (default), automatically launches the system's default web browser to
            view the chart.
        server_timeout (float): Maximum time (in seconds) to wait for the server to start before proceeding.
            Defaults to 2.0.
        block (bool): If `True` (default), blocks execution until the browser page is closed. Useful in
            Jupyter notebooks.

    Returns:
        Dict[str, Any]: A dictionary containing execution details:
            - `status`: "success" or "error".
            - `url`: The full URL to view the chart.
            - `server_url`: The base URL of the server.
            - `session_id`: The session ID used.
            - `data_points`: Number of data points loaded.
            - `server_running`: Boolean indicating if the server is active.

    Example:
        ```python
        import numpy as np
        from pycharting import plot

        # 1. Prepare Data
        n = 1000
        index = np.arange(n)
        close = np.cumsum(np.random.randn(n)) + 100

        # 2. Simple Line Chart
        plot(index, close=close)

        # 3. Candlestick Chart
        open_p = close + np.random.randn(n) * 0.5
        high = np.maximum(open_p, close) + np.abs(np.random.randn(n))
        low = np.minimum(open_p, close) - np.abs(np.random.randn(n))

        plot(
            index, open_p, high, low, close,
            overlays={"SMA 20": sma},
            session_id="my-analysis"
        )
        ```
    """
    global _active_server

    try:
        # Convert lists to numpy arrays for convenience
        if isinstance(index, list):
            index = np.array(index)
        if isinstance(open, list):
            open = np.array(open)  # noqa: A001
        if isinstance(high, list):
            high = np.array(high)
        if isinstance(low, list):
            low = np.array(low)
        if isinstance(close, list):
            close = np.array(close)

        # Convert overlay lists
        if overlays:
            overlays = {k: np.array(v) if isinstance(v, list) else v for k, v in overlays.items()}

        if subplots:
            converted: dict[str, SubplotSpec] = {}
            for k, v in subplots.items():
                if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                    converted[k] = [
                        {
                            **entry,
                            "data": np.array(entry["data"])
                            if isinstance(entry.get("data"), list)
                            else entry.get("data"),
                        }
                        for entry in v
                    ]
                elif isinstance(v, dict):
                    d = v.get("data")
                    converted[k] = cast("dict[str, Any]", {**v, "data": np.array(d) if isinstance(d, list) else d})
                else:
                    converted[k] = np.array(v) if isinstance(v, list) else v
            subplots = converted

        # Convert trades list
        if isinstance(trades, list):
            trades = np.array(trades)

        # Create DataManager with validation
        logger.info("Creating DataManager...")
        data_manager = DataManager(
            index=index,
            open=open,
            high=high,
            low=low,
            close=close,
            overlays=overlays,
            subplots=subplots,
            trades=trades,
        )

        # Store in global session registry for API access
        _data_managers[session_id] = data_manager
        logger.info(f"Data loaded: {data_manager.length} points")

        # Start or reuse server
        if _active_server is None or not _active_server.is_running:
            logger.info("Starting ChartServer...")
            _active_server = ChartServer(
                host="127.0.0.1",
                port=port,
                auto_shutdown_timeout=3.0,  # 3 seconds after disconnect
            )
            server_info = _active_server.start_server()

            # Wait for server to be ready
            time.sleep(server_timeout)

        else:
            logger.info("Reusing existing ChartServer...")
            server_info = _active_server.server_info
            server_info["url"] = f"http://{server_info['host']}:{server_info['port']}"

        # Construct chart URL with session ID and timestamp to bust cache
        # Use viewport demo which pulls data from the API for the given session
        ts = int(time.time())
        chart_url = f"{server_info['url']}/static/viewport-demo.html?session={session_id}&v={ts}"

        # Open browser if requested
        if open_browser:
            logger.info(f"Opening browser: {chart_url}")
            try:
                webbrowser.open(chart_url)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Could not open browser: {e}")
                _notify(f"Please open this URL manually: {chart_url}")

        result: PlotResult = {
            "status": "success",
            "url": chart_url,
            "server_url": server_info["url"],
            "session_id": session_id,
            "data_points": data_manager.length,
            "server_running": _active_server.is_running if _active_server else False,
        }

        # Print user-friendly message
        _notify("\n✓ Chart created successfully!")
        _notify(f"  URL: {chart_url}")
        _notify(f"  Data points: {data_manager.length:,}")
        if not open_browser:
            _notify("  Open the URL above in your browser to view the chart.")
        _notify("")

        # Block until server shutdown if requested
        if block and _active_server:
            logger.info("Blocking until chart is closed (press Ctrl+C to force exit)...")
            _notify("Keeping server alive until you close the browser page...")
            try:
                # Wait with timeout so Ctrl+C can interrupt
                while not _active_server._shutdown_event.is_set():
                    _active_server._shutdown_event.wait(timeout=0.5)
                logger.info("Server shutdown detected, returning control")
                _notify("\n✓ Chart closed, server stopped")
            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                _notify("\n⚠️  Interrupted - stopping server...")
                _active_server.stop_server()

    except DataValidationError as e:
        # Input data failed validation — the user can fix this by correcting
        # their arrays before calling plot() again.
        logger.error(f"Invalid input data: {e}", exc_info=True)
        _notify(f"\n✗ Invalid input data: {e}\n")

        return {
            "status": "error",
            "stage": "validation",
            "error": str(e),
            "session_id": session_id,
        }
    except Exception as e:
        # Server startup, browser launch, or other runtime failure — not
        # something the caller's data can fix.
        logger.error(f"Error creating chart: {e}", exc_info=True)
        _notify(f"\n✗ Error creating chart: {e}\n")

        return {
            "status": "error",
            "stage": "server",
            "error": str(e),
            "session_id": session_id,
        }
    else:
        return result


def stop_server() -> None:
    """Manually shut down the active chart server.

    While the server has an auto-shutdown feature (triggered after a timeout when no clients are connected),
    this function allows for immediate, manual cleanup. This is useful in scripts or notebooks where you want
    to ensure resources are freed immediately after a session.

    If no server is running, this function does nothing and prints a message.

    Example:
        ```python
        from pycharting import stop_server

        # ... after done with analysis ...
        stop_server()
        ```
    """
    global _active_server

    if _active_server and _active_server.is_running:
        logger.info("Stopping ChartServer...")
        _active_server.stop_server()
        _notify("✓ Chart server stopped")
    else:
        _notify("ⓘ No active server to stop")


def get_server_status() -> ServerStatus:
    """Retrieve the current status of the background chart server.

    This is useful for debugging connection issues or checking if a session is still active.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - `running`: Boolean indicating if the server process is alive.
            - `server_info`: Dictionary of host, port, and connection details (or None).
            - `active_sessions`: Count of currently loaded datasets/sessions.

    Example:
        ```python
        from pycharting import get_server_status

        status = get_server_status()
        if status['running']:
            print(f"Server running at {status['server_info']['url']}")
        ```
    """
    global _active_server

    if _active_server:
        return {
            "running": _active_server.is_running,
            "server_info": _active_server.server_info,
            "active_sessions": len(_data_managers),
        }
    else:
        return {
            "running": False,
            "server_info": None,
            "active_sessions": 0,
        }


# Jupyter notebook support
def _repr_html_() -> str:
    """Jupyter notebook representation."""
    status = get_server_status()
    server_info = status["server_info"]
    if status["running"] and server_info is not None:
        url = f"http://{server_info['host']}:{server_info['port']}"
        return f'''
        <div style="padding: 10px; background: #f0f0f0; border-radius: 5px;">
            <strong>PyCharting Server</strong><br>
            Status: <span style="color: green;">●</span> Running<br>
            URL: <a href="{url}" target="_blank">{url}</a><br>
            Active Sessions: {status["active_sessions"]}
        </div>
        '''
    else:
        return """
        <div style="padding: 10px; background: #f0f0f0; border-radius: 5px;">
            <strong>PyCharting Server</strong><br>
            Status: <span style="color: red;">●</span> Stopped
        </div>
        """


# Export main functions
__all__ = ["get_server_status", "plot", "stop_server"]
