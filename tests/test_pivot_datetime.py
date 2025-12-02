"""Tests for DateTime to Unix timestamp conversion in pivot module."""
import pytest
import pandas as pd
import pytz
from datetime import datetime
from charting.processing.pivot import (
    datetime_to_unix_ms,
    datetime_to_unix_seconds,
    to_uplot_format
)


def test_datetime_to_unix_ms_basic():
    """Test basic datetime to Unix milliseconds conversion."""
    dt = pd.Timestamp("2024-01-01 00:00:00", tz="UTC")
    result = datetime_to_unix_ms(dt)
    
    # 2024-01-01 00:00:00 UTC
    expected = int(dt.timestamp() * 1000)
    assert result == expected


def test_datetime_to_unix_seconds_basic():
    """Test basic datetime to Unix seconds conversion."""
    dt = pd.Timestamp("2024-01-01 00:00:00", tz="UTC")
    result = datetime_to_unix_seconds(dt)
    
    expected = int(dt.timestamp())
    assert result == expected


def test_datetime_index_to_unix_ms():
    """Test converting a DatetimeIndex to Unix milliseconds."""
    dates = pd.date_range("2024-01-01", periods=3, freq="1h", tz="UTC")
    df = pd.DataFrame({
        "open": [100.0, 101.0, 102.0],
        "high": [105.0, 106.0, 107.0],
        "low": [95.0, 96.0, 97.0],
        "close": [102.0, 103.0, 104.0],
        "volume": [1000, 1100, 1200]
    }, index=dates)
    
    result = to_uplot_format(df, timestamp_unit="ms")
    
    # First array should be timestamps in milliseconds
    timestamps = result[0]
    assert len(timestamps) == 3
    assert all(isinstance(ts, int) for ts in timestamps)
    
    # Verify they're in milliseconds (13 digits for current timestamps)
    assert all(len(str(ts)) == 13 for ts in timestamps)


def test_datetime_index_to_unix_seconds():
    """Test converting a DatetimeIndex to Unix seconds."""
    dates = pd.date_range("2024-01-01", periods=3, freq="1h", tz="UTC")
    df = pd.DataFrame({
        "open": [100.0, 101.0, 102.0],
        "high": [105.0, 106.0, 107.0],
        "low": [95.0, 96.0, 97.0],
        "close": [102.0, 103.0, 104.0],
        "volume": [1000, 1100, 1200]
    }, index=dates)
    
    result = to_uplot_format(df, timestamp_unit="s")
    
    # First array should be timestamps in seconds
    timestamps = result[0]
    assert len(timestamps) == 3
    assert all(isinstance(ts, int) for ts in timestamps)
    
    # Verify they're in seconds (10 digits for current timestamps)
    assert all(len(str(ts)) == 10 for ts in timestamps)


def test_timestamps_maintain_chronological_order():
    """Test that timestamps maintain chronological order."""
    dates = pd.date_range("2024-01-01", periods=5, freq="1h", tz="UTC")
    df = pd.DataFrame({
        "open": [100.0, 101.0, 102.0, 103.0, 104.0],
        "high": [105.0, 106.0, 107.0, 108.0, 109.0],
        "low": [95.0, 96.0, 97.0, 98.0, 99.0],
        "close": [102.0, 103.0, 104.0, 105.0, 106.0],
        "volume": [1000, 1100, 1200, 1300, 1400]
    }, index=dates)
    
    result = to_uplot_format(df)
    timestamps = result[0]
    
    # Verify ascending order
    assert timestamps == sorted(timestamps)
    
    # Verify consistent intervals (1 hour = 3600000 ms)
    diffs = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
    assert all(d == 3600000 for d in diffs)


def test_timezone_aware_conversion():
    """Test conversion with timezone-aware datetimes."""
    # Create datetime in US/Eastern
    dates = pd.date_range("2024-01-15 09:00", periods=3, freq="1h", tz="US/Eastern")
    df = pd.DataFrame({
        "open": [100.0, 101.0, 102.0],
        "high": [105.0, 106.0, 107.0],
        "low": [95.0, 96.0, 97.0],
        "close": [102.0, 103.0, 104.0],
        "volume": [1000, 1100, 1200]
    }, index=dates)
    
    result = to_uplot_format(df)
    timestamps = result[0]
    
    # Timestamps should be in Unix time (UTC)
    # 09:00 Eastern = 14:00 UTC
    first_dt = pd.Timestamp("2024-01-15 14:00", tz="UTC")
    expected_first = int(first_dt.timestamp() * 1000)
    
    assert timestamps[0] == expected_first


