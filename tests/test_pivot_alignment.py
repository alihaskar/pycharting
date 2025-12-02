"""Tests for data alignment verification in pivot module."""
import pytest
import pandas as pd
import numpy as np
from charting.processing.pivot import (
    to_uplot_format,
    verify_data_alignment,
    DataAlignmentError
)


@pytest.fixture
def aligned_data():
    """Create properly aligned OHLC DataFrame."""
    dates = pd.date_range("2024-01-01", periods=5, freq="1h")
    return pd.DataFrame({
        "open": [100.0, 101.0, 102.0, 103.0, 104.0],
        "high": [105.0, 106.0, 107.0, 108.0, 109.0],
        "low": [95.0, 96.0, 97.0, 98.0, 99.0],
        "close": [102.0, 103.0, 104.0, 105.0, 106.0],
        "volume": [1000, 1100, 1200, 1300, 1400]
    }, index=dates)


def test_verify_data_alignment_pass(aligned_data):
    """Test that properly aligned data passes verification."""
    result = to_uplot_format(aligned_data)
    
    # Should not raise error
    verify_data_alignment(result)


def test_all_arrays_same_length(aligned_data):
    """Test that all output arrays have the same length."""
    result = to_uplot_format(aligned_data)
    
    lengths = [len(arr) for arr in result]
    
    # All lengths should be equal
    assert len(set(lengths)) == 1
    assert lengths[0] == 5


def test_data_alignment_with_indicators():
    """Test alignment when indicators are present."""
    dates = pd.date_range("2024-01-01", periods=10, freq="1h")
    df = pd.DataFrame({
        "open": np.random.uniform(100, 110, 10),
        "high": np.random.uniform(110, 120, 10),
        "low": np.random.uniform(90, 100, 10),
        "close": np.random.uniform(100, 110, 10),
        "volume": np.random.randint(1000, 2000, 10),
        "sma_20": np.random.uniform(100, 110, 10),
        "rsi": np.random.uniform(30, 70, 10),
        "ema_12": np.random.uniform(100, 110, 10)
    }, index=dates)
    
    result = to_uplot_format(df)
    
    # All arrays should have same length
    verify_data_alignment(result)
    
    # Verify count
    lengths = [len(arr) for arr in result]
    assert all(l == 10 for l in lengths)


def test_timestamps_align_with_ohlc():
    """Test that timestamps align with OHLC data points."""
    dates = pd.date_range("2024-01-01", periods=5, freq="1h")
    df = pd.DataFrame({
        "open": [100.0, 101.0, 102.0, 103.0, 104.0],
        "high": [105.0, 106.0, 107.0, 108.0, 109.0],
        "low": [95.0, 96.0, 97.0, 98.0, 99.0],
        "close": [102.0, 103.0, 104.0, 105.0, 106.0],
        "volume": [1000, 1100, 1200, 1300, 1400]
    }, index=dates)
    
    result = to_uplot_format(df)
    
    # Timestamps (first array) should have same length as data arrays
    assert len(result[0]) == len(result[1])
    assert len(result[0]) == len(result[2])
    assert len(result[0]) == len(result[3])
    assert len(result[0]) == len(result[4])
    assert len(result[0]) == len(result[5])


def test_verify_alignment_function():
    """Test the verify_data_alignment function directly."""
    # Valid data: all same length
    valid_data = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]
    
    # Should not raise error
    verify_data_alignment(valid_data)


def test_verify_alignment_detects_mismatch():
    """Test that misaligned data is detected."""
    # Invalid data: different lengths
    invalid_data = [
        [1, 2, 3],
        [4, 5],      # Too short
        [7, 8, 9]
    ]
    
    with pytest.raises(DataAlignmentError, match="length"):
        verify_data_alignment(invalid_data)


def test_empty_arrays_alignment():
    """Test alignment verification with empty arrays."""
    df = pd.DataFrame({
        "open": [],
        "high": [],
        "low": [],
        "close": [],
        "volume": []
    })
    df.index = pd.DatetimeIndex([])
    
    result = to_uplot_format(df)
    
    # Should verify even with empty arrays
    verify_data_alignment(result)
    
    # All should be length 0
    assert all(len(arr) == 0 for arr in result)


