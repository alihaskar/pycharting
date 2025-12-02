"""Technical indicators calculation module."""
import pandas as pd
import numpy as np
from typing import Union


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    
    RSI = 100 - (100 / (1 + RS))
    where RS = Average Gain / Average Loss
    
    Args:
        prices: Series of price data (typically close prices)
        period: Lookback period for RSI calculation (default: 14)
    
    Returns:
        Series of RSI values with same index as input
        First 'period' values will be NaN (lookback period)
    """
    if len(prices) == 0:
        return pd.Series([], dtype=float)
    
    if len(prices) == 1:
        return pd.Series([np.nan], index=prices.index)
    
    # Calculate price changes (delta)
    delta = prices.diff()
    
    # Separate gains and losses
    gains = delta.copy()
    losses = delta.copy()
    
    gains[gains < 0] = 0  # Keep only positive changes
    losses[losses > 0] = 0  # Keep only negative changes
    losses = abs(losses)  # Make losses positive
    
    # Initialize average gain and loss series
    avg_gain = pd.Series(index=prices.index, dtype=float)
    avg_loss = pd.Series(index=prices.index, dtype=float)
    
    # Calculate first average using simple mean of first 'period' values
    # Note: We need period+1 data points (first is NaN from diff, then period values)
    if len(prices) > period:
        # First average is at position 'period' (0-indexed)
        avg_gain.iloc[period] = gains.iloc[1:period+1].mean()
        avg_loss.iloc[period] = losses.iloc[1:period+1].mean()
        
        # For subsequent values, use Wilder's smoothing
        # Smoothed average = ((Previous avg * (period - 1)) + current value) / period
        for i in range(period + 1, len(prices)):
            avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period - 1) + gains.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period - 1) + losses.iloc[i]) / period
    
    # Calculate RS (Relative Strength)
    rs = avg_gain / avg_loss
    
    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))
    
    # Handle special cases:
    # When avg_loss is 0 (all gains), RSI = 100
    rsi[avg_loss == 0] = 100.0
    # When avg_gain is 0 (all losses), RSI = 0
    rsi[avg_gain == 0] = 0.0
    # When both are 0 (no change), RSI = 50 (neutral)
    rsi[(avg_gain == 0) & (avg_loss == 0)] = 50.0
    
    return rsi


def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
    """
    Calculate Simple Moving Average (SMA).
    
    SMA is the average of the last 'period' values.
    
    Args:
        prices: Series of price data (typically close prices)
        period: Window size for moving average
    
    Returns:
        Series of SMA values with same index as input
        First 'period-1' values will be NaN (insufficient data for window)
    """
    if len(prices) == 0:
        return pd.Series([], dtype=float)
    
    # Use pandas rolling mean for efficient calculation
    sma = prices.rolling(window=period, min_periods=period).mean()
    
    return sma

