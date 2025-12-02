"""Tests for NaN value handling and JSON serialization in pivot module."""
import pytest
import pandas as pd
import numpy as np
import json
from src.processing.pivot import to_uplot_format, sanitize_nan_values


@pytest.fixture
def data_with_nans():
    """Create DataFrame with various NaN patterns."""
    dates = pd.date_range("2024-01-01", periods=5, freq="1h")
    return pd.DataFrame({
        "open": [100.0, np.nan, 102.0, 103.0, 104.0],
        "high": [105.0, 106.0, np.nan, 108.0, 109.0],
        "low": [95.0, 96.0, 97.0, np.nan, 99.0],
        "close": [102.0, 103.0, 104.0, 105.0, np.nan],
        "volume": [1000, 1100, np.nan, 1300, 1400]
    }, index=dates)


def test_nan_values_converted_to_none():
    """Test that NaN values are converted to None for JSON compatibility."""
    dates = pd.date_range("2024-01-01", periods=3, freq="1h")
    df = pd.DataFrame({
        "open": [100.0, np.nan, 102.0],
        "high": [105.0, 106.0, 107.0],
        "low": [95.0, 96.0, 97.0],
        "close": [102.0, 103.0, 104.0],
        "volume": [1000, 1100, 1200]
    }, index=dates)
    
    result = to_uplot_format(df)
    
    # Second value in open array should be None
    assert result[1][1] is None


def test_json_serializable_output(data_with_nans):
    """Test that output can be serialized to JSON."""
    result = to_uplot_format(data_with_nans)
    
    # Should be able to convert to JSON without errors
    json_str = json.dumps(result)
    
    # Should be able to parse back
    parsed = json.loads(json_str)
    
    # Verify structure is preserved
    assert len(parsed) == 6  # timestamp + 5 OHLCV columns
    assert len(parsed[0]) == 5  # 5 data points


def test_all_nan_column_handling():
    """Test handling of columns that are entirely NaN."""
    dates = pd.date_range("2024-01-01", periods=3, freq="1h")
    df = pd.DataFrame({
        "open": [100.0, 101.0, 102.0],
        "high": [105.0, 106.0, 107.0],
        "low": [95.0, 96.0, 97.0],
        "close": [102.0, 103.0, 104.0],
        "volume": [1000, 1100, 1200],
        "indicator": [np.nan, np.nan, np.nan]  # All NaN
    }, index=dates)
    
    result = to_uplot_format(df)
    
    # Should still include the column with all None values
    assert len(result) == 7
    assert result[6] == [None, None, None]


def test_mixed_nan_patterns(data_with_nans):
    """Test various NaN patterns across different columns."""
    result = to_uplot_format(data_with_nans)
    
    # Verify NaN positions are converted to None
    assert result[1][1] is None  # open[1] is NaN
    assert result[2][2] is None  # high[2] is NaN
    assert result[3][3] is None  # low[3] is NaN
    assert result[4][4] is None  # close[4] is NaN
    assert result[5][2] is None  # volume[2] is NaN


def test_sanitize_nan_values_function():
    """Test the sanitize_nan_values helper function."""
    values = [1.0, np.nan, 3.0, np.nan, 5.0]
    result = sanitize_nan_values(values)
    
    # NaN should be converted to None
    assert result == [1.0, None, 3.0, None, 5.0]


def test_sanitize_handles_various_nan_types():
    """Test that sanitization handles different NaN representations."""
    values = [
        1.0,
        np.nan,           # numpy NaN
        float('nan'),     # Python NaN
        pd.NA,            # pandas NA
        3.0
    ]
    result = sanitize_nan_values(values)
    
    # All NaN types should be converted to None
    assert result[0] == 1.0
    assert result[1] is None
    assert result[2] is None
    assert result[3] is None
    assert result[4] == 3.0


