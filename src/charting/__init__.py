"""
Python API for Financial Charting Tool.

Provides a simple interface for displaying Pandas DataFrames as
interactive charts in the browser with automatic OHLC and indicator detection.

Basic Usage:
    >>> import charting
    >>> charting.plot(df)

Advanced Usage:
    >>> from charting import Charting
    >>> chart = Charting(height=800, port=8080, auto_open=False)
    >>> url = chart.load(df, overlays=['sma_20'], subplots=['rsi_14'])
    >>> print(url)
"""

__version__ = "1.0.0"

import time
import logging

# Export main Charting class and utility functions
from .charting import Charting
from .detector import detect_ohlc_columns, classify_indicators
from .transformer import transform_dataframe_to_csv

logger = logging.getLogger(__name__)

def plot(data, **kwargs):
    """
    Plot data in a single command.
    
    Args:
        data: pandas DataFrame or path to CSV file
        **kwargs: Arguments passed to Charting.load()
            - overlays: List of overlay indicator columns
            - subplots: List of subplot indicator columns
            - indicators: Dict of {name: is_overlay}
            - open, high, low, close, volume: Explicit column names
            - port: Server port (default: 8000)
            - height: Chart height (default: 600)
            - auto_open: Open browser automatically (default: True)
            - block: Block execution to keep server running (default: True)
    
    Returns:
        str: URL of the launched chart
    """
    auto_open = kwargs.pop('auto_open', True)
    port = kwargs.pop('port', None)
    height = kwargs.pop('height', 600)
    block = kwargs.pop('block', True)
    
    chart = Charting(height=height, port=port, auto_open=auto_open)
    url = chart.load(data, **kwargs)
    
    if block:
        print(f"Serving chart at {url}")
        print("Press Ctrl+C to stop...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping server...")
            chart.close()
            
    return url

# Define public API
__all__ = [
    'Charting',
    'Chart',  # Shorter alias
    'plot',
    'detect_ohlc_columns',
    'classify_indicators',
    'transform_dataframe_to_csv',
]

# Convenience alias for shorter imports
Chart = Charting
