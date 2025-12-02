"""Data resampling and downsampling module for OHLC data."""
import pandas as pd
import numpy as np
from typing import Union


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
        timeframe: Target timeframe (e.g., '5min', '1H', '1D')
    
    Returns:
        Resampled DataFrame with same structure
        
    Examples:
        >>> df_5min = resample_ohlc(df_1min, '5min')
        >>> df_daily = resample_ohlc(df_hourly, '1D')
    """
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