def test_numpy_array_to_list_conversion():
    """Test that numpy arrays are properly converted to lists."""
    dates = pd.date_range("2024-01-01", periods=3, freq="1h")
    df = pd.DataFrame({
        "open": np.array([100.0, 101.0, 102.0]),
        "high": np.array([105.0, 106.0, 107.0]),
        "low": np.array([95.0, 96.0, 97.0]),
        "close": np.array([102.0, 103.0, 104.0]),
        "volume": np.array([1000, 1100, 1200])
    }, index=dates)
    
    result = to_uplot_format(df)
    
    # All columns should be lists, not numpy arrays
    for col in result:
        assert isinstance(col, list)


def test_preserves_non_nan_values():
    """Test that non-NaN values are preserved correctly."""
    dates = pd.date_range("2024-01-01", periods=3, freq="1h")
    df = pd.DataFrame({
        "open": [100.5, np.nan, 102.7],
        "high": [105.2, 106.8, 107.1],
        "low": [95.1, 96.4, 97.9],
        "close": [102.6, 103.2, 104.8],
        "volume": [1000, 1100, 1200]
    }, index=dates)
    
    result = to_uplot_format(df)
    
    # Non-NaN values should be preserved exactly
    assert result[1][0] == 100.5
    assert result[1][2] == 102.7
    assert result[2] == [105.2, 106.8, 107.1]


def test_empty_dataframe_json_serialization():
    """Test JSON serialization of empty DataFrame."""
    df = pd.DataFrame({
        "open": [],
        "high": [],
        "low": [],
        "close": [],
        "volume": []
    })
    df.index = pd.DatetimeIndex([])
    
    result = to_uplot_format(df)
    
    # Should be JSON serializable
    json_str = json.dumps(result)
    parsed = json.loads(json_str)
    
    assert len(parsed) == 6
    assert all(len(col) == 0 for col in parsed)


def test_inf_values_handling():
    """Test handling of infinity values."""
    dates = pd.date_range("2024-01-01", periods=3, freq="1h")
    df = pd.DataFrame({
        "open": [100.0, np.inf, 102.0],
        "high": [105.0, -np.inf, 107.0],
        "low": [95.0, 96.0, 97.0],
        "close": [102.0, 103.0, 104.0],
        "volume": [1000, 1100, 1200]
    }, index=dates)
    
    result = to_uplot_format(df)
    
    # Infinity values should be converted to None for JSON compatibility
    assert result[1][1] is None  # np.inf
    assert result[2][1] is None  # -np.inf


def test_indicators_with_nans():
    """Test that indicators with NaN values are handled correctly."""
    dates = pd.date_range("2024-01-01", periods=5, freq="1h")
    df = pd.DataFrame({
        "open": [100.0, 101.0, 102.0, 103.0, 104.0],
        "high": [105.0, 106.0, 107.0, 108.0, 109.0],
        "low": [95.0, 96.0, 97.0, 98.0, 99.0],
        "close": [102.0, 103.0, 104.0, 105.0, 106.0],
        "volume": [1000, 1100, 1200, 1300, 1400],
        "sma_20": [np.nan, np.nan, np.nan, 102.5, 103.0],  # NaN at start
        "rsi": [45.0, 50.0, 55.0, np.nan, 60.0]  # NaN in middle
    }, index=dates)
    
    result = to_uplot_format(df)
    
    # Indicators are sorted alphabetically: rsi (index 6), sma_20 (index 7)
    assert result[6][3] is None  # rsi has NaN in middle
    assert result[7][:3] == [None, None, None]  # sma_20 starts with NaN
    assert result[7][3] == 102.5


def test_json_roundtrip_preserves_structure():
    """Test that JSON roundtrip preserves data structure."""
    dates = pd.date_range("2024-01-01", periods=3, freq="1h")
    df = pd.DataFrame({
        "open": [100.0, np.nan, 102.0],
        "high": [105.0, 106.0, 107.0],
        "low": [95.0, 96.0, 97.0],
        "close": [102.0, 103.0, 104.0],
        "volume": [1000, 1100, 1200]
    }, index=dates)
    
    result = to_uplot_format(df)
    
    # Convert to JSON and back
    json_str = json.dumps(result)
    parsed = json.loads(json_str)
    
    # Verify structure
    assert len(parsed) == len(result)
    assert all(len(parsed[i]) == len(result[i]) for i in range(len(result)))
    
    # Verify None values are preserved
    assert parsed[1][1] is None

