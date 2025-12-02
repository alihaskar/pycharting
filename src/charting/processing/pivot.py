"""Data pivoting module for converting DataFrames to uPlot format."""
import pandas as pd
import numpy as np
import math
from typing import List, Any, Literal


class DataAlignmentError(ValueError):
    """Custom exception for data alignment errors."""
    pass


def verify_data_alignment(data: List[List[Any]]) -> None:
    """
    Verify that all arrays in the data structure have consistent length.
    
    Ensures all columnar arrays (timestamps, OHLC, indicators) have the
    same number of data points, which is critical for uPlot rendering.
    
    Args:
        data: List of columnar arrays (nested list structure)
        
    Raises:
        DataAlignmentError: If arrays have inconsistent lengths
        
    Example:
        >>> data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        >>> verify_data_alignment(data)  # OK
        >>> bad_data = [[1, 2], [4, 5, 6]]
        >>> verify_data_alignment(bad_data)  # Raises DataAlignmentError
    """
    if not data:
        return  # Empty data is trivially aligned
    
    # Get length of first array as reference
    expected_length = len(data[0])
    
    # Check all arrays have same length
    for i, arr in enumerate(data):
        if len(arr) != expected_length:
            raise DataAlignmentError(
                f"Data alignment error: Column {i} has length {len(arr)}, "
                f"but expected {expected_length}. All columns must have "
                f"the same number of data points."
            )


def sanitize_nan_values(values: List[Any]) -> List[Any]:
    """
    Convert NaN, Inf, and NA values to None for JSON compatibility.
    
    Handles:
    - np.nan (numpy NaN)
    - float('nan') (Python NaN)
    - pd.NA (pandas NA)
    - np.inf and -np.inf (infinity)
    
    Args:
        values: List of values that may contain NaN/Inf/NA
        
    Returns:
        List with NaN/Inf/NA converted to None
        
    Example:
        >>> sanitize_nan_values([1.0, np.nan, 3.0])
        [1.0, None, 3.0]
    """
    result = []
    for val in values:
        # Check for various NaN/NA representations
        if val is pd.NA:
            result.append(None)
        elif isinstance(val, float):
            # Check for NaN or Inf
            if math.isnan(val) or math.isinf(val):
                result.append(None)
            else:
                result.append(val)
        else:
            result.append(val)
    
    return result


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
        df: DataFrame with DatetimeIndex and OHLC columns
            Required columns: 'open', 'high', 'low', 'close'
            Optional: 'volume' and any additional indicator columns
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
    
    # Validate required OHLC columns (volume is optional)
    required_cols = ['open', 'high', 'low', 'close']
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
    
    # Add OHLC columns in order with NaN sanitization
    for col in required_cols:
        values = df[col].tolist()
        sanitized = sanitize_nan_values(values)
        result.append(sanitized)
    
    # Add volume if it exists
    if 'volume' in df.columns:
        values = df['volume'].tolist()
        sanitized = sanitize_nan_values(values)
        result.append(sanitized)
    
    # Add any additional indicator columns with NaN sanitization
    indicator_cols = [col for col in df.columns if col not in required_cols and col != 'volume']
    for col in sorted(indicator_cols):  # Sort for consistent ordering
        values = df[col].tolist()
        sanitized = sanitize_nan_values(values)
        result.append(sanitized)
    
    # Verify data alignment before returning
    verify_data_alignment(result)
    
    return result

