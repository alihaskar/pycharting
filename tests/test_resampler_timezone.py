"""Tests for timezone-aware resampling in resampler module."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from src.processing.resampler import resample_ohlc_with_timezone


@pytest.fixture
def sample_utc_data():
    """Create sample OHLC data with UTC timezone."""
    dates = pd.date_range("2024-01-01 09:00", periods=10, freq="1h", tz="UTC")
    data = {
        "open": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
        "high": [101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0],
        "low": [99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0],
        "close": [100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5, 108.5, 109.5],
        "volume": [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]
    }
    return pd.DataFrame(data, index=dates)


def test_resample_with_utc_timezone(sample_utc_data):
    """Test resampling with UTC timezone data."""
    result = resample_ohlc_with_timezone(sample_utc_data, "2h", target_tz="UTC")
    
    # Should have timezone information
    assert result.index.tz is not None
    assert str(result.index.tz) == "UTC"
    
    # Should have proper resampling (depends on bin alignment)
    assert len(result) >= 5  # At least 5 bars for 10 hours resampled to 2h


def test_resample_convert_to_us_eastern():
    """Test resampling with timezone conversion to US Eastern."""
    # Create UTC data
    dates = pd.date_range("2024-01-01 14:00", periods=6, freq="1h", tz="UTC")
    df = pd.DataFrame({
        "open": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0],
        "high": [101.0, 102.0, 103.0, 104.0, 105.0, 106.0],
        "low": [99.0, 100.0, 101.0, 102.0, 103.0, 104.0],
        "close": [100.5, 101.5, 102.5, 103.5, 104.5, 105.5],
        "volume": [1000, 1100, 1200, 1300, 1400, 1500]
    }, index=dates)
    
    # Convert to US/Eastern
    result = resample_ohlc_with_timezone(df, "1h", target_tz="US/Eastern")
    
    # Should be in US/Eastern timezone
    assert result.index.tz is not None
    assert "America/New_York" in str(result.index.tz) or "US/Eastern" in str(result.index.tz)


def test_resample_naive_to_timezone_aware():
    """Test converting naive datetime to timezone-aware."""
    # Create naive datetime data
    dates = pd.date_range("2024-01-01 09:00", periods=6, freq="1h")
    df = pd.DataFrame({
        "open": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0],
        "high": [101.0, 102.0, 103.0, 104.0, 105.0, 106.0],
        "low": [99.0, 100.0, 101.0, 102.0, 103.0, 104.0],
        "close": [100.5, 101.5, 102.5, 103.5, 104.5, 105.5],
        "volume": [1000, 1100, 1200, 1300, 1400, 1500]
    }, index=dates)
    
    # Localize to UTC
    result = resample_ohlc_with_timezone(df, "2h", source_tz="UTC")
    
    # Should be timezone-aware
    assert result.index.tz is not None


def test_resample_preserves_timezone():
    """Test that resampling preserves timezone information."""
    dates = pd.date_range("2024-01-01 09:00", periods=6, freq="1h", tz="Europe/London")
    df = pd.DataFrame({
        "open": range(100, 106),
        "high": range(101, 107),
        "low": range(99, 105),
        "close": range(100, 106),
        "volume": [1000] * 6
    }, index=dates)
    
    result = resample_ohlc_with_timezone(df, "3h")
    
    # Should maintain Europe/London timezone
    assert result.index.tz is not None
    assert "Europe/London" in str(result.index.tz)


def test_resample_across_dst_transition():
    """Test resampling across daylight saving time transition."""
    # Create data spanning DST transition in US (March 2024)
    # DST starts March 10, 2024 at 2:00 AM
    dates = pd.date_range("2024-03-10 00:00", periods=10, freq="1h", tz="US/Eastern")
    df = pd.DataFrame({
        "open": range(100, 110),
        "high": range(101, 111),
        "low": range(99, 109),
        "close": range(100, 110),
        "volume": [1000] * 10
    }, index=dates)
    
    result = resample_ohlc_with_timezone(df, "2h")
    
    # Should handle DST transition gracefully
    assert result.index.tz is not None
    # Should not have NaN or errors
    assert not result["close"].isna().any()


def test_resample_common_market_timezones():
    """Test resampling with common financial market timezones."""
    dates = pd.date_range("2024-01-01 09:00", periods=6, freq="1h", tz="UTC")
    df = pd.DataFrame({
        "open": range(100, 106),
        "high": range(101, 107),
        "low": range(99, 105),
        "close": range(100, 106),
        "volume": [1000] * 6
    }, index=dates)
    
    # Test US markets
    us_result = resample_ohlc_with_timezone(df, "2h", target_tz="US/Eastern")
    assert us_result.index.tz is not None
    
    # Test European markets
    eu_result = resample_ohlc_with_timezone(df, "2h", target_tz="Europe/London")
    assert eu_result.index.tz is not None
    
    # Test Asian markets
    asia_result = resample_ohlc_with_timezone(df, "2h", target_tz="Asia/Tokyo")
    assert asia_result.index.tz is not None


def test_resample_timezone_conversion_accuracy():
    """Test that timezone conversion maintains accurate timestamps."""
    # 14:00 UTC = 09:00 US/Eastern (EST, UTC-5)
    utc_dates = pd.date_range("2024-01-15 14:00", periods=3, freq="1h", tz="UTC")
    df = pd.DataFrame({
        "open": [100.0, 101.0, 102.0],
        "high": [101.0, 102.0, 103.0],
        "low": [99.0, 100.0, 101.0],
        "close": [100.5, 101.5, 102.5],
        "volume": [1000, 1100, 1200]
    }, index=utc_dates)
    
    result = resample_ohlc_with_timezone(df, "1h", target_tz="US/Eastern")
    
    # First timestamp should be 09:00 Eastern
    assert result.index[0].hour == 9


def test_resample_empty_dataframe_with_timezone():
    """Test timezone handling with empty DataFrame."""
    df = pd.DataFrame({
        "open": [],
        "high": [],
        "low": [],
        "close": [],
        "volume": []
    })
    df.index = pd.DatetimeIndex([], tz="UTC")
    
    result = resample_ohlc_with_timezone(df, "1h")
    
    # Should handle empty DataFrame
    assert len(result) == 0


def test_resample_with_none_timezone():
    """Test that None timezone uses data's existing timezone."""
    dates = pd.date_range("2024-01-01", periods=6, freq="1h", tz="Asia/Tokyo")
    df = pd.DataFrame({
        "open": range(100, 106),
        "high": range(101, 107),
        "low": range(99, 105),
        "close": range(100, 106),
        "volume": [1000] * 6
    }, index=dates)
    
    # Should preserve existing timezone
    result = resample_ohlc_with_timezone(df, "2h", target_tz=None)
    
    assert result.index.tz is not None
    assert "Asia/Tokyo" in str(result.index.tz)


