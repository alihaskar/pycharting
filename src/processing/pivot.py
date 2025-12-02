"""Data pivoting module for converting DataFrames to uPlot format."""
import pandas as pd
import numpy as np
from typing import List, Any, Literal


def datetime_to_unix_ms(dt: pd.Timestamp) -> int:
    """
    Convert a pandas Timestamp to Unix milliseconds.
    
    Args:
        dt: Pandas Timestamp (timezone-aware or naive)
        
    Returns:
        Unix timestamp in milliseconds (integer)
        
    Example:
        >>> dt = pd.Timestamp("2024-01-01", tz="UTC")
        >>> datetime_to_unix_ms(dt)
        1704067200000
    """
    # If naive, assume UTC
    if dt.tz is None:
        dt = dt.tz_localize("UTC")
    
    # Convert to Unix timestamp in seconds, then to milliseconds
    return int(dt.timestamp() * 1000)


def datetime_to_unix_seconds(dt: pd.Timestamp) -> int:
    """
    Convert a pandas Timestamp to Unix seconds.
    
    Args:
        dt: Pandas Timestamp (timezone-aware or naive)
        
    Returns:
        Unix timestamp in seconds (integer)
        
    Example:
        >>> dt = pd.Timestamp("2024-01-01", tz="UTC")
        >>> datetime_to_unix_seconds(dt)
        1704067200
    """
    # If naive, assume UTC
    if dt.tz is None:
        dt = dt.tz_localize("UTC")
    
    # Convert to Unix timestamp in seconds
    return int(dt.timestamp())


def to_uplot_format(
    df: pd.DataFrame,
    timestamp_unit: Literal["ms", "s"] = "ms"
) -> List[List[Any]]:
    """
    Convert a Pandas DataFrame to uPlot's columnar array format.
    
    uPlot expects data in columnar format:
    [
        [timestamp1, timestamp2, ...],  # Unix timestamps
        [open1, open2, ...],
        [high1, high2, ...],
        [low1, low2, ...],
        [close1, close2, ...],
        [volume1, volume2, ...],
        [indicator1_val1, indicator1_val2, ...],  # Optional indicators
        ...
    ]
    
    Args:
        df: DataFrame with DatetimeIndex and OHLCV columns
            Required columns: 'open', 'high', 'low', 'close', 'volume'
            Optional: any additional indicator columns
        timestamp_unit: Unit for Unix timestamps ('ms' for milliseconds, 's' for seconds)
                       Default: 'ms'
    
    Returns:
        List of lists in columnar format for uPlot
        
    Raises:
        ValueError: If DataFrame doesn't have DatetimeIndex or required columns
        
    Example:
        >>> df = pd.DataFrame({
        ...     'open': [100, 101],
        ...     'high': [105, 106],
        ...     'low': [95, 96],
        ...     'close': [102, 103],
        ...     'volume': [1000, 1100]
        ... }, index=pd.date_range('2024-01-01', periods=2, freq='1h'))
        >>> result = to_uplot_format(df)
        >>> len(result)
        6
    """
    # Validate DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError(
            "DataFrame must have a DatetimeIndex. "
            "Use df.set_index('timestamp') if needed."
        )
    
    # Validate required OHLCV columns
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"DataFrame is missing required columns: {missing_cols}. "
            f"Required columns are: {required_cols}"
        )
    
    # Initialize result list
    result = []
    
    # First column: timestamps converted to Unix time
    if timestamp_unit == "ms":
        timestamps = [datetime_to_unix_ms(ts) for ts in df.index]
    else:  # timestamp_unit == "s"
        timestamps = [datetime_to_unix_seconds(ts) for ts in df.index]
    result.append(timestamps)
    
    # Add OHLCV columns in order
    for col in required_cols:
        result.append(df[col].tolist())
    
    # Add any additional indicator columns
    indicator_cols = [col for col in df.columns if col not in required_cols]
    for col in sorted(indicator_cols):  # Sort for consistent ordering
        result.append(df[col].tolist())
    
    return result

