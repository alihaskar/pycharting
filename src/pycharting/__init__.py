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
    The main entry point is the `plot` function.

    ```python
    from pycharting import plot, stop_server
    import numpy as np

    # Prepare your data (numpy arrays or pandas Series)
    index = np.arange(100)
    open_data = np.random.rand(100) + 100
    high_data = open_data + 1
    low_data = open_data - 1
    close_data = open_data + 0.5

    # Create and open the chart
    plot(index, open_data, high_data, low_data, close_data)

    # ... keep the script running if needed ...
    # input("Press Enter to stop...")
    # stop_server()
    ```

Exports:
    - `plot`: Main function to create and display charts.
    - `stop_server`: Function to gracefully shut down the local chart server.
    - `get_server_status`: Function to check the status of the background server.
"""

from importlib.metadata import version as _distribution_version

from .api.interface import get_server_status, plot, stop_server

__all__ = ["__version__", "get_server_status", "plot", "stop_server"]

# Resolved from the installed distribution metadata, which is generated from the
# version in pyproject.toml. That is the single place to bump; nothing here needs
# to be kept in sync by hand.
__version__ = _distribution_version("pycharting")
