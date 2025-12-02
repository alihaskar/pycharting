"""Tests for SMA (Simple Moving Average) indicator."""
import pytest
import pandas as pd
import numpy as np
from charting.processing.indicators import calculate_sma


def test_sma_basic_calculation():
    """Test basic SMA calculation."""
    prices = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    
    sma = calculate_sma(prices, period=3)
    
    # Length should match input
    assert len(sma) == len(prices)
    
    # First 2 values should be NaN (period - 1)
    assert sma.iloc[:2].isna().all()
    
    # Third value should be average of first 3
    assert sma.iloc[2] == pytest.approx(2.0)  # (1+2+3)/3
    
    # Fourth value should be average of values 2-4
    assert sma.iloc[3] == pytest.approx(3.0)  # (2+3+4)/3


def test_sma_known_values():
    """Test SMA with known calculated values."""
    prices = pd.Series([10, 20, 30, 40, 50])
    
    sma = calculate_sma(prices, period=3)
    
    # First 2 should be NaN
    assert pd.isna(sma.iloc[0])
    assert pd.isna(sma.iloc[1])
    
    # Index 2: (10+20+30)/3 = 20
    assert sma.iloc[2] == pytest.approx(20.0)
    
    # Index 3: (20+30+40)/3 = 30
    assert sma.iloc[3] == pytest.approx(30.0)
    
    # Index 4: (30+40+50)/3 = 40
    assert sma.iloc[4] == pytest.approx(40.0)


def test_sma_different_periods():
    """Test SMA with different period values."""
    prices = pd.Series(range(1, 21))  # 1 to 20
    
    # Period 5
    sma_5 = calculate_sma(prices, period=5)
    assert sma_5.iloc[:4].isna().all()
    assert not pd.isna(sma_5.iloc[4])
    assert sma_5.iloc[4] == pytest.approx(3.0)  # (1+2+3+4+5)/5
    
    # Period 10
    sma_10 = calculate_sma(prices, period=10)
    assert sma_10.iloc[:9].isna().all()
    assert not pd.isna(sma_10.iloc[9])
    assert sma_10.iloc[9] == pytest.approx(5.5)  # (1+2+...+10)/10


def test_sma_period_1():
    """Test SMA with period 1 (should return original values)."""
    prices = pd.Series([5, 10, 15, 20, 25])
    
    sma = calculate_sma(prices, period=1)
    
    # No NaN values
    assert not sma.isna().any()
    
    # Should equal original prices (values, not dtype)
    pd.testing.assert_series_equal(sma, prices.astype(float), check_names=False)


def test_sma_maintains_index():
    """Test that SMA maintains the same index as input."""
    index = pd.date_range("2024-01-01", periods=10, freq="D")
    prices = pd.Series(range(1, 11), index=index)
    
    sma = calculate_sma(prices, period=3)
    
    # Index should be preserved
    pd.testing.assert_index_equal(sma.index, prices.index)


def test_sma_insufficient_data():
    """Test SMA with insufficient data points."""
    prices = pd.Series([1, 2, 3])
    
    sma = calculate_sma(prices, period=10)
    
    # All values should be NaN
    assert sma.isna().all()


def test_sma_exact_period_data():
    """Test SMA with exactly period data points."""
    prices = pd.Series([2, 4, 6, 8, 10])
    
    sma = calculate_sma(prices, period=5)
    
    # First 4 should be NaN, last should have value
    assert sma.iloc[:4].isna().all()
    assert sma.iloc[4] == pytest.approx(6.0)  # (2+4+6+8+10)/5


def test_sma_with_nan_in_prices():
    """Test SMA handles NaN values in input prices."""
    prices = pd.Series([1, 2, np.nan, 4, 5, 6, 7, 8, 9, 10])
    
    sma = calculate_sma(prices, period=3)
    
    # Should handle NaN gracefully
    assert len(sma) == len(prices)
    
    # Values around NaN might be affected
    # This depends on how we want to handle NaN - skip or propagate


def test_sma_constant_values():
    """Test SMA with constant prices."""
    prices = pd.Series([100.0] * 10)
    
    sma = calculate_sma(prices, period=5)
    
    # SMA of constant values should equal that constant
    valid_sma = sma.dropna()
    assert (valid_sma == 100.0).all()


def test_sma_common_periods():
    """Test SMA with commonly used periods (5, 10, 20, 50, 200)."""
    prices = pd.Series(range(1, 251))  # 250 values
    
    # Test period 5
    sma_5 = calculate_sma(prices, period=5)
    assert len(sma_5.dropna()) == 246
    
    # Test period 20
    sma_20 = calculate_sma(prices, period=20)
    assert len(sma_20.dropna()) == 231
    
    # Test period 50
    sma_50 = calculate_sma(prices, period=50)
    assert len(sma_50.dropna()) == 201
    
    # Test period 200
    sma_200 = calculate_sma(prices, period=200)
    assert len(sma_200.dropna()) == 51


def test_sma_empty_series():
    """Test SMA with empty series."""
    prices = pd.Series([], dtype=float)
    
    sma = calculate_sma(prices, period=10)
    
    # Should return empty series
    assert len(sma) == 0


def test_sma_single_value():
    """Test SMA with single value."""
    prices = pd.Series([42.0])
    
    sma = calculate_sma(prices, period=5)
    
    # Should return series with NaN
    assert len(sma) == 1
    assert pd.isna(sma.iloc[0])


def test_sma_preserves_dtype():
    """Test that SMA preserves numeric dtype."""
    prices = pd.Series([1.5, 2.5, 3.5, 4.5, 5.5])
    
    sma = calculate_sma(prices, period=3)
    
    # Should be numeric type
    assert pd.api.types.is_numeric_dtype(sma)

