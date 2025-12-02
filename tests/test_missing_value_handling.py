"""Tests for missing value handling and data cleaning."""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from charting.ingestion.loader import load_csv, parse_datetime, clean_missing_values


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


def test_forward_fill_missing_prices(fixtures_dir):
    """Test that missing price values are forward-filled."""
    csv_path = fixtures_dir / "missing_prices.csv"
    df = load_csv(csv_path)
    df = parse_datetime(df)
    df_clean = clean_missing_values(df)
    
    # Should not have any NaN values in price columns after cleaning
    assert not df_clean["open"].isna().any(), "open should not have NaN values"
    assert not df_clean["high"].isna().any(), "high should not have NaN values"
    assert not df_clean["low"].isna().any(), "low should not have NaN values"
    assert not df_clean["close"].isna().any(), "close should not have NaN values"


def test_interpolate_missing_volume(fixtures_dir):
    """Test that missing volume values are interpolated."""
    csv_path = fixtures_dir / "missing_volume.csv"
    df = load_csv(csv_path)
    df = parse_datetime(df)
    df_clean = clean_missing_values(df)
    
    # Should not have any NaN values in volume after cleaning
    assert not df_clean["volume"].isna().any(), "volume should not have NaN values"
    
    # Interpolated values should be reasonable (between neighboring values)
    # Row 1 volume should be interpolated between 10000 and 12000
    assert 10000 <= df_clean["volume"].iloc[1] <= 12000


def test_remove_rows_with_missing_timestamps(fixtures_dir):
    """Test that rows with missing timestamps are removed."""
    csv_path = fixtures_dir / "missing_timestamps.csv"
    df = load_csv(csv_path)
    
    # Before cleaning, should have 3 rows (one with NaN timestamp)
    # After parse_datetime and cleaning, row with missing timestamp should be removed
    df = parse_datetime(df)
    df_clean = clean_missing_values(df)
    
    # Should have 2 valid rows (the one with missing timestamp removed)
    assert len(df_clean) == 2
    assert not df_clean["timestamp"].isna().any()


def test_handle_consecutive_missing_values(fixtures_dir):
    """Test handling of consecutive missing values."""
    csv_path = fixtures_dir / "consecutive_missing.csv"
    df = load_csv(csv_path)
    df = parse_datetime(df)
    df_clean = clean_missing_values(df)
    
    # Consecutive missing values in prices should be forward-filled
    assert not df_clean["open"].isna().any()
    assert not df_clean["close"].isna().any()
    
    # Volume should be interpolated
    assert not df_clean["volume"].isna().any()


def test_preserves_valid_data(fixtures_dir):
    """Test that cleaning doesn't alter valid data."""
    csv_path = fixtures_dir / "valid_ohlc.csv"
    df = load_csv(csv_path)
    df = parse_datetime(df)
    original_values = df["close"].copy()
    
    df_clean = clean_missing_values(df)
    
    # All values should remain the same
    pd.testing.assert_series_equal(df_clean["close"], original_values, check_names=False)


def test_maintains_row_count_when_possible(fixtures_dir):
    """Test that cleaning maintains row count when no critical data is missing."""
    csv_path = fixtures_dir / "missing_prices.csv"
    df = load_csv(csv_path)
    df = parse_datetime(df)
    original_length = len(df)
    
    df_clean = clean_missing_values(df)
    
    # Should maintain same number of rows
    assert len(df_clean) == original_length


def test_data_types_preserved_after_cleaning(fixtures_dir):
    """Test that data types are preserved after cleaning."""
    csv_path = fixtures_dir / "missing_prices.csv"
    df = load_csv(csv_path)
    df = parse_datetime(df)
    df_clean = clean_missing_values(df)
    
    # Check that datetime and numeric types are preserved
    assert pd.api.types.is_datetime64_any_dtype(df_clean["timestamp"])
    assert pd.api.types.is_numeric_dtype(df_clean["open"])
    assert pd.api.types.is_numeric_dtype(df_clean["volume"])


def test_forward_fill_uses_previous_value():
    """Test that forward-fill uses the previous valid value."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=4, freq="h"),
        "open": [100.0, np.nan, np.nan, 104.0],
        "high": [105.0, 106.0, 107.0, 108.0],
        "low": [99.0, 100.0, 101.0, 102.0],
        "close": [103.0, 104.0, 105.0, 106.0],
        "volume": [1000, 1100, 1200, 1300]
    })
    
    df_clean = clean_missing_values(df)
    
    # Missing values at index 1 and 2 should be filled with 100.0
    assert df_clean["open"].iloc[1] == 100.0
    assert df_clean["open"].iloc[2] == 100.0


def test_interpolation_calculates_intermediate_values():
    """Test that volume interpolation calculates intermediate values."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=5, freq="h"),
        "open": [100.0, 101.0, 102.0, 103.0, 104.0],
        "high": [105.0, 106.0, 107.0, 108.0, 109.0],
        "low": [99.0, 100.0, 101.0, 102.0, 103.0],
        "close": [103.0, 104.0, 105.0, 106.0, 107.0],
        "volume": [1000, np.nan, np.nan, np.nan, 2000]
    })
    
    df_clean = clean_missing_values(df)
    
    # Interpolated values should be evenly spaced between 1000 and 2000
    assert df_clean["volume"].iloc[1] == pytest.approx(1250.0, rel=0.01)
    assert df_clean["volume"].iloc[2] == pytest.approx(1500.0, rel=0.01)
    assert df_clean["volume"].iloc[3] == pytest.approx(1750.0, rel=0.01)


def test_cleaning_with_no_missing_values(fixtures_dir):
    """Test that cleaning works correctly when there are no missing values."""
    csv_path = fixtures_dir / "valid_ohlc.csv"
    df = load_csv(csv_path)
    df = parse_datetime(df)
    original_df = df.copy()
    
    df_clean = clean_missing_values(df)
    
    # Should be identical to original
    pd.testing.assert_frame_equal(df_clean, original_df)


def test_edge_case_all_volume_missing():
    """Test edge case where all volume values are missing."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=3, freq="h"),
        "open": [100.0, 101.0, 102.0],
        "high": [105.0, 106.0, 107.0],
        "low": [99.0, 100.0, 101.0],
        "close": [103.0, 104.0, 105.0],
        "volume": [np.nan, np.nan, np.nan]
    })
    
    # Should handle gracefully - could fill with 0 or a default value
    df_clean = clean_missing_values(df)
    
    # After cleaning, volume should have some default value (not NaN)
    assert not df_clean["volume"].isna().any()

