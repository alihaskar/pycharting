"""Tests for DataFrame to columnar array conversion for uPlot."""
import pytest
import pandas as pd
import numpy as np
from src.processing.pivot import to_uplot_format


@pytest.fixture
def simple_ohlc_data():
    """Create simple OHLC DataFrame for testing."""
    dates = pd.date_range("2024-01-01", periods=5, freq="1h")
    return pd.DataFrame({
        "open": [100.0, 101.0, 102.0, 103.0, 104.0],
        "high": [105.0, 106.0, 107.0, 108.0, 109.0],
        "low": [95.0, 96.0, 97.0, 98.0, 99.0],
        "close": [102.0, 103.0, 104.0, 105.0, 106.0],
        "volume": [1000, 1100, 1200, 1300, 1400]
    }, index=dates)


def test_basic_columnar_conversion(simple_ohlc_data):
    """Test basic DataFrame to columnar array conversion."""
    result = to_uplot_format(simple_ohlc_data)
    
    # Should return a list of lists
    assert isinstance(result, list)
    assert len(result) == 6  # timestamp + 5 OHLCV columns
    
    # Each column should be a list
    for col in result:
        assert isinstance(col, list)
        assert len(col) == 5  # 5 data points


def test_column_ordering():
    """Test that columns are ordered correctly: timestamp, open, high, low, close, volume."""
    dates = pd.date_range("2024-01-01", periods=3, freq="1h")
    df = pd.DataFrame({
        "open": [100.0, 101.0, 102.0],
        "high": [105.0, 106.0, 107.0],
        "low": [95.0, 96.0, 97.0],
        "close": [102.0, 103.0, 104.0],
        "volume": [1000, 1100, 1200]
    }, index=dates)
    
    result = to_uplot_format(df)
    
    # First array is timestamps (will test exact values in datetime tests)
    # Second array should be opens
    assert result[1] == [100.0, 101.0, 102.0]
    # Third array should be highs
    assert result[2] == [105.0, 106.0, 107.0]
    # Fourth array should be lows
    assert result[3] == [95.0, 96.0, 97.0]
    # Fifth array should be closes
    assert result[4] == [102.0, 103.0, 104.0]
    # Sixth array should be volumes
    assert result[5] == [1000, 1100, 1200]


def test_handles_indicators():
    """Test that additional indicator columns are included after OHLCV."""
    dates = pd.date_range("2024-01-01", periods=3, freq="1h")
    df = pd.DataFrame({
        "open": [100.0, 101.0, 102.0],
        "high": [105.0, 106.0, 107.0],
        "low": [95.0, 96.0, 97.0],
        "close": [102.0, 103.0, 104.0],
        "volume": [1000, 1100, 1200],
        "rsi": [45.0, 50.0, 55.0],
        "sma_20": [100.5, 101.0, 101.5]
    }, index=dates)
    
    result = to_uplot_format(df)
    
    # Should have 8 columns: timestamp + 5 OHLCV + 2 indicators
    assert len(result) == 8
    
    # RSI column (6th position, 0-indexed)
    assert result[6] == [45.0, 50.0, 55.0]
    
    # SMA column (7th position, 0-indexed)
    assert result[7] == [100.5, 101.0, 101.5]


def test_array_length_consistency():
    """Test that all arrays have the same length."""
    dates = pd.date_range("2024-01-01", periods=10, freq="1h")
    df = pd.DataFrame({
        "open": np.random.uniform(100, 110, 10),
        "high": np.random.uniform(110, 120, 10),
        "low": np.random.uniform(90, 100, 10),
        "close": np.random.uniform(100, 110, 10),
        "volume": np.random.randint(1000, 2000, 10)
    }, index=dates)
    
    result = to_uplot_format(df)
    
    # All arrays should have same length
    lengths = [len(col) for col in result]
    assert len(set(lengths)) == 1  # All lengths should be equal
    assert lengths[0] == 10


def test_preserves_data_types():
    """Test that numeric data types are preserved."""
    dates = pd.date_range("2024-01-01", periods=3, freq="1h")
    df = pd.DataFrame({
        "open": [100.5, 101.7, 102.3],
        "high": [105.2, 106.8, 107.1],
        "low": [95.1, 96.4, 97.9],
        "close": [102.6, 103.2, 104.8],
        "volume": [1000, 1100, 1200]
    }, index=dates)
    
    result = to_uplot_format(df)
    
    # Check that floats are preserved
    assert all(isinstance(x, float) for x in result[1])  # opens
    # Check that integers/floats for volume
    assert all(isinstance(x, (int, float)) for x in result[5])  # volumes


def test_empty_dataframe():
    """Test handling of empty DataFrame."""
    df = pd.DataFrame({
        "open": [],
        "high": [],
        "low": [],
        "close": [],
        "volume": []
    })
    df.index = pd.DatetimeIndex([])
    
    result = to_uplot_format(df)
    
    # Should return empty arrays
    assert len(result) == 6
    assert all(len(col) == 0 for col in result)


def test_single_row_dataframe():
    """Test handling of single-row DataFrame."""
    dates = pd.date_range("2024-01-01", periods=1, freq="1h")
    df = pd.DataFrame({
        "open": [100.0],
        "high": [105.0],
        "low": [95.0],
        "close": [102.0],
        "volume": [1000]
    }, index=dates)
    
    result = to_uplot_format(df)
    
    # Should handle single row
    assert len(result) == 6
    assert all(len(col) == 1 for col in result)


def test_maintains_chronological_order():
    """Test that data maintains chronological order from DataFrame."""
    dates = pd.date_range("2024-01-01", periods=5, freq="1h")
    df = pd.DataFrame({
        "open": [100.0, 101.0, 102.0, 103.0, 104.0],
        "high": [105.0, 106.0, 107.0, 108.0, 109.0],
        "low": [95.0, 96.0, 97.0, 98.0, 99.0],
        "close": [102.0, 103.0, 104.0, 105.0, 106.0],
        "volume": [1000, 1100, 1200, 1300, 1400]
    }, index=dates)
    
    result = to_uplot_format(df)
    
    # Verify chronological order in open prices
    assert result[1] == [100.0, 101.0, 102.0, 103.0, 104.0]


def test_requires_datetime_index():
    """Test that function requires DatetimeIndex."""
    df = pd.DataFrame({
        "open": [100.0, 101.0],
        "high": [105.0, 106.0],
        "low": [95.0, 96.0],
        "close": [102.0, 103.0],
        "volume": [1000, 1100]
    })
    # Default index is RangeIndex, not DatetimeIndex
    
    with pytest.raises(ValueError, match="DatetimeIndex"):
        to_uplot_format(df)


def test_requires_ohlcv_columns():
    """Test that function validates required OHLCV columns."""
    dates = pd.date_range("2024-01-01", periods=3, freq="1h")
    df = pd.DataFrame({
        "open": [100.0, 101.0, 102.0],
        "high": [105.0, 106.0, 107.0],
        # Missing low, close, volume
    }, index=dates)
    
    with pytest.raises(ValueError, match="required.*columns"):
        to_uplot_format(df)

