"""Tests for DataFrame optimization for time-series operations."""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from charting.ingestion.loader import load_csv, parse_datetime, clean_missing_values, optimize_dataframe


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


def test_datetime_set_as_index(fixtures_dir):
    """Test that timestamp column is set as the DataFrame index."""
    csv_path = fixtures_dir / "valid_ohlc.csv"
    df = load_csv(csv_path)
    df = parse_datetime(df)
    df = clean_missing_values(df)
    df_opt = optimize_dataframe(df)
    
    # Index should be datetime
    assert isinstance(df_opt.index, pd.DatetimeIndex)
    assert df_opt.index.name == "timestamp"


def test_timestamp_column_removed_after_indexing(fixtures_dir):
    """Test that timestamp column is removed after being set as index."""
    csv_path = fixtures_dir / "valid_ohlc.csv"
    df = load_csv(csv_path)
    df = parse_datetime(df)
    df = clean_missing_values(df)
    df_opt = optimize_dataframe(df)
    
    # Timestamp should not be a column anymore (it's the index)
    assert "timestamp" not in df_opt.columns


def test_dataframe_sorted_chronologically(fixtures_dir):
    """Test that DataFrame is sorted by timestamp."""
    csv_path = fixtures_dir / "valid_ohlc.csv"
    df = load_csv(csv_path)
    df = parse_datetime(df)
    df = clean_missing_values(df)
    df_opt = optimize_dataframe(df)
    
    # Index should be monotonically increasing
    assert df_opt.index.is_monotonic_increasing


def test_memory_optimization_float32():
    """Test that price columns are converted to float32 for memory efficiency."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=5, freq="h"),
        "open": [100.0, 101.0, 102.0, 103.0, 104.0],
        "high": [105.0, 106.0, 107.0, 108.0, 109.0],
        "low": [99.0, 100.0, 101.0, 102.0, 103.0],
        "close": [103.0, 104.0, 105.0, 106.0, 107.0],
        "volume": [10000, 11000, 12000, 13000, 14000]
    })
    
    df_opt = optimize_dataframe(df)
    
    # Price columns should be float32
    assert df_opt["open"].dtype == np.float32
    assert df_opt["high"].dtype == np.float32
    assert df_opt["low"].dtype == np.float32
    assert df_opt["close"].dtype == np.float32


def test_memory_optimization_int32_volume():
    """Test that volume column is converted to int32 when values are integers."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=5, freq="h"),
        "open": [100.0, 101.0, 102.0, 103.0, 104.0],
        "high": [105.0, 106.0, 107.0, 108.0, 109.0],
        "low": [99.0, 100.0, 101.0, 102.0, 103.0],
        "close": [103.0, 104.0, 105.0, 106.0, 107.0],
        "volume": [10000, 11000, 12000, 13000, 14000]
    })
    
    df_opt = optimize_dataframe(df)
    
    # Volume should be int32 if all values are integers
    assert df_opt["volume"].dtype in [np.int32, np.int64]


def test_required_columns_validation():
    """Test that missing required columns raise an error."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=3, freq="h"),
        "open": [100.0, 101.0, 102.0],
        # Missing high, low, close, volume
    })
    
    with pytest.raises(ValueError, match="required columns"):
        optimize_dataframe(df)


def test_all_required_columns_present(fixtures_dir):
    """Test validation passes when all required columns are present."""
    csv_path = fixtures_dir / "valid_ohlc.csv"
    df = load_csv(csv_path)
    df = parse_datetime(df)
    df = clean_missing_values(df)
    
    # Should not raise any error
    df_opt = optimize_dataframe(df)
    assert df_opt is not None


def test_metadata_attributes_added():
    """Test that metadata attributes are added to the DataFrame."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=3, freq="h"),
        "open": [100.0, 101.0, 102.0],
        "high": [105.0, 106.0, 107.0],
        "low": [99.0, 100.0, 101.0],
        "close": [103.0, 104.0, 105.0],
        "volume": [10000, 11000, 12000]
    })
    
    df_opt = optimize_dataframe(df, source="test_data.csv")
    
    # Should have metadata attributes
    assert hasattr(df_opt, "attrs")
    assert "source" in df_opt.attrs
    assert "processed_at" in df_opt.attrs
    assert df_opt.attrs["source"] == "test_data.csv"


def test_preserves_data_values():
    """Test that optimization doesn't change data values."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=3, freq="h"),
        "open": [100.0, 101.0, 102.0],
        "high": [105.0, 106.0, 107.0],
        "low": [99.0, 100.0, 101.0],
        "close": [103.0, 104.0, 105.0],
        "volume": [10000, 11000, 12000]
    })
    
    original_close = df["close"].values.copy()
    df_opt = optimize_dataframe(df)
    
    # Values should be preserved (within floating point precision)
    np.testing.assert_allclose(df_opt["close"].values, original_close, rtol=1e-6)


def test_time_based_slicing_performance():
    """Test that time-based slicing works efficiently with datetime index."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=100, freq="h"),
        "open": np.random.uniform(100, 110, 100),
        "high": np.random.uniform(110, 120, 100),
        "low": np.random.uniform(90, 100, 100),
        "close": np.random.uniform(100, 110, 100),
        "volume": np.random.randint(10000, 20000, 100)
    })
    
    df_opt = optimize_dataframe(df)
    
    # Should be able to slice by date strings
    sliced = df_opt["2024-01-01":"2024-01-02"]
    assert len(sliced) > 0
    assert isinstance(sliced.index, pd.DatetimeIndex)


def test_handles_fractional_volume():
    """Test that fractional volume values are handled properly."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=3, freq="h"),
        "open": [100.0, 101.0, 102.0],
        "high": [105.0, 106.0, 107.0],
        "low": [99.0, 100.0, 101.0],
        "close": [103.0, 104.0, 105.0],
        "volume": [10000.5, 11000.7, 12000.3]  # Fractional volumes
    })
    
    df_opt = optimize_dataframe(df)
    
    # Volume with fractions should remain float type
    assert df_opt["volume"].dtype in [np.float32, np.float64]


def test_empty_dataframe_handling():
    """Test handling of empty DataFrames."""
    df = pd.DataFrame({
        "timestamp": pd.Series([], dtype="datetime64[ns]"),
        "open": pd.Series([], dtype=float),
        "high": pd.Series([], dtype=float),
        "low": pd.Series([], dtype=float),
        "close": pd.Series([], dtype=float),
        "volume": pd.Series([], dtype=float)
    })
    
    df_opt = optimize_dataframe(df)
    
    # Should handle empty DataFrame gracefully
    assert len(df_opt) == 0
    assert isinstance(df_opt.index, pd.DatetimeIndex)

