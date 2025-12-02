"""
Python API for Financial Charting Tool.

Task 30: Public interface for Python API

Provides a simple interface for displaying Pandas DataFrames as
interactive charts in the browser with automatic OHLC and indicator detection.

Basic Usage:
    >>> from python_api import Charting
    >>> chart = Charting()
    >>> chart.load(df)  # Auto-detects OHLC and indicators
    >>> chart.close()

Advanced Usage:
    >>> chart = Charting(height=800, port=8080, auto_open=False)
    >>> url = chart.load(df, overlays=['sma_20'], subplots=['rsi_14'])
    >>> print(url)
"""

__version__ = "1.0.0"

# Task 30.1: Export main Charting class and utility functions
from .charting import Charting
from .detector import detect_ohlc_columns, classify_indicators
from .transformer import transform_dataframe_to_csv

# Task 30.1: Define public API
__all__ = [
    'Charting',
    'Chart',  # Shorter alias
    'detect_ohlc_columns',
    'classify_indicators',
    'transform_dataframe_to_csv',
]

# Task 30.1: Convenience alias for shorter imports
Chart = Charting
