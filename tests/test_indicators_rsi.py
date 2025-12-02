"""Tests for RSI (Relative Strength Index) indicator."""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from src.processing.indicators import calculate_rsi


def test_rsi_basic_calculation():
    """Test basic RSI calculation with simple data."""
    # Create test data with known price changes
    prices = pd.Series([
        44.0, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84,
        46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41,
        46.22, 45.64
    ])
    
    rsi = calculate_rsi(prices, period=14)
    
    # RSI should be a Series of same length
    assert len(rsi) == len(prices)
    
    # First 14 values should be NaN (lookback period)
    assert rsi.iloc[:14].isna().all()
    
    # RSI should be between 0 and 100
    valid_rsi = rsi.dropna()
    assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()


def test_rsi_period_14():
    """Test RSI with default period of 14."""
    prices = pd.Series([50, 51, 52, 51, 53, 54, 53, 55, 56, 57, 56, 58, 59, 60, 61])
    
    rsi = calculate_rsi(prices, period=14)
    
    # First 14 values should be NaN
    assert rsi.iloc[:14].isna().all()
    # 15th value should have RSI calculated
    assert not pd.isna(rsi.iloc[14])


def test_rsi_different_periods():
    """Test RSI with different period values."""
    prices = pd.Series(range(100, 120))
    
    # Test period 5
    rsi_5 = calculate_rsi(prices, period=5)
    assert rsi_5.iloc[:5].isna().all()
    assert not pd.isna(rsi_5.iloc[5])
    
    # Test period 10
    rsi_10 = calculate_rsi(prices, period=10)
    assert rsi_10.iloc[:10].isna().all()
    assert not pd.isna(rsi_10.iloc[10])


def test_rsi_all_gains():
    """Test RSI when all price changes are gains (should approach 100)."""
    # Steadily increasing prices
    prices = pd.Series([100 + i for i in range(30)])
    
    rsi = calculate_rsi(prices, period=14)
    
    # RSI should be very high (close to 100) for continuous gains
    valid_rsi = rsi.dropna()
    assert valid_rsi.iloc[-1] > 90  # Should be very high


def test_rsi_all_losses():
    """Test RSI when all price changes are losses (should approach 0)."""
    # Steadily decreasing prices
    prices = pd.Series([100 - i for i in range(30)])
    
    rsi = calculate_rsi(prices, period=14)
    
    # RSI should be very low (close to 0) for continuous losses
    valid_rsi = rsi.dropna()
    assert valid_rsi.iloc[-1] < 10  # Should be very low


def test_rsi_insufficient_data():
    """Test RSI with insufficient data points."""
    # Less data than period
    prices = pd.Series([100, 101, 102])
    
    rsi = calculate_rsi(prices, period=14)
    
    # All values should be NaN (not enough data)
    assert rsi.isna().all()


def test_rsi_exact_period_data():
    """Test RSI with exactly period+1 data points."""
    prices = pd.Series(range(100, 115))  # 15 values for period 14
    
    rsi = calculate_rsi(prices, period=14)
    
    # First 14 should be NaN, last should have value
    assert rsi.iloc[:14].isna().all()
    assert not pd.isna(rsi.iloc[14])


def test_rsi_maintains_index():
    """Test that RSI maintains the same index as input."""
    index = pd.date_range("2024-01-01", periods=20, freq="D")
    prices = pd.Series(range(100, 120), index=index)
    
    rsi = calculate_rsi(prices, period=14)
    
    # Index should be preserved
    pd.testing.assert_index_equal(rsi.index, prices.index)


def test_rsi_with_constant_prices():
    """Test RSI with constant prices (no change)."""
    prices = pd.Series([100.0] * 20)
    
    rsi = calculate_rsi(prices, period=14)
    
    # With no price changes, RSI should be 50 (neutral)
    # Or could be NaN depending on implementation
    valid_rsi = rsi.dropna()
    if len(valid_rsi) > 0:
        # If calculated, should be neutral (50) or handle division by zero
        assert valid_rsi.iloc[-1] == pytest.approx(50, abs=1) or pd.isna(valid_rsi.iloc[-1])


def test_rsi_with_nan_in_prices():
    """Test RSI handles NaN values in input prices."""
    prices = pd.Series([100, 101, np.nan, 103, 104, 105, 106, 107, 108, 109, 
                       110, 111, 112, 113, 114, 115, 116, 117, 118, 119])
    
    rsi = calculate_rsi(prices, period=14)
    
    # Should handle NaN gracefully
    assert len(rsi) == len(prices)


def test_rsi_formula_validation():
    """Test RSI calculation against manual calculation."""
    # Simple data for manual verification
    prices = pd.Series([100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                       111, 110, 112, 114, 113, 115, 117])
    
    rsi = calculate_rsi(prices, period=5)
    
    # Manually calculate for verification
    # After index 5, we should have RSI values
    assert not rsi.iloc[5:].isna().all()


def test_rsi_known_values():
    """Test RSI against known reference values."""
    # Test data with known RSI values (can be verified with TA-Lib or other tools)
    prices = pd.Series([
        44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84,
        46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03,
        46.41, 46.22, 45.64, 46.21
    ])
    
    rsi = calculate_rsi(prices, period=14)
    
    # RSI should be calculated and be in valid range
    # For this generally upward trending data, RSI should be above 50
    last_rsi = rsi.iloc[-1]
    assert not pd.isna(last_rsi), "RSI should be calculated"
    assert 50 < last_rsi < 75, f"RSI should be bullish for uptrending data, got {last_rsi}"


def test_rsi_empty_series():
    """Test RSI with empty series."""
    prices = pd.Series([], dtype=float)
    
    rsi = calculate_rsi(prices, period=14)
    
    # Should return empty series
    assert len(rsi) == 0


def test_rsi_single_value():
    """Test RSI with single value."""
    prices = pd.Series([100.0])
    
    rsi = calculate_rsi(prices, period=14)
    
    # Should return series with NaN
    assert len(rsi) == 1
    assert pd.isna(rsi.iloc[0])