def test_naive_datetime_assumes_utc():
    """Test that naive datetimes are assumed to be UTC."""
    # Create naive datetime
    dates = pd.date_range("2024-01-01 10:00", periods=2, freq="1h")
    df = pd.DataFrame({
        "open": [100.0, 101.0],
        "high": [105.0, 106.0],
        "low": [95.0, 96.0],
        "close": [102.0, 103.0],
        "volume": [1000, 1100]
    }, index=dates)
    
    result = to_uplot_format(df)
    timestamps = result[0]
    
    # Should treat as UTC
    expected_first = int(pd.Timestamp("2024-01-01 10:00", tz="UTC").timestamp() * 1000)
    assert timestamps[0] == expected_first


def test_conversion_precision():
    """Test that conversion maintains millisecond precision."""
    # Create timestamp with milliseconds
    dt_with_ms = pd.DatetimeIndex(["2024-01-01 10:00:00.123"], tz="UTC")
    df = pd.DataFrame({
        "open": [100.0],
        "high": [105.0],
        "low": [95.0],
        "close": [102.0],
        "volume": [1000]
    }, index=dt_with_ms)
    
    result = to_uplot_format(df, timestamp_unit="ms")
    timestamp = result[0][0]
    
    # Should include milliseconds (.123)
    # Verify by converting back
    converted_back = pd.Timestamp(timestamp, unit="ms", tz="UTC")
    assert converted_back.microsecond == 123000  # 123 ms = 123000 μs


def test_empty_dataframe_timestamps():
    """Test timestamp handling with empty DataFrame."""
    df = pd.DataFrame({
        "open": [],
        "high": [],
        "low": [],
        "close": [],
        "volume": []
    })
    df.index = pd.DatetimeIndex([], tz="UTC")
    
    result = to_uplot_format(df)
    
    # Should have empty timestamp array
    assert len(result[0]) == 0


def test_single_timestamp_conversion():
    """Test conversion of single timestamp."""
    dates = pd.date_range("2024-01-01", periods=1, freq="1h", tz="UTC")
    df = pd.DataFrame({
        "open": [100.0],
        "high": [105.0],
        "low": [95.0],
        "close": [102.0],
        "volume": [1000]
    }, index=dates)
    
    result = to_uplot_format(df)
    
    # Should handle single timestamp
    assert len(result[0]) == 1
    assert isinstance(result[0][0], int)


def test_mixed_timezone_data():
    """Test that mixed timezone data is normalized to UTC."""
    # Create data in different timezones (though in practice, a single
    # DataFrame will have one timezone for its index)
    dates_utc = pd.date_range("2024-01-01 14:00", periods=2, freq="1h", tz="UTC")
    df = pd.DataFrame({
        "open": [100.0, 101.0],
        "high": [105.0, 106.0],
        "low": [95.0, 96.0],
        "close": [102.0, 103.0],
        "volume": [1000, 1100]
    }, index=dates_utc)
    
    # Convert to different timezone
    df.index = df.index.tz_convert("Asia/Tokyo")
    
    result = to_uplot_format(df)
    timestamps = result[0]
    
    # Timestamps should still represent the same moment in time
    # First timestamp: 2024-01-01 14:00 UTC = 2024-01-01 23:00 Tokyo
    expected_first = int(pd.Timestamp("2024-01-01 14:00", tz="UTC").timestamp() * 1000)
    assert timestamps[0] == expected_first


def test_dst_transition_handling():
    """Test timestamp conversion across DST transition."""
    # Create data spanning DST transition in US (March 2024)
    dates = pd.date_range("2024-03-10 00:00", periods=5, freq="1h", tz="US/Eastern")
    df = pd.DataFrame({
        "open": range(100, 105),
        "high": range(105, 110),
        "low": range(95, 100),
        "close": range(100, 105),
        "volume": [1000] * 5
    }, index=dates)
    
    result = to_uplot_format(df)
    timestamps = result[0]
    
    # Timestamps should be correctly converted to UTC despite DST
    assert len(timestamps) == 5
    assert timestamps == sorted(timestamps)  # Should be chronological

