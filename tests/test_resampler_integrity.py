"""Tests for data integrity verification during resampling."""
import pytest
import pandas as pd
import numpy as np
from charting.processing.resampler import (
    verify_volume_conservation,
    verify_ohlc_relationships,
    verify_timestamp_continuity,
    validate_resampled_data,
    DataIntegrityError
)


@pytest.fixture
def valid_ohlc_data():
    """Create valid OHLC data for testing."""
    dates = pd.date_range("2024-01-01", periods=10, freq="1h")
    return pd.DataFrame({
        "open": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
        "high": [105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0, 112.0, 113.0, 114.0],
        "low": [95.0, 96.0, 97.0, 98.0, 99.0, 100.0, 101.0, 102.0, 103.0, 104.0],
        "close": [102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0],
        "volume": [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]
    }, index=dates)


def test_verify_volume_conservation_pass(valid_ohlc_data):
    """Test volume conservation verification with matching volumes."""
    original_volume = valid_ohlc_data["volume"].sum()
    
    # Create resampled data with same total volume
    resampled = pd.DataFrame({
        "open": [100.0, 105.0],
        "high": [109.0, 114.0],
        "low": [95.0, 100.0],
        "close": [104.0, 111.0],
        "volume": [6500, 8000]  # Sum = 14500 = original
    }, index=pd.date_range("2024-01-01", periods=2, freq="5h"))
    
    # Should not raise error
    verify_volume_conservation(valid_ohlc_data, resampled)


def test_verify_volume_conservation_fail():
    """Test volume conservation verification with mismatched volumes."""
    original = pd.DataFrame({
        "volume": [1000, 2000, 3000]
    }, index=pd.date_range("2024-01-01", periods=3, freq="1h"))
    
    resampled = pd.DataFrame({
        "volume": [5000]  # Should be 6000
    }, index=pd.date_range("2024-01-01", periods=1, freq="3h"))
    
    with pytest.raises(DataIntegrityError, match="Volume conservation"):
        verify_volume_conservation(original, resampled)


def test_verify_ohlc_relationships_valid(valid_ohlc_data):
    """Test OHLC relationship verification with valid data."""
    # Should not raise error
    verify_ohlc_relationships(valid_ohlc_data)


def test_verify_ohlc_relationships_high_too_low():
    """Test detection of high price below open/close."""
    invalid_data = pd.DataFrame({
        "open": [100.0],
        "high": [99.0],   # Invalid: high < open
        "low": [95.0],
        "close": [98.0],
        "volume": [1000]
    }, index=pd.date_range("2024-01-01", periods=1, freq="1h"))
    
    with pytest.raises(DataIntegrityError, match="High.*below"):
        verify_ohlc_relationships(invalid_data)


def test_verify_ohlc_relationships_low_too_high():
    """Test detection of low price above open/close."""
    invalid_data = pd.DataFrame({
        "open": [100.0],
        "high": [105.0],
        "low": [101.0],   # Invalid: low > open
        "close": [98.0],
        "volume": [1000]
    }, index=pd.date_range("2024-01-01", periods=1, freq="1h"))
    
    with pytest.raises(DataIntegrityError, match="Low.*above"):
        verify_ohlc_relationships(invalid_data)


def test_verify_timestamp_continuity_continuous():
    """Test timestamp continuity verification with continuous data."""
    dates = pd.date_range("2024-01-01", periods=10, freq="1h")
    df = pd.DataFrame({
        "close": range(10)
    }, index=dates)
    
    # Should not raise error
    verify_timestamp_continuity(df, expected_freq="1h")


def test_verify_timestamp_continuity_with_gaps():
    """Test timestamp continuity detection with gaps."""
    # Create data with a gap
    dates = pd.DatetimeIndex([
        "2024-01-01 09:00",
        "2024-01-01 10:00",
        "2024-01-01 11:00",
        "2024-01-01 13:00",  # Gap: missing 12:00
        "2024-01-01 14:00"
    ])
    df = pd.DataFrame({
        "close": range(5)
    }, index=dates)
    
    # Should detect gap
    with pytest.raises(DataIntegrityError, match="timestamp.*gap"):
        verify_timestamp_continuity(df, expected_freq="1h")


def test_verify_timestamp_continuity_allows_small_tolerance():
    """Test that small timestamp deviations are tolerated."""
    # Create timestamps with minor drift (seconds)
    dates = pd.DatetimeIndex([
        "2024-01-01 09:00:00",
        "2024-01-01 10:00:02",  # 2 seconds off
        "2024-01-01 11:00:01",  # 1 second off
    ])
    df = pd.DataFrame({
        "close": [100, 101, 102]
    }, index=dates)
    
    # Should pass with tolerance
    verify_timestamp_continuity(df, expected_freq="1h", tolerance_seconds=5)


