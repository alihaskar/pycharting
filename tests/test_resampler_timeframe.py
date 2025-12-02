"""Tests for timeframe conversion and validation in resampler module."""
import pytest
from src.processing.resampler import (
    validate_timeframe,
    parse_timeframe,
    TimeframeValidationError
)


def test_validate_supported_timeframes():
    """Test validation of supported timeframe formats."""
    valid_timeframes = [
        "1min", "5min", "15min", "30min",
        "1h", "4h", "12h",
        "1D", "1W", "1M"
    ]
    
    for tf in valid_timeframes:
        # Should not raise any error
        validate_timeframe(tf)


def test_validate_invalid_timeframe_format():
    """Test that invalid timeframe formats raise errors."""
    invalid_timeframes = [
        "invalid",
        "5minutes",
        "1hour",
        "2x",
        "",
        "min5"
    ]
    
    for tf in invalid_timeframes:
        with pytest.raises(TimeframeValidationError):
            validate_timeframe(tf)


def test_validate_timeframe_case_insensitive():
    """Test that timeframe validation is case-insensitive."""
    # All these should be valid
    validate_timeframe("1Min")
    validate_timeframe("1MIN")
    validate_timeframe("1H")
    validate_timeframe("1h")
    validate_timeframe("1d")
    validate_timeframe("1D")


def test_validate_none_timeframe():
    """Test that None timeframe raises error."""
    with pytest.raises(TimeframeValidationError, match="cannot be None"):
        validate_timeframe(None)


def test_parse_minute_timeframes():
    """Test parsing minute-based timeframes."""
    assert parse_timeframe("1min") == "1min"
    assert parse_timeframe("5min") == "5min"
    assert parse_timeframe("15min") == "15min"
    assert parse_timeframe("30min") == "30min"


def test_parse_hour_timeframes():
    """Test parsing hour-based timeframes."""
    assert parse_timeframe("1h") == "1h"
    assert parse_timeframe("4h") == "4h"
    assert parse_timeframe("12h") == "12h"


def test_parse_daily_timeframes():
    """Test parsing daily timeframes."""
    assert parse_timeframe("1D") == "1D"
    assert parse_timeframe("1d") == "1D"  # Normalized to uppercase


def test_parse_weekly_timeframes():
    """Test parsing weekly timeframes."""
    assert parse_timeframe("1W") == "1W"
    assert parse_timeframe("1w") == "1W"


def test_parse_monthly_timeframes():
    """Test parsing monthly timeframes."""
    assert parse_timeframe("1M") == "1M"
    assert parse_timeframe("1m") == "1M"  # Normalized (but careful - could be minute)


def test_parse_timeframe_normalizes_case():
    """Test that parse_timeframe normalizes case for consistency."""
    # Minutes stay lowercase
    assert parse_timeframe("5MIN") == "5min"
    assert parse_timeframe("5Min") == "5min"
    
    # Hours stay lowercase
    assert parse_timeframe("1H") == "1h"
    assert parse_timeframe("4H") == "4h"
    
    # Days become uppercase
    assert parse_timeframe("1d") == "1D"


def test_parse_timeframe_strips_whitespace():
    """Test that whitespace is stripped from timeframe."""
    assert parse_timeframe(" 5min ") == "5min"
    assert parse_timeframe("  1h  ") == "1h"


def test_parse_common_trading_timeframes():
    """Test all common trading timeframes."""
    common_timeframes = {
        "1min": "1min",
        "3min": "3min",
        "5min": "5min",
        "15min": "15min",
        "30min": "30min",
        "1h": "1h",
        "2h": "2h",
        "4h": "4h",
        "6h": "6h",
        "12h": "12h",
        "1D": "1D",
        "1W": "1W"
    }
    
    for input_tf, expected in common_timeframes.items():
        assert parse_timeframe(input_tf) == expected


def test_validate_numeric_prefix():
    """Test that timeframes must start with a number."""
    with pytest.raises(TimeframeValidationError):
        validate_timeframe("min")
    
    with pytest.raises(TimeframeValidationError):
        validate_timeframe("hour")


def test_validate_supported_units():
    """Test that only supported time units are allowed."""
    # Valid units
    validate_timeframe("1min")
    validate_timeframe("1h")
    validate_timeframe("1D")
    validate_timeframe("1W")
    validate_timeframe("1M")
    
    # Invalid units
    with pytest.raises(TimeframeValidationError):
        validate_timeframe("1s")  # seconds not supported
    
    with pytest.raises(TimeframeValidationError):
        validate_timeframe("1Y")  # years not supported


def test_parse_ambiguous_m_as_month():
    """Test that standalone 'M' is treated as month, not minute."""
    # 1M should be month
    result = parse_timeframe("1M")
    assert result == "1M"
    
    # But 'min' should be minute
    result = parse_timeframe("1min")
    assert result == "1min"


def test_validate_reasonable_values():
    """Test validation of reasonable numeric values."""
    # Very large values should still be allowed (pandas will handle them)
    validate_timeframe("1000min")
    validate_timeframe("100h")


def test_parse_timeframe_error_for_invalid():
    """Test that parse_timeframe raises error for invalid formats."""
    with pytest.raises(TimeframeValidationError):
        parse_timeframe("invalid_format")
    
    with pytest.raises(TimeframeValidationError):
        parse_timeframe("5 minutes")  # No spaces allowed


def test_validate_and_parse_integration():
    """Test that validate and parse work together."""
    timeframe = "5min"
    
    # Should validate successfully
    validate_timeframe(timeframe)
    
    # Should parse to normalized form
    parsed = parse_timeframe(timeframe)
    assert parsed == "5min"
    
    # Parsed form should also validate
    validate_timeframe(parsed)

