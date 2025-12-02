"""Data resampling and downsampling module for OHLC data."""
import pandas as pd
import numpy as np
import re
import pytz
from typing import Union, Optional


class TimeframeValidationError(Exception):
    """Custom exception for timeframe validation errors."""
    pass


def validate_timeframe(timeframe: str) -> None:
    """
    Validate that a timeframe string is in a supported format.
    
    Supported formats:
    - Minutes: 1min, 5min, 15min, 30min, etc.
    - Hours: 1h, 4h, 12h, etc.
    - Days: 1D
    - Weeks: 1W
    - Months: 1M
    
    Args:
        timeframe: Timeframe string to validate
        
    Raises:
        TimeframeValidationError: If timeframe is invalid
    """
    if timeframe is None:
        raise TimeframeValidationError("Timeframe cannot be None")
    
    # Strip whitespace and convert to string
    timeframe = str(timeframe).strip()
    
    if not timeframe:
        raise TimeframeValidationError("Timeframe cannot be empty")
    
    # Pattern: number followed by time unit
    # Supported units: min, h, D, W, M
    pattern = r'^(\d+)(min|h|H|d|D|w|W|m|M)$'
    
    if not re.match(pattern, timeframe, re.IGNORECASE):
        raise TimeframeValidationError(
            f"Invalid timeframe format: '{timeframe}'. "
            f"Supported formats: 1min, 5min, 1h, 1D, 1W, 1M"
        )
    
    # Extract unit for additional validation
    match = re.match(pattern, timeframe, re.IGNORECASE)
    unit = match.group(2).lower()
    
    # Check for unsupported units (like seconds, years)
    if unit == 's':
        raise TimeframeValidationError("Seconds are not supported")
    if unit == 'y':
        raise TimeframeValidationError("Years are not supported")


def parse_timeframe(timeframe: str) -> str:
    """
    Parse and normalize a timeframe string to pandas frequency format.
    
    Converts various timeframe formats to standardized pandas-compatible strings.
    
    Args:
        timeframe: Timeframe string (e.g., "5min", "1H", "1D")
        
    Returns:
        Normalized timeframe string compatible with pandas resample
        
    Raises:
        TimeframeValidationError: If timeframe is invalid
        
    Examples:
        >>> parse_timeframe("5MIN")
        '5min'
        >>> parse_timeframe("1h")
        '1h'
        >>> parse_timeframe("1d")
        '1D'
    """
    # First validate the timeframe
    validate_timeframe(timeframe)
    
    # Strip whitespace
    timeframe = timeframe.strip()
    
    # Pattern to extract number and unit
    pattern = r'^(\d+)(min|h|H|d|D|w|W|m|M)$'
    match = re.match(pattern, timeframe, re.IGNORECASE)
    
    if not match:
        raise TimeframeValidationError(f"Invalid timeframe format: '{timeframe}'")
    
    number = match.group(1)
    unit = match.group(2)
    
    # Normalize the unit
    unit_lower = unit.lower()
    
    if unit_lower == 'min':
        # Minutes stay lowercase
        normalized_unit = 'min'
    elif unit_lower == 'h':
        # Hours stay lowercase
        normalized_unit = 'h'
    elif unit_lower == 'd':
        # Days become uppercase
        normalized_unit = 'D'
    elif unit_lower == 'w':
        # Weeks become uppercase
        normalized_unit = 'W'
    elif unit_lower == 'm':
        # Month becomes uppercase (ambiguous but we treat single M as month)
        normalized_unit = 'M'
    else:
        normalized_unit = unit
    
    return f"{number}{normalized_unit}"


def resample_ohlc(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """
    Resample OHLC data to a different timeframe.
    
    Implements proper OHLC aggregation rules:
    - Open: First value in period
    - High: Maximum value in period
    - Low: Minimum value in period
    - Close: Last value in period
    - Volume: Sum of values in period
    
    Args:
        df: DataFrame with OHLC data and DatetimeIndex
        timeframe: Target timeframe (e.g., '5min', '1h', '1D')
    
    Returns:
        Resampled DataFrame with same structure
        
    Examples:
        >>> df_5min = resample_ohlc(df_1min, '5min')
        >>> df_daily = resample_ohlc(df_hourly, '1D')
    """
    # Validate and normalize timeframe
    timeframe = parse_timeframe(timeframe)
    
    # Validate input has DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame must have a DatetimeIndex")
    
    # Check if DataFrame is empty
    if len(df) == 0:
        return df.copy()
    
    # Validate required columns
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Define aggregation rules for OHLC data
    ohlc_dict = {
        'open': 'first',    # First open of period
        'high': 'max',      # Highest high of period
        'low': 'min',       # Lowest low of period
        'close': 'last',    # Last close of period
        'volume': 'sum'     # Total volume of period
    }
    
    # Resample using pandas resample with proper OHLC aggregation
    resampled = df.resample(timeframe).agg(ohlc_dict)
    
    # Drop rows where all OHLC values are NaN (no data in that period)
    resampled = resampled.dropna(how='all', subset=['open', 'high', 'low', 'close'])
    
    return resampled


def resample_ohlc_with_timezone(
    df: pd.DataFrame,
    timeframe: str,
    source_tz: Optional[str] = None,
    target_tz: Optional[str] = None
) -> pd.DataFrame:
    """
    Resample OHLC data with timezone handling and conversion.
    
    Handles timezone localization, conversion, and DST transitions.
    
    Args:
        df: DataFrame with OHLC data and DatetimeIndex
        timeframe: Target timeframe (e.g., '5min', '1h', '1D')
        source_tz: Source timezone for naive datetimes (e.g., 'UTC', 'US/Eastern')
                   If None and df has timezone, uses existing timezone
        target_tz: Target timezone for output (e.g., 'US/Eastern', 'Europe/London')
                   If None, keeps source timezone
    
    Returns:
        Resampled DataFrame with timezone-aware DatetimeIndex
        
    Raises:
        ValueError: If DataFrame doesn't have DatetimeIndex
        pytz.UnknownTimeZoneError: If timezone string is invalid
        
    Examples:
        >>> # Convert UTC to US Eastern and resample
        >>> df_eastern = resample_ohlc_with_timezone(
        ...     df_utc, '1h', target_tz='US/Eastern'
        ... )
        >>> 
        >>> # Localize naive datetime and resample
        >>> df_aware = resample_ohlc_with_timezone(
        ...     df_naive, '5min', source_tz='UTC'
        ... )
    """
    # Validate input has DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame must have a DatetimeIndex")
    
    # Check if DataFrame is empty
    if len(df) == 0:
        return df.copy()
    
    # Make a copy to avoid modifying original
    df_copy = df.copy()
    
    # Handle timezone localization for naive datetimes
    if df_copy.index.tz is None:
        if source_tz is None:
            # Default to UTC for naive datetimes
            source_tz = 'UTC'
        
        # Localize to source timezone
        try:
            tz = pytz.timezone(source_tz)
            df_copy.index = df_copy.index.tz_localize(tz)
        except pytz.UnknownTimeZoneError:
            raise ValueError(f"Invalid source timezone: '{source_tz}'")
    
    # Convert to target timezone if specified
    if target_tz is not None:
        try:
            target_tz_obj = pytz.timezone(target_tz)
            df_copy.index = df_copy.index.tz_convert(target_tz_obj)
        except pytz.UnknownTimeZoneError:
            raise ValueError(f"Invalid target timezone: '{target_tz}'")
    
    # Now resample using the existing function
    # We need to pass the df with timezone-aware index
    resampled = resample_ohlc(df_copy, timeframe)
    
    return resampled

