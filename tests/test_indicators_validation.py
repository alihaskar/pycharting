"""Tests for indicator validation and NaN handling."""
import pytest
import pandas as pd
import numpy as np
from src.processing.indicators import (
    validate_indicator_input,
    check_sufficient_data,
    IndicatorValidationError
)


def test_validate_valid_input():
    """Test validation passes for valid input."""
    prices = pd.Series([1, 2, 3, 4, 5])
    
    # Should not raise any error
    validate_indicator_input(prices, period=3, indicator_name="TEST")


def test_validate_period_positive():
    """Test that period must be positive."""
    prices = pd.Series([1, 2, 3, 4, 5])
    
    with pytest.raises(IndicatorValidationError, match="positive"):
        validate_indicator_input(prices, period=0, indicator_name="TEST")
    
    with pytest.raises(IndicatorValidationError, match="positive"):
        validate_indicator_input(prices, period=-5, indicator_name="TEST")


def test_validate_input_is_series():
    """Test that input must be a pandas Series."""
    with pytest.raises(IndicatorValidationError, match="Series"):
        validate_indicator_input([1, 2, 3], period=2, indicator_name="TEST")
    
    with pytest.raises(IndicatorValidationError, match="Series"):
        validate_indicator_input(np.array([1, 2, 3]), period=2, indicator_name="TEST")


def test_validate_input_not_none():
    """Test that input cannot be None."""
    with pytest.raises(IndicatorValidationError, match="None"):
        validate_indicator_input(None, period=2, indicator_name="TEST")


def test_check_sufficient_data_true():
    """Test checking for sufficient data returns True when adequate."""
    prices = pd.Series([1, 2, 3, 4, 5])
    
    assert check_sufficient_data(prices, required=3)
    assert check_sufficient_data(prices, required=5)


def test_check_sufficient_data_false():
    """Test checking for sufficient data returns False when inadequate."""
    prices = pd.Series([1, 2, 3])
    
    assert not check_sufficient_data(prices, required=5)
    assert not check_sufficient_data(prices, required=10)


def test_check_sufficient_data_empty():
    """Test checking empty series."""
    prices = pd.Series([], dtype=float)
    
    assert not check_sufficient_data(prices, required=1)


def test_validate_with_all_nan():
    """Test validation with Series containing all NaN."""
    prices = pd.Series([np.nan, np.nan, np.nan])
    
    # Should pass validation (input is valid Series)
    # But check_sufficient_data should handle actual data availability
    validate_indicator_input(prices, period=2, indicator_name="TEST")


def test_indicator_validation_error_message():
    """Test that IndicatorValidationError provides clear messages."""
    prices = pd.Series([1, 2, 3])
    
    try:
        validate_indicator_input(prices, period=-1, indicator_name="RSI")
        assert False, "Should have raised error"
    except IndicatorValidationError as e:
        error_msg = str(e)
        assert "RSI" in error_msg
        assert "period" in error_msg.lower()


def test_validate_period_type():
    """Test that period must be an integer."""
    prices = pd.Series([1, 2, 3, 4, 5])
    
    with pytest.raises(IndicatorValidationError, match="integer"):
        validate_indicator_input(prices, period=3.5, indicator_name="TEST")
    
    with pytest.raises(IndicatorValidationError, match="integer"):
        validate_indicator_input(prices, period="5", indicator_name="TEST")


def test_validate_empty_series():
    """Test validation with empty series."""
    prices = pd.Series([], dtype=float)
    
    # Should pass validation (valid Series, even if empty)
    validate_indicator_input(prices, period=5, indicator_name="TEST")


def test_validate_single_value_series():
    """Test validation with single value series."""
    prices = pd.Series([42.0])
    
    # Should pass validation
    validate_indicator_input(prices, period=5, indicator_name="TEST")
    
    # But check_sufficient_data should return False
    assert not check_sufficient_data(prices, required=5)


def test_check_sufficient_data_exact():
    """Test with exact amount of required data."""
    prices = pd.Series([1, 2, 3, 4, 5])
    
    assert check_sufficient_data(prices, required=5)


def test_validate_nan_handling_consistency():
    """Test that validation is consistent across different NaN scenarios."""
    # Series with some NaN
    prices1 = pd.Series([1, np.nan, 3, 4, 5])
    validate_indicator_input(prices1, period=3, indicator_name="TEST")
    
    # Series starting with NaN
    prices2 = pd.Series([np.nan, 2, 3, 4, 5])
    validate_indicator_input(prices2, period=3, indicator_name="TEST")
    
    # Series ending with NaN
    prices3 = pd.Series([1, 2, 3, 4, np.nan])
    validate_indicator_input(prices3, period=3, indicator_name="TEST")

