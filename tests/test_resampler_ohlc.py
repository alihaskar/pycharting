"""Tests for OHLC aggregation logic in resampler module."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from charting.processing.resampler import resample_ohlc


@pytest.fixture
def sample_1min_data():
    """Create sample 1-minute OHLC data for testing."""
    dates = pd.date_range("2024-01-01 09:00", periods=10, freq="1min")
    data = {
        "open": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
        "high": [101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0],
        "low": [99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0],
        "close": [100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5, 108.5, 109.5],
        "volume": [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]
    }
    return pd.DataFrame(data, index=dates)


def test_resample_5min_basic(sample_1min_data):
    """Test basic 5-minute resampling."""
    result = resample_ohlc(sample_1min_data, "5min")
    
    # Should have 2 bars (10 minutes / 5 = 2)
    assert len(result) == 2
    
    # Check first bar (minutes 0-4, indices 0-4 = 5 bars)
    assert result.iloc[0]["open"] == 100.0  # First open
    assert result.iloc[0]["high"] == 105.0  # Max high
    assert result.iloc[0]["low"] == 99.0    # Min low
    assert result.iloc[0]["close"] == 104.5 # Last close
    assert result.iloc[0]["volume"] == 6000 # Sum of volumes (1000+1100+1200+1300+1400)


def test_resample_ohlc_logic(sample_1min_data):
    """Test OHLC aggregation rules: Open=first, High=max, Low=min, Close=last, Volume=sum."""
    result = resample_ohlc(sample_1min_data, "10min")
    
    # Should have 1 bar for all 10 minutes
    assert len(result) == 1
    
    # Verify OHLC logic
    assert result.iloc[0]["open"] == sample_1min_data.iloc[0]["open"]    # First open
    assert result.iloc[0]["high"] == sample_1min_data["high"].max()      # Max high
    assert result.iloc[0]["low"] == sample_1min_data["low"].min()        # Min low
    assert result.iloc[0]["close"] == sample_1min_data.iloc[-1]["close"] # Last close
    assert result.iloc[0]["volume"] == sample_1min_data["volume"].sum()  # Sum volume


def test_resample_maintains_index_type():
    """Test that resampled data maintains DatetimeIndex."""
    dates = pd.date_range("2024-01-01", periods=60, freq="1min")
    df = pd.DataFrame({
        "open": range(100, 160),
        "high": range(101, 161),
        "low": range(99, 159),
        "close": range(100, 160),
        "volume": [1000] * 60
    }, index=dates)
    
    result = resample_ohlc(df, "1h")
    
    assert isinstance(result.index, pd.DatetimeIndex)


def test_resample_with_missing_values():
    """Test resampling with missing values in data."""
    dates = pd.date_range("2024-01-01 09:00", periods=10, freq="1min")
    data = {
        "open": [100.0, np.nan, 102.0, 103.0, 104.0, np.nan, 106.0, 107.0, 108.0, 109.0],
        "high": [101.0, 102.0, np.nan, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0],
        "low": [99.0, 100.0, 101.0, 102.0, np.nan, 104.0, 105.0, 106.0, 107.0, 108.0],
        "close": [100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5, 108.5, 109.5],
        "volume": [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]
    }
    df = pd.DataFrame(data, index=dates)
    
    result = resample_ohlc(df, "5min")
    
    # Should handle NaN gracefully (using non-NaN values)
    assert len(result) == 2
    assert not np.isnan(result.iloc[0]["close"])  # Close should always have value


def test_resample_single_bar():
    """Test resampling with only one bar of data."""
    dates = pd.date_range("2024-01-01 09:00", periods=1, freq="1min")
    df = pd.DataFrame({
        "open": [100.0],
        "high": [101.0],
        "low": [99.0],
        "close": [100.5],
        "volume": [1000]
    }, index=dates)
    
    result = resample_ohlc(df, "5min")
    
    # Single bar should remain
    assert len(result) == 1
    assert result.iloc[0]["open"] == 100.0
    assert result.iloc[0]["high"] == 101.0
    assert result.iloc[0]["low"] == 99.0
    assert result.iloc[0]["close"] == 100.5
    assert result.iloc[0]["volume"] == 1000


def test_resample_to_daily():
    """Test resampling to daily timeframe."""
    dates = pd.date_range("2024-01-01 09:00", periods=390, freq="1min")  # Full trading day
    df = pd.DataFrame({
        "open": [100.0] * 390,
        "high": [105.0] * 390,
        "low": [95.0] * 390,
        "close": [102.0] * 390,
        "volume": [1000] * 390
    }, index=dates)
    
    result = resample_ohlc(df, "1D")
    
    # Should have 1 daily bar
    assert len(result) == 1
    assert result.iloc[0]["volume"] == 390000  # Sum of all volumes


def test_resample_preserves_ohlc_relationships():
    """Test that OHLC relationships are preserved after resampling."""
    dates = pd.date_range("2024-01-01", periods=100, freq="1min")
    df = pd.DataFrame({
        "open": np.random.uniform(100, 110, 100),
        "high": np.random.uniform(110, 120, 100),
        "low": np.random.uniform(90, 100, 100),
        "close": np.random.uniform(100, 110, 100),
        "volume": np.random.randint(1000, 2000, 100)
    }, index=dates)
    
    result = resample_ohlc(df, "10min")
    
    # Verify OHLC relationships
    for idx in range(len(result)):
        assert result.iloc[idx]["high"] >= result.iloc[idx]["open"]
        assert result.iloc[idx]["high"] >= result.iloc[idx]["close"]
        assert result.iloc[idx]["low"] <= result.iloc[idx]["open"]
        assert result.iloc[idx]["low"] <= result.iloc[idx]["close"]
        assert result.iloc[idx]["volume"] >= 0


def test_resample_empty_dataframe():
    """Test resampling empty DataFrame."""
    df = pd.DataFrame({
        "open": [],
        "high": [],
        "low": [],
        "close": [],
        "volume": []
    })
    df.index = pd.DatetimeIndex([])
    
    result = resample_ohlc(df, "5min")
    
    assert len(result) == 0
    assert isinstance(result.index, pd.DatetimeIndex)


def test_resample_volume_conservation():
    """Test that total volume is conserved during resampling."""
    dates = pd.date_range("2024-01-01", periods=60, freq="1min")
    df = pd.DataFrame({
        "open": range(100, 160),
        "high": range(101, 161),
        "low": range(99, 159),
        "close": range(100, 160),
        "volume": [1000] * 60
    }, index=dates)
    
    original_volume = df["volume"].sum()
    result = resample_ohlc(df, "10min")
    resampled_volume = result["volume"].sum()
    
    assert original_volume == resampled_volume


def test_resample_multiple_timeframes():
    """Test resampling to various timeframes."""
    dates = pd.date_range("2024-01-01", periods=120, freq="1min")
    df = pd.DataFrame({
        "open": range(100, 220),
        "high": range(101, 221),
        "low": range(99, 219),
        "close": range(100, 220),
        "volume": [1000] * 120
    }, index=dates)
    
    # Test various timeframes
    result_5min = resample_ohlc(df, "5min")
    assert len(result_5min) == 24  # 120 / 5
    
    result_15min = resample_ohlc(df, "15min")
    assert len(result_15min) == 8  # 120 / 15
    
    result_1h = resample_ohlc(df, "1h")
    assert len(result_1h) == 2  # 120 / 60


def test_resample_irregular_periods():
    """Test resampling with irregular time periods."""
    # Create data with some gaps
    dates = pd.DatetimeIndex([
        "2024-01-01 09:00",
        "2024-01-01 09:01",
        "2024-01-01 09:05",  # Gap
        "2024-01-01 09:06",
        "2024-01-01 09:10"
    ])
    df = pd.DataFrame({
        "open": [100.0, 101.0, 102.0, 103.0, 104.0],
        "high": [101.0, 102.0, 103.0, 104.0, 105.0],
        "low": [99.0, 100.0, 101.0, 102.0, 103.0],
        "close": [100.5, 101.5, 102.5, 103.5, 104.5],
        "volume": [1000, 1100, 1200, 1300, 1400]
    }, index=dates)
    
    result = resample_ohlc(df, "5min")
    
    # Should handle gaps appropriately
    assert len(result) >= 1
    assert isinstance(result.index, pd.DatetimeIndex)

