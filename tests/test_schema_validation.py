"""Tests for Pydantic OHLC data validation models."""
import pytest
from datetime import datetime
from pydantic import ValidationError
from charting.ingestion.schema import OHLCRecord


def test_valid_ohlc_record():
    """Test creating a valid OHLC record."""
    record = OHLCRecord(
        timestamp=datetime(2024, 1, 1, 0, 0, 0),
        open=100.0,
        high=105.0,
        low=99.0,
        close=103.0,
        volume=10000
    )
    
    assert record.timestamp == datetime(2024, 1, 1, 0, 0, 0)
    assert record.open == 100.0
    assert record.high == 105.0
    assert record.low == 99.0
    assert record.close == 103.0
    assert record.volume == 10000


def test_high_greater_than_or_equal_to_open():
    """Test that high must be >= open."""
    # Valid: high > open
    record = OHLCRecord(
        timestamp=datetime(2024, 1, 1),
        open=100.0,
        high=105.0,
        low=99.0,
        close=103.0,
        volume=1000
    )
    assert record.high >= record.open
    
    # Valid: high == open
    record = OHLCRecord(
        timestamp=datetime(2024, 1, 1),
        open=100.0,
        high=100.0,
        low=99.0,
        close=100.0,
        volume=1000
    )
    assert record.high == record.open


def test_high_less_than_open_fails():
    """Test that high < open raises validation error."""
    with pytest.raises(ValidationError, match="High.*open"):
        OHLCRecord(
            timestamp=datetime(2024, 1, 1),
            open=100.0,
            high=95.0,  # Invalid: high < open
            low=94.0,
            close=98.0,
            volume=1000
        )


def test_high_greater_than_or_equal_to_close():
    """Test that high must be >= close."""
    # Valid: high > close
    record = OHLCRecord(
        timestamp=datetime(2024, 1, 1),
        open=100.0,
        high=105.0,
        low=99.0,
        close=103.0,
        volume=1000
    )
    assert record.high >= record.close
    
    # Valid: high == close
    record = OHLCRecord(
        timestamp=datetime(2024, 1, 1),
        open=100.0,
        high=100.0,
        low=99.0,
        close=100.0,
        volume=1000
    )
    assert record.high == record.close


def test_high_less_than_close_fails():
    """Test that high < close raises validation error."""
    with pytest.raises(ValidationError, match="High.*close"):
        OHLCRecord(
            timestamp=datetime(2024, 1, 1),
            open=100.0,
            high=102.0,
            low=99.0,
            close=105.0,  # Invalid: close > high
            volume=1000
        )


def test_low_less_than_or_equal_to_open():
    """Test that low must be <= open."""
    # Valid: low < open
    record = OHLCRecord(
        timestamp=datetime(2024, 1, 1),
        open=100.0,
        high=105.0,
        low=99.0,
        close=103.0,
        volume=1000
    )
    assert record.low <= record.open
    
    # Valid: low == open
    record = OHLCRecord(
        timestamp=datetime(2024, 1, 1),
        open=100.0,
        high=100.0,
        low=100.0,
        close=100.0,
        volume=1000
    )
    assert record.low == record.open


def test_low_greater_than_open_fails():
    """Test that low > open raises validation error."""
    with pytest.raises(ValidationError, match="Low.*open"):
        OHLCRecord(
            timestamp=datetime(2024, 1, 1),
            open=100.0,
            high=105.0,
            low=102.0,  # Invalid: low > open
            close=103.0,
            volume=1000
        )


def test_low_less_than_or_equal_to_close():
    """Test that low must be <= close."""
    # Valid: low < close
    record = OHLCRecord(
        timestamp=datetime(2024, 1, 1),
        open=100.0,
        high=105.0,
        low=99.0,
        close=103.0,
        volume=1000
    )
    assert record.low <= record.close


def test_low_greater_than_close_fails():
    """Test that low > close raises validation error."""
    # When low > both open and close, it will fail on the first check (low > open)
    with pytest.raises(ValidationError, match="Low.*(open|close)"):
        OHLCRecord(
            timestamp=datetime(2024, 1, 1),
            open=100.0,
            high=105.0,
            low=104.0,  # Invalid: low > close (and also > open)
            close=103.0,
            volume=1000
        )


def test_volume_must_be_non_negative():
    """Test that volume must be >= 0."""
    # Valid: volume = 0
    record = OHLCRecord(
        timestamp=datetime(2024, 1, 1),
        open=100.0,
        high=105.0,
        low=99.0,
        close=103.0,
        volume=0
    )
    assert record.volume == 0
    
    # Valid: volume > 0
    record = OHLCRecord(
        timestamp=datetime(2024, 1, 1),
        open=100.0,
        high=105.0,
        low=99.0,
        close=103.0,
        volume=1000
    )
    assert record.volume == 1000


def test_negative_volume_fails():
    """Test that negative volume raises validation error."""
    with pytest.raises(ValidationError, match="volume"):
        OHLCRecord(
            timestamp=datetime(2024, 1, 1),
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=-1000  # Invalid: negative volume
        )


def test_all_fields_required():
    """Test that all fields are required."""
    with pytest.raises(ValidationError):
        OHLCRecord(
            timestamp=datetime(2024, 1, 1),
            # Missing open, high, low, close, volume
        )


def test_prices_must_be_numeric():
    """Test that prices must be numeric types."""
    # Valid with float
    record = OHLCRecord(
        timestamp=datetime(2024, 1, 1),
        open=100.5,
        high=105.2,
        low=99.8,
        close=103.1,
        volume=1000
    )
    assert isinstance(record.open, float)
    
    # Valid with int (should convert to float)
    record = OHLCRecord(
        timestamp=datetime(2024, 1, 1),
        open=100,
        high=105,
        low=99,
        close=103,
        volume=1000
    )
    assert record.open == 100


def test_complex_validation_scenario():
    """Test a complex scenario with multiple constraints."""
    # Bullish candle: close > open, high at close, low below open
    record = OHLCRecord(
        timestamp=datetime(2024, 1, 1),
        open=100.0,
        high=110.0,
        low=95.0,
        close=108.0,
        volume=50000
    )
    
    assert record.high >= max(record.open, record.close)
    assert record.low <= min(record.open, record.close)
    assert record.volume >= 0