def test_validate_resampled_data_complete(valid_ohlc_data):
    """Test complete data validation passes for valid data."""
    from charting.processing.resampler import resample_ohlc
    resampled = resample_ohlc(valid_ohlc_data, "2h")
    
    # Should not raise error
    validate_resampled_data(valid_ohlc_data, resampled)


def test_validate_resampled_data_catches_volume_error():
    """Test that validation catches volume conservation errors."""
    original = pd.DataFrame({
        "open": [100.0, 101.0],
        "high": [105.0, 106.0],
        "low": [95.0, 96.0],
        "close": [102.0, 103.0],
        "volume": [1000, 2000]
    }, index=pd.date_range("2024-01-01", periods=2, freq="1h"))
    
    invalid_resampled = pd.DataFrame({
        "open": [100.0],
        "high": [106.0],
        "low": [95.0],
        "close": [103.0],
        "volume": [2000]  # Should be 3000
    }, index=pd.date_range("2024-01-01", periods=1, freq="2h"))
    
    with pytest.raises(DataIntegrityError, match="Volume"):
        validate_resampled_data(original, invalid_resampled)


def test_validate_resampled_data_catches_ohlc_error():
    """Test that validation catches OHLC relationship errors."""
    original = pd.DataFrame({
        "open": [100.0],
        "high": [105.0],
        "low": [95.0],
        "close": [102.0],
        "volume": [1000]
    }, index=pd.date_range("2024-01-01", periods=1, freq="1h"))
    
    invalid_resampled = pd.DataFrame({
        "open": [100.0],
        "high": [90.0],   # Invalid: high < open
        "low": [95.0],
        "close": [102.0],
        "volume": [1000]
    }, index=pd.date_range("2024-01-01", periods=1, freq="1h"))
    
    with pytest.raises(DataIntegrityError):
        validate_resampled_data(original, invalid_resampled)


def test_volume_conservation_tolerance():
    """Test volume conservation with small floating-point tolerance."""
    original = pd.DataFrame({
        "volume": [1000.1, 2000.2, 3000.3]
    }, index=pd.date_range("2024-01-01", periods=3, freq="1h"))
    
    # Resampled with tiny rounding difference
    resampled = pd.DataFrame({
        "volume": [6000.599999]  # Within tolerance
    }, index=pd.date_range("2024-01-01", periods=1, freq="3h"))
    
    # Should pass with tolerance
    verify_volume_conservation(original, resampled, tolerance=0.01)


def test_verify_negative_volume_detected():
    """Test that negative volumes are detected."""
    invalid_data = pd.DataFrame({
        "open": [100.0],
        "high": [105.0],
        "low": [95.0],
        "close": [102.0],
        "volume": [-1000]  # Invalid: negative volume
    }, index=pd.date_range("2024-01-01", periods=1, freq="1h"))
    
    with pytest.raises(DataIntegrityError, match="negative.*volume"):
        verify_ohlc_relationships(invalid_data)


def test_empty_dataframe_validation():
    """Test validation with empty DataFrames."""
    empty_df = pd.DataFrame({
        "open": [],
        "high": [],
        "low": [],
        "close": [],
        "volume": []
    })
    empty_df.index = pd.DatetimeIndex([])
    
    # Should handle gracefully
    validate_resampled_data(empty_df, empty_df)


def test_verify_ohlc_all_rows():
    """Test that all rows are checked for OHLC relationships."""
    # Mix of valid and invalid rows
    data = pd.DataFrame({
        "open": [100.0, 200.0, 300.0],
        "high": [105.0, 205.0, 295.0],  # Last row: high < open (invalid)
        "low": [95.0, 195.0, 285.0],
        "close": [102.0, 202.0, 302.0],
        "volume": [1000, 2000, 3000]
    }, index=pd.date_range("2024-01-01", periods=3, freq="1h"))
    
    with pytest.raises(DataIntegrityError):
        verify_ohlc_relationships(data)


def test_volume_conservation_with_nan():
    """Test volume conservation when data contains NaN."""
    original = pd.DataFrame({
        "volume": [1000, np.nan, 3000]
    }, index=pd.date_range("2024-01-01", periods=3, freq="1h"))
    
    resampled = pd.DataFrame({
        "volume": [4000]  # 1000 + 3000 (NaN excluded)
    }, index=pd.date_range("2024-01-01", periods=1, freq="3h"))
    
    # Should handle NaN by excluding from sum
    verify_volume_conservation(original, resampled)

