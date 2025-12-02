"""Technical indicators calculation module."""
import pandas as pd
import numpy as np
from typing import Union


class IndicatorValidationError(Exception):
    """Custom exception for indicator validation errors."""
    pass


def validate_indicator_input(
    prices: pd.Series,
    period: int,
    indicator_name: str
) -> None:
    """
    Validate input parameters for indicator calculations.
    
    Args:
        prices: Input price series
        period: Lookback period for calculation
        indicator_name: Name of indicator for error messages
    
    Raises:
        IndicatorValidationError: If validation fails
    """
    # Check if prices is None
    if prices is None:
        raise IndicatorValidationError(
            f"{indicator_name}: Input prices cannot be None"
        )
    
    # Check if prices is a pandas Series
    if not isinstance(prices, pd.Series):
        raise IndicatorValidationError(
            f"{indicator_name}: Input must be a pandas Series, got {type(prices).__name__}"
        )
    
    # Check if period is an integer
    if not isinstance(period, (int, np.integer)):
        raise IndicatorValidationError(
            f"{indicator_name}: Period must be an integer, got {type(period).__name__}"
        )
    
    # Check if period is positive
    if period <= 0:
        raise IndicatorValidationError(
            f"{indicator_name}: Period must be positive, got {period}"
        )


def check_sufficient_data(prices: pd.Series, required: int) -> bool:
    """
    Check if there is sufficient data for calculation.
    
    Args:
        prices: Input price series
        required: Minimum number of data points required
    
    Returns:
        True if sufficient data, False otherwise
    """
    if prices is None or len(prices) < required:
        return False
    return True


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
    
    # Use pandas ewm with Wilder's smoothing (alpha = 1/period)
    # This is equivalent to Wilder's smoothing method used in RSI
    # adjust=False gives us the recursive formula
    avg_gain = gains.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    avg_loss = losses.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    
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


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average (EMA).
    
    EMA gives more weight to recent prices using exponential weighting.
    Formula: EMA = (Price * Alpha) + (Previous EMA * (1 - Alpha))
    where Alpha = 2 / (Period + 1)
    
    Uses pandas' optimized ewm() for vectorized calculation.
    
    Args:
        prices: Series of price data (typically close prices)
        period: Period for EMA calculation
    
    Returns:
        Series of EMA values with same index as input
        First 'period-1' values will be NaN (lookback period)
    """
    if len(prices) == 0:
        return pd.Series([], dtype=float)
    
    if len(prices) < period:
        # Not enough data, return all NaN
        return pd.Series([np.nan] * len(prices), index=prices.index)
    
    # Use pandas ewm (exponentially weighted moving average) - vectorized and fast
    # adjust=False gives us the recursive formula we want
    # min_periods=period ensures first period-1 values are NaN
    ema = prices.ewm(span=period, adjust=False, min_periods=period).mean()
    
    return ema


def calculate_indicator(
    prices: pd.Series,
    indicator_type: str,
    params: dict = None
) -> pd.Series:
    """
    Main API function to calculate technical indicators.
    
    Routes to specific indicator implementations based on type.
    
    Args:
        prices: Series of price data (typically close prices)
        indicator_type: Type of indicator ('sma', 'ema', 'rsi')
        params: Dictionary of parameters for the indicator
                - For SMA/EMA/RSI: 'period' (int)
    
    Returns:
        Series of indicator values with same index as input
    
    Raises:
        IndicatorValidationError: If validation fails or indicator type is unknown
    
    Examples:
        >>> prices = pd.Series([100, 102, 101, 103, 105])
        >>> sma = calculate_indicator(prices, 'sma', {'period': 3})
        >>> rsi = calculate_indicator(prices, 'rsi', {'period': 14})
    """
    # Normalize params
    if params is None:
        params = {}
    
    # Normalize indicator type to lowercase
    indicator_type = indicator_type.lower()
    
    # Default periods for indicators
    default_periods = {
        'sma': 20,
        'ema': 20,
        'rsi': 14
    }
    
    # Get period from params or use default
    period = params.get('period', default_periods.get(indicator_type))
    
    # Validate period exists
    if period is None:
        raise IndicatorValidationError(
            f"{indicator_type.upper()}: 'period' parameter is required"
        )
    
    # Route to specific indicator function
    if indicator_type == 'sma':
        validate_indicator_input(prices, period, 'SMA')
        return calculate_sma(prices, period)
    
    elif indicator_type == 'ema':
        validate_indicator_input(prices, period, 'EMA')
        return calculate_ema(prices, period)
    
    elif indicator_type == 'rsi':
        validate_indicator_input(prices, period, 'RSI')
        return calculate_rsi(prices, period)
    
    else:
        raise IndicatorValidationError(
            f"Unknown indicator type: '{indicator_type}'. "
            f"Supported types: sma, ema, rsi"
        )