def test_single_point_alignment():
    """Test alignment with single data point."""
    dates = pd.date_range("2024-01-01", periods=1, freq="1h")
    df = pd.DataFrame({
        "open": [100.0],
        "high": [105.0],
        "low": [95.0],
        "close": [102.0],
        "volume": [1000]
    }, index=dates)
    
    result = to_uplot_format(df)
    
    verify_data_alignment(result)
    assert all(len(arr) == 1 for arr in result)


def test_alignment_with_nan_values():
    """Test that NaN values don't affect alignment."""
    dates = pd.date_range("2024-01-01", periods=5, freq="1h")
    df = pd.DataFrame({
        "open": [100.0, np.nan, 102.0, 103.0, 104.0],
        "high": [105.0, 106.0, np.nan, 108.0, 109.0],
        "low": [95.0, 96.0, 97.0, np.nan, 99.0],
        "close": [102.0, 103.0, 104.0, 105.0, np.nan],
        "volume": [1000, 1100, np.nan, 1300, 1400]
    }, index=dates)
    
    result = to_uplot_format(df)
    
    # Alignment should be maintained despite NaN values
    verify_data_alignment(result)
    assert all(len(arr) == 5 for arr in result)


def test_large_dataset_alignment():
    """Test alignment with large dataset."""
    dates = pd.date_range("2024-01-01", periods=1000, freq="1min")
    df = pd.DataFrame({
        "open": np.random.uniform(100, 110, 1000),
        "high": np.random.uniform(110, 120, 1000),
        "low": np.random.uniform(90, 100, 1000),
        "close": np.random.uniform(100, 110, 1000),
        "volume": np.random.randint(1000, 2000, 1000)
    }, index=dates)
    
    result = to_uplot_format(df)
    
    verify_data_alignment(result)
    assert all(len(arr) == 1000 for arr in result)


def test_alignment_error_message_clarity():
    """Test that alignment errors provide clear information."""
    invalid_data = [
        [1, 2, 3, 4, 5],     # Length 5
        [1, 2, 3],           # Length 3
        [1, 2, 3, 4, 5, 6]   # Length 6
    ]
    
    with pytest.raises(DataAlignmentError) as exc_info:
        verify_data_alignment(invalid_data)
    
    # Error message should mention lengths
    assert "length" in str(exc_info.value).lower()


def test_alignment_preserves_data_integrity():
    """Test that alignment verification doesn't modify data."""
    dates = pd.date_range("2024-01-01", periods=3, freq="1h")
    df = pd.DataFrame({
        "open": [100.0, 101.0, 102.0],
        "high": [105.0, 106.0, 107.0],
        "low": [95.0, 96.0, 97.0],
        "close": [102.0, 103.0, 104.0],
        "volume": [1000, 1100, 1200]
    }, index=dates)
    
    result = to_uplot_format(df)
    
    # Store original data
    original = [arr.copy() for arr in result]
    
    # Verify alignment
    verify_data_alignment(result)
    
    # Data should be unchanged
    for i, arr in enumerate(result):
        assert arr == original[i]


def test_automatic_alignment_verification():
    """Test that to_uplot_format automatically verifies alignment."""
    dates = pd.date_range("2024-01-01", periods=5, freq="1h")
    df = pd.DataFrame({
        "open": [100.0, 101.0, 102.0, 103.0, 104.0],
        "high": [105.0, 106.0, 107.0, 108.0, 109.0],
        "low": [95.0, 96.0, 97.0, 98.0, 99.0],
        "close": [102.0, 103.0, 104.0, 105.0, 106.0],
        "volume": [1000, 1100, 1200, 1300, 1400]
    }, index=dates)
    
    # Should complete without errors
    result = to_uplot_format(df)
    
    # Verify it's properly aligned
    lengths = [len(arr) for arr in result]
    assert len(set(lengths)) == 1

