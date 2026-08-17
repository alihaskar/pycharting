"""PyCharting: Interactive Financial Charting Library.

This package provides a high-performance, interactive charting solution for financial data
(OHLC), designed to handle large datasets efficiently. It uses a local server architecture
to render charts in the web browser, allowing for smooth zooming, panning, and analysis.

Key Features:
- **High Performance:** Capable of handling millions of data points using efficient data slicing.
- **Interactive:** Zoom, pan, and inspect data in real-time.
- **Flexible:** Support for overlays (e.g., Moving Averages) and subplots (e.g., RSI, Volume).
- **Easy to Use:** Simple Python API similar to matplotlib or plotly.

Usage:
    The public surface is three functions, re-exported at the top level:

    >>> import pycharting
    >>> sorted(pycharting.__all__)
    ['__version__', 'get_server_status', 'plot', 'stop_server']

    The main entry point is `plot`. It starts a local server and opens a
    browser, so the example below is illustrative rather than executed here:

    >>> import numpy as np
    >>> from pycharting import plot, stop_server
    >>> index = np.arange(100)
    >>> open_data = np.random.rand(100) + 100
    >>> high_data = open_data + 1
    >>> low_data = open_data - 1
    >>> close_data = open_data + 0.5
    >>> plot(index, open_data, high_data, low_data, close_data)  # doctest: +SKIP
    >>> stop_server()  # doctest: +SKIP

Exports:
    - `plot`: Main function to create and display charts.
    - `stop_server`: Function to gracefully shut down the local chart server.
    - `get_server_status`: Function to check the status of the background server.
"""

from .api.interface import get_server_status, plot, stop_server

__all__ = ["__version__", "get_server_status", "plot", "stop_server"]

# Keep this in sync with pyproject.toml
__version__ = "0.2.14"