def test_resample_invalid_timezone_raises_error():
    """Test that invalid timezone raises appropriate error."""
    dates = pd.date_range("2024-01-01", periods=6, freq="1h", tz="UTC")
    df = pd.DataFrame({
        "open": range(100, 106),
        "high": range(101, 107),
        "low": range(99, 105),
        "close": range(100, 106),
        "volume": [1000] * 6
    }, index=dates)
    
    with pytest.raises((pytz.UnknownTimeZoneError, ValueError)):
        resample_ohlc_with_timezone(df, "1h", target_tz="Invalid/Timezone")


def test_resample_ohlc_relationships_with_timezone():
    """Test that OHLC relationships are preserved after timezone operations."""
    dates = pd.date_range("2024-01-01", periods=12, freq="1h", tz="UTC")
    df = pd.DataFrame({
        "open": np.random.uniform(100, 110, 12),
        "high": np.random.uniform(110, 120, 12),
        "low": np.random.uniform(90, 100, 12),
        "close": np.random.uniform(100, 110, 12),
        "volume": np.random.randint(1000, 2000, 12)
    }, index=dates)
    
    result = resample_ohlc_with_timezone(df, "4h", target_tz="US/Eastern")
    
    # Verify OHLC relationships
    for idx in range(len(result)):
        assert result.iloc[idx]["high"] >= result.iloc[idx]["open"]
        assert result.iloc[idx]["high"] >= result.iloc[idx]["close"]
        assert result.iloc[idx]["low"] <= result.iloc[idx]["open"]
        assert result.iloc[idx]["low"] <= result.iloc[idx]["close"]

