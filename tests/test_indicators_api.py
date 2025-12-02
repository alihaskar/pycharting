"""Tests for main calculate_indicator API function."""
import pytest
import pandas as pd
import numpy as np
from src.processing.indicators import calculate_indicator, IndicatorValidationError


def test_calculate_indicator_sma():
    """Test calculate_indicator with SMA type."""
    prices = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    
    result = calculate_indicator(prices, indicator_type="sma", params={"period": 3})
    
    assert len(result) == len(prices)
    assert not result.iloc[3:].isna().all()


def test_calculate_indicator_ema():
    """Test calculate_indicator with EMA type."""
    prices = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    
    result = calculate_indicator(prices, indicator_type="ema", params={"period": 3})
    
    assert len(result) == len(prices)
    assert not result.iloc[3:].isna().all()


def test_calculate_indicator_rsi():
    """Test calculate_indicator with RSI type."""
    prices = pd.Series([100 + i for i in range(20)])
    
    result = calculate_indicator(prices, indicator_type="rsi", params={"period": 14})
    
    assert len(result) == len(prices)
    assert not result.iloc[14:].isna().all()


def test_calculate_indicator_case_insensitive():
    """Test that indicator type is case-insensitive."""
    prices = pd.Series([1, 2, 3, 4, 5])
    
    result1 = calculate_indicator(prices, indicator_type="SMA", params={"period": 3})
    result2 = calculate_indicator(prices, indicator_type="sma", params={"period": 3})
    result3 = calculate_indicator(prices, indicator_type="Sma", params={"period": 3})
    
    pd.testing.assert_series_equal(result1, result2)
    pd.testing.assert_series_equal(result2, result3)


def test_calculate_indicator_invalid_type():
    """Test error handling for invalid indicator type."""
    prices = pd.Series([1, 2, 3, 4, 5])
    
    with pytest.raises(IndicatorValidationError, match="Unknown indicator"):
        calculate_indicator(prices, indicator_type="invalid", params={"period": 3})


def test_calculate_indicator_missing_params():
    """Test that missing parameters use defaults."""
    prices = pd.Series(range(1, 31))
    
    # Should use default period (20 for SMA)
    result = calculate_indicator(prices, indicator_type="sma", params={})
    assert len(result) == len(prices)
    assert not result.iloc[20:].isna().all()


def test_calculate_indicator_invalid_period():
    """Test error handling for invalid period."""
    prices = pd.Series([1, 2, 3, 4, 5])
    
    with pytest.raises(IndicatorValidationError, match="positive"):
        calculate_indicator(prices, indicator_type="sma", params={"period": 0})


def test_calculate_indicator_default_period():
    """Test default period values for indicators."""
    prices = pd.Series(range(1, 51))
    
    # Default RSI period is 14
    rsi = calculate_indicator(prices, indicator_type="rsi", params={})
    assert not rsi.iloc[14:].isna().all()


def test_calculate_indicator_returns_series():
    """Test that result is always a Series."""
    prices = pd.Series([1, 2, 3, 4, 5])
    
    result = calculate_indicator(prices, indicator_type="sma", params={"period": 3})
    
    assert isinstance(result, pd.Series)


def test_calculate_indicator_preserves_index():
    """Test that result preserves input index."""
    index = pd.date_range("2024-01-01", periods=10, freq="D")
    prices = pd.Series(range(1, 11), index=index)
    
    result = calculate_indicator(prices, indicator_type="sma", params={"period": 3})
    
    pd.testing.assert_index_equal(result.index, prices.index)


def test_calculate_indicator_none_params():
    """Test handling of None params."""
    prices = pd.Series(range(1, 21))
    
    # Should use defaults
    result = calculate_indicator(prices, indicator_type="rsi", params=None)
    assert not result.iloc[14:].isna().all()


def test_calculate_indicator_extra_params():
    """Test that extra parameters are ignored."""
    prices = pd.Series([1, 2, 3, 4, 5])
    
    # Extra params should not cause error
    result = calculate_indicator(
        prices, 
        indicator_type="sma", 
        params={"period": 3, "extra_param": "ignored"}
    )
    
    assert len(result) == len(prices)


def test_calculate_indicator_with_dataframe_column():
    """Test using a DataFrame column."""
    df = pd.DataFrame({
        "close": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "volume": [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    })
    
    result = calculate_indicator(df["close"], indicator_type="sma", params={"period": 3})
    
    assert len(result) == len(df)


def test_calculate_indicator_all_types():
    """Test all supported indicator types."""
    prices = pd.Series(range(1, 51))
    
    indicators = {
        "sma": {"period": 10},
        "ema": {"period": 10},
        "rsi": {"period": 14}
    }
    
    for ind_type, params in indicators.items():
        result = calculate_indicator(prices, indicator_type=ind_type, params=params)
        assert isinstance(result, pd.Series)
        assert len(result) == len(prices)

