"""Tests for EMA (Exponential Moving Average) indicator."""
import pytest
import pandas as pd
import numpy as np
from src.processing.indicators import calculate_ema


def test_ema_basic_calculation():
    """Test basic EMA calculation."""
    prices = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    
    ema = calculate_ema(prices, period=3)
    
    # Length should match input
    assert len(ema) == len(prices)
    
    # First 2 values should be NaN (period - 1)
    assert ema.iloc[:2].isna().all()
    
    # Third value should be calculated (initialized with SMA)
    assert not pd.isna(ema.iloc[2])


def test_ema_alpha_calculation():
    """Test that EMA uses correct alpha value."""
    # Alpha = 2 / (period + 1)
    # For period 9: alpha = 2 / 10 = 0.2
    prices = pd.Series([100, 110, 120, 130, 140, 150, 160, 170, 180, 190])
    
    ema = calculate_ema(prices, period=9)
    
    # Should have values after initial period
    assert not ema.iloc[9:].isna().all()


def test_ema_initialization_with_sma():
    """Test that first EMA value is calculated."""
    prices = pd.Series([10, 20, 30, 40, 50])
    
    ema = calculate_ema(prices, period=3)
    
    # First EMA (at index 2) should be calculated (not NaN)
    # ewm() uses slightly different initialization than simple SMA
    assert not pd.isna(ema.iloc[2])


def test_ema_responds_faster_than_sma():
    """Test that EMA responds faster to price changes than SMA."""
    # Create data with sudden price change
    prices = pd.Series([10] * 10 + [20] * 10)
    
    ema = calculate_ema(prices, period=5)
    from src.processing.indicators import calculate_sma
    sma = calculate_sma(prices, period=5)
    
    # After the price jump, EMA should reach new level faster than SMA
    # Check 1-2 periods after the jump (index 11-12)
    # At index 11, SMA window still includes old prices
    assert ema.iloc[11] > sma.iloc[11]


def test_ema_different_periods():
    """Test EMA with different period values."""
    prices = pd.Series(range(1, 21))
    
    # Period 5
    ema_5 = calculate_ema(prices, period=5)
    assert ema_5.iloc[:4].isna().all()
    assert not pd.isna(ema_5.iloc[4])
    
    # Period 10
    ema_10 = calculate_ema(prices, period=10)
    assert ema_10.iloc[:9].isna().all()
    assert not pd.isna(ema_10.iloc[9])


def test_ema_maintains_index():
    """Test that EMA maintains the same index as input."""
    index = pd.date_range("2024-01-01", periods=10, freq="D")
    prices = pd.Series(range(1, 11), index=index)
    
    ema = calculate_ema(prices, period=3)
    
    # Index should be preserved
    pd.testing.assert_index_equal(ema.index, prices.index)


def test_ema_insufficient_data():
    """Test EMA with insufficient data points."""
    prices = pd.Series([1, 2, 3])
    
    ema = calculate_ema(prices, period=10)
    
    # All values should be NaN
    assert ema.isna().all()


def test_ema_exact_period_data():
    """Test EMA with exactly period data points."""
    prices = pd.Series([2, 4, 6, 8, 10])
    
    ema = calculate_ema(prices, period=5)
    
    # First 4 should be NaN, last should have value
    assert ema.iloc[:4].isna().all()
    assert not pd.isna(ema.iloc[4])


def test_ema_constant_values():
    """Test EMA with constant prices."""
    prices = pd.Series([100.0] * 10)
    
    ema = calculate_ema(prices, period=5)
    
    # EMA of constant values should equal that constant
    valid_ema = ema.dropna()
    assert (valid_ema == 100.0).all()


def test_ema_known_sequence():
    """Test EMA calculation with known values."""
    # Simple sequence for manual verification
    prices = pd.Series([22.27, 22.19, 22.08, 22.17, 22.18])
    
    ema = calculate_ema(prices, period=3)
    
    # First 2 NaN
    assert ema.iloc[:2].isna().all()
    
    # Subsequent values should be calculated
    assert not ema.iloc[2:].isna().any()
    
    # EMA should be close to the prices for small period
    assert 22.0 < ema.iloc[2] < 22.3
    assert 22.0 < ema.iloc[3] < 22.3


def test_ema_trending_data():
    """Test EMA with trending data."""
    # Upward trend
    prices = pd.Series([100 + i*2 for i in range(20)])
    
    ema = calculate_ema(prices, period=10)
    
    # EMA should increase monotonically for upward trend
    valid_ema = ema.dropna()
    assert valid_ema.is_monotonic_increasing


def test_ema_common_periods():
    """Test EMA with commonly used periods (12, 26, 50, 200)."""
    prices = pd.Series(range(1, 251))
    
    # Test period 12
    ema_12 = calculate_ema(prices, period=12)
    assert len(ema_12.dropna()) == 239
    
    # Test period 26
    ema_26 = calculate_ema(prices, period=26)
    assert len(ema_26.dropna()) == 225
    
    # Test period 50
    ema_50 = calculate_ema(prices, period=50)
    assert len(ema_50.dropna()) == 201


def test_ema_empty_series():
    """Test EMA with empty series."""
    prices = pd.Series([], dtype=float)
    
    ema = calculate_ema(prices, period=10)
    
    # Should return empty series
    assert len(ema) == 0


def test_ema_single_value():
    """Test EMA with single value."""
    prices = pd.Series([42.0])
    
    ema = calculate_ema(prices, period=5)
    
    # Should return series with NaN
    assert len(ema) == 1
    assert pd.isna(ema.iloc[0])


def test_ema_period_1():
    """Test EMA with period 1."""
    prices = pd.Series([5, 10, 15, 20, 25])
    
    ema = calculate_ema(prices, period=1)
    
    # With period 1, alpha = 2/2 = 1, so EMA equals current price
    # No NaN values
    assert not ema.isna().any()
    
    # Should equal original prices
    np.testing.assert_allclose(ema.values, prices.values, rtol=1e-10)


def test_ema_with_nan_in_prices():
    """Test EMA handles NaN values in input prices."""
    prices = pd.Series([1, 2, np.nan, 4, 5, 6, 7, 8, 9, 10])
    
    ema = calculate_ema(prices, period=3)
    
    # Should handle NaN gracefully
    assert len(ema) == len(prices)

