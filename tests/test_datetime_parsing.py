"""Tests for datetime format detection and parsing."""
import pytest
import pandas as pd
from pathlib import Path
from charting.ingestion.loader import load_csv, parse_datetime


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


def test_parse_iso8601_datetime(fixtures_dir):
    """Test parsing ISO 8601 format datetime."""
    csv_path = fixtures_dir / "iso8601_datetime.csv"
    df = load_csv(csv_path)
    df = parse_datetime(df)
    
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"]), "timestamp should be datetime type"
    assert df["timestamp"].iloc[0] == pd.Timestamp("2024-01-01 00:00:00")


def test_parse_unix_timestamp(fixtures_dir):
    """Test parsing Unix timestamp format."""
    csv_path = fixtures_dir / "unix_timestamp.csv"
    df = load_csv(csv_path)
    df = parse_datetime(df)
    
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"]), "timestamp should be datetime type"
    # Unix timestamp 1704067200 = 2024-01-01 00:00:00 UTC
    assert df["timestamp"].iloc[0].year == 2024
    assert df["timestamp"].iloc[0].month == 1
    assert df["timestamp"].iloc[0].day == 1


def test_parse_us_datetime_format(fixtures_dir):
    """Test parsing US datetime format (MM/DD/YYYY)."""
    csv_path = fixtures_dir / "us_datetime.csv"
    df = load_csv(csv_path)
    df = parse_datetime(df)
    
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"]), "timestamp should be datetime type"
    assert df["timestamp"].iloc[0] == pd.Timestamp("2024-01-01 00:00:00")


def test_parse_eu_datetime_format(fixtures_dir):
    """Test parsing EU datetime format (DD-MM-YYYY)."""
    csv_path = fixtures_dir / "eu_datetime.csv"
    df = load_csv(csv_path)
    df = parse_datetime(df)
    
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"]), "timestamp should be datetime type"
    assert df["timestamp"].iloc[0] == pd.Timestamp("2024-01-01 00:00:00")


def test_parse_datetime_preserves_other_columns(fixtures_dir):
    """Test that parsing datetime doesn't affect other columns."""
    csv_path = fixtures_dir / "valid_ohlc.csv"
    df = load_csv(csv_path)
    original_columns = list(df.columns)
    
    df = parse_datetime(df)
    
    assert list(df.columns) == original_columns, "Columns should not change"
    assert "open" in df.columns
    assert "close" in df.columns


def test_parse_datetime_maintains_data_order(fixtures_dir):
    """Test that datetime parsing maintains row order."""
    csv_path = fixtures_dir / "valid_ohlc.csv"
    df = load_csv(csv_path)
    original_length = len(df)
    
    df = parse_datetime(df)
    
    assert len(df) == original_length, "Number of rows should not change"


def test_parse_datetime_sorts_chronologically(fixtures_dir):
    """Test that datetime parsing sorts data chronologically."""
    csv_path = fixtures_dir / "valid_ohlc.csv"
    df = load_csv(csv_path)
    df = parse_datetime(df)
    
    # Check that timestamps are in ascending order
    assert df["timestamp"].is_monotonic_increasing, "Timestamps should be sorted"


def test_parse_datetime_handles_already_parsed():
    """Test that parsing an already-parsed datetime column doesn't fail."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=3, freq="h"),
        "open": [100, 101, 102],
        "high": [105, 106, 107],
        "low": [99, 100, 101],
        "close": [103, 104, 105],
        "volume": [1000, 1100, 1200]
    })
    
    # Should not raise error when timestamp is already datetime
    result = parse_datetime(df)
    assert pd.api.types.is_datetime64_any_dtype(result["timestamp"])


def test_parse_datetime_with_timezone():
    """Test that datetime parsing handles timezone information."""
    df = pd.DataFrame({
        "timestamp": ["2024-01-01T00:00:00+00:00", "2024-01-01T01:00:00+00:00"],
        "open": [100, 101],
        "high": [105, 106],
        "low": [99, 100],
        "close": [103, 104],
        "volume": [1000, 1100]
    })
    
    result = parse_datetime(df)
    assert pd.api.types.is_datetime64_any_dtype(result["timestamp"])


def test_parse_datetime_missing_timestamp_column():
    """Test error handling when timestamp column is missing."""
    df = pd.DataFrame({
        "date": ["2024-01-01", "2024-01-02"],
        "open": [100, 101],
        "high": [105, 106],
        "low": [99, 100],
        "close": [103, 104],
        "volume": [1000, 1100]
    })
    
    with pytest.raises(ValueError, match="timestamp.*not found"):
        parse_datetime(df)

