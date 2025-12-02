"""
Tests for DataFrame OHLC column detection.
Testing pattern matching with various naming conventions.
"""

import pytest
import pandas as pd
import numpy as np
from src.python_api.detector import (
    detect_ohlc_columns,
    validate_ohlc_columns,
    check_numeric_columns,
    check_null_values,
    check_ohlc_relationships,
    OHLCColumnsNotFoundError,
    AmbiguousColumnError,
    require_ohlc_columns,
    detect_indicator_columns,
    classify_indicators
)


class TestOHLCPatternMatching:
    """Test pattern matching for OHLC column detection."""
    
    def test_detect_standard_lowercase_columns(self):
        """Test detection with standard lowercase column names."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='1min'),
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [101.0, 102.0, 103.0, 104.0, 105.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        
        result = detect_ohlc_columns(df)
        
        assert result['open'] == 'open'
        assert result['high'] == 'high'
        assert result['low'] == 'low'
        assert result['close'] == 'close'
        assert result['volume'] == 'volume'
    
    def test_detect_uppercase_columns(self):
        """Test detection with uppercase column names."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='1min'),
            'OPEN': [100.0, 101.0, 102.0, 103.0, 104.0],
            'HIGH': [101.0, 102.0, 103.0, 104.0, 105.0],
            'LOW': [99.0, 100.0, 101.0, 102.0, 103.0],
            'CLOSE': [100.5, 101.5, 102.5, 103.5, 104.5],
            'VOLUME': [1000, 1100, 1200, 1300, 1400]
        })
        
        result = detect_ohlc_columns(df)
        
        assert result['open'] == 'OPEN'
        assert result['high'] == 'HIGH'
        assert result['low'] == 'LOW'
        assert result['close'] == 'CLOSE'
        assert result['volume'] == 'VOLUME'
    
    def test_detect_mixed_case_columns(self):
        """Test detection with mixed case column names."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='1min'),
            'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'High': [101.0, 102.0, 103.0, 104.0, 105.0],
            'Low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'Close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'Volume': [1000, 1100, 1200, 1300, 1400]
        })
        
        result = detect_ohlc_columns(df)
        
        assert result['open'] == 'Open'
        assert result['high'] == 'High'
        assert result['low'] == 'Low'
        assert result['close'] == 'Close'
        assert result['volume'] == 'Volume'
    
    def test_detect_abbreviated_single_letter_columns(self):
        """Test detection with single letter abbreviations."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='1min'),
            'o': [100.0, 101.0, 102.0, 103.0, 104.0],
            'h': [101.0, 102.0, 103.0, 104.0, 105.0],
            'l': [99.0, 100.0, 101.0, 102.0, 103.0],
            'c': [100.5, 101.5, 102.5, 103.5, 104.5],
            'v': [1000, 1100, 1200, 1300, 1400]
        })
        
        result = detect_ohlc_columns(df)
        
        assert result['open'] == 'o'
        assert result['high'] == 'h'
        assert result['low'] == 'l'
        assert result['close'] == 'c'
        assert result['volume'] == 'v'
    
    def test_detect_abbreviated_uppercase_single_letter(self):
        """Test detection with uppercase single letter abbreviations."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='1min'),
            'O': [100.0, 101.0, 102.0, 103.0, 104.0],
            'H': [101.0, 102.0, 103.0, 104.0, 105.0],
            'L': [99.0, 100.0, 101.0, 102.0, 103.0],
            'C': [100.5, 101.5, 102.5, 103.5, 104.5],
            'V': [1000, 1100, 1200, 1300, 1400]
        })
        
        result = detect_ohlc_columns(df)
        
        assert result['open'] == 'O'
        assert result['high'] == 'H'
        assert result['low'] == 'L'
        assert result['close'] == 'C'
        assert result['volume'] == 'V'
    
    def test_detect_volume_variations(self):
        """Test detection of volume column with various names."""
        # Test 'vol'
        df_vol = pd.DataFrame({
            'open': [100.0], 'high': [101.0], 'low': [99.0], 'close': [100.5],
            'vol': [1000]
        })
        result = detect_ohlc_columns(df_vol)
        assert result['volume'] == 'vol'
        
        # Test 'Vol'
        df_vol_cap = pd.DataFrame({
            'open': [100.0], 'high': [101.0], 'low': [99.0], 'close': [100.5],
            'Vol': [1000]
        })
        result = detect_ohlc_columns(df_vol_cap)
        assert result['volume'] == 'Vol'
        
        # Test 'VOL'
        df_vol_upper = pd.DataFrame({
            'open': [100.0], 'high': [101.0], 'low': [99.0], 'close': [100.5],
            'VOL': [1000]
        })
        result = detect_ohlc_columns(df_vol_upper)
        assert result['volume'] == 'VOL'
    
    def test_detect_without_volume_column(self):
        """Test detection when volume column is missing."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='1min'),
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [101.0, 102.0, 103.0, 104.0, 105.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5]
        })
        
        result = detect_ohlc_columns(df)
        
        # Should detect OHLC but not volume
        assert 'open' in result
        assert 'high' in result
        assert 'low' in result
        assert 'close' in result
        assert 'volume' not in result
    
    def test_detect_with_extra_columns(self):
        """Test detection with extra indicator columns present."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='1min'),
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [101.0, 102.0, 103.0, 104.0, 105.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'volume': [1000, 1100, 1200, 1300, 1400],
            'rsi_14': [45.0, 46.0, 47.0, 48.0, 49.0],
            'sma_20': [100.2, 100.8, 101.2, 101.8, 102.2]
        })
        
        result = detect_ohlc_columns(df)
        
        # Should only detect OHLC, not indicators
        assert len(result) == 5  # open, high, low, close, volume
        assert 'rsi_14' not in result.values()
        assert 'sma_20' not in result.values()
    
    def test_returns_empty_dict_when_no_ohlc_columns(self):
        """Test that function returns empty dict when no OHLC columns found."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='1min'),
            'price': [100.0, 101.0, 102.0, 103.0, 104.0],
            'quantity': [1000, 1100, 1200, 1300, 1400]
        })
        
        result = detect_ohlc_columns(df)
        
        assert isinstance(result, dict)
        assert len(result) == 0


class TestOHLCValidation:
    """Test validation of detected OHLC columns."""
    
    def test_validate_numeric_columns_valid(self):
        """Test validation passes for numeric columns."""
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0],
            'high': [101.0, 102.0, 103.0],
            'low': [99.0, 100.0, 101.0],
            'close': [100.5, 101.5, 102.5],
            'volume': [1000, 1100, 1200]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        # Should not raise any exception
        check_numeric_columns(df, ohlc_cols)
    
    def test_validate_numeric_columns_invalid_string_data(self):
        """Test validation fails for string data in OHLC columns."""
        df = pd.DataFrame({
            'open': ['100', '101', '102'],  # Strings instead of numbers
            'high': [101.0, 102.0, 103.0],
            'low': [99.0, 100.0, 101.0],
            'close': [100.5, 101.5, 102.5]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        with pytest.raises(ValueError, match="non-numeric|string"):
            check_numeric_columns(df, ohlc_cols)
    
    def test_validate_numeric_columns_integer_accepted(self):
        """Test validation accepts integer types."""
        df = pd.DataFrame({
            'open': [100, 101, 102],  # Integers
            'high': [101, 102, 103],
            'low': [99, 100, 101],
            'close': [100, 101, 102],
            'volume': [1000, 1100, 1200]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        # Should not raise exception for integers
        check_numeric_columns(df, ohlc_cols)
    
    def test_check_null_values_no_nulls(self):
        """Test null check passes when no null values."""
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0],
            'high': [101.0, 102.0, 103.0],
            'low': [99.0, 100.0, 101.0],
            'close': [100.5, 101.5, 102.5]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        result = check_null_values(df, ohlc_cols)
        assert result is True
    
    def test_check_null_values_with_nans(self):
        """Test null check detects NaN values."""
        df = pd.DataFrame({
            'open': [100.0, np.nan, 102.0],
            'high': [101.0, 102.0, 103.0],
            'low': [99.0, 100.0, 101.0],
            'close': [100.5, 101.5, 102.5]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        result = check_null_values(df, ohlc_cols)
        assert result is False
    
    def test_check_null_values_with_none(self):
        """Test null check detects None values."""
        df = pd.DataFrame({
            'open': [100.0, 101.0, None],
            'high': [101.0, 102.0, 103.0],
            'low': [99.0, 100.0, 101.0],
            'close': [100.5, 101.5, 102.5]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        result = check_null_values(df, ohlc_cols)
        assert result is False
    
    def test_check_ohlc_relationships_valid(self):
        """Test OHLC relationship validation passes for valid data."""
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0],
            'high': [101.0, 102.0, 103.0],  # high >= all others
            'low': [99.0, 100.0, 101.0],    # low <= all others
            'close': [100.5, 101.5, 102.5]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        # Should not raise exception
        check_ohlc_relationships(df, ohlc_cols)
    
    def test_check_ohlc_relationships_high_less_than_low(self):
        """Test validation fails when high < low."""
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0],
            'high': [98.0, 102.0, 103.0],   # First high < low (invalid!)
            'low': [99.0, 100.0, 101.0],
            'close': [100.5, 101.5, 102.5]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        with pytest.raises(ValueError, match="high.*less than.*low|invalid.*relationship"):
            check_ohlc_relationships(df, ohlc_cols)
    
    def test_check_ohlc_relationships_high_equal_to_low(self):
        """Test validation passes when high == low (valid for no price movement)."""
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0],
            'high': [100.0, 101.0, 102.0],  # high == low (valid)
            'low': [100.0, 101.0, 102.0],
            'close': [100.0, 101.0, 102.0]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        # Should not raise exception
        check_ohlc_relationships(df, ohlc_cols)
    
    def test_check_ohlc_relationships_open_outside_range(self):
        """Test validation fails when open is outside [low, high] range."""
        df = pd.DataFrame({
            'open': [105.0, 101.0, 102.0],  # First open > high (invalid!)
            'high': [101.0, 102.0, 103.0],
            'low': [99.0, 100.0, 101.0],
            'close': [100.5, 101.5, 102.5]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        with pytest.raises(ValueError, match="open.*outside.*range|invalid.*relationship"):
            check_ohlc_relationships(df, ohlc_cols)
    
    def test_check_ohlc_relationships_close_outside_range(self):
        """Test validation fails when close is outside [low, high] range."""
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0],
            'high': [101.0, 102.0, 103.0],
            'low': [99.0, 100.0, 101.0],
            'close': [98.0, 101.5, 102.5]  # First close < low (invalid!)
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        with pytest.raises(ValueError, match="close.*outside.*range|invalid.*relationship"):
            check_ohlc_relationships(df, ohlc_cols)
    
    def test_validate_ohlc_columns_comprehensive(self):
        """Test complete validation pipeline."""
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0],
            'high': [101.0, 102.0, 103.0],
            'low': [99.0, 100.0, 101.0],
            'close': [100.5, 101.5, 102.5],
            'volume': [1000, 1100, 1200]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        # Should pass all validation checks
        result = validate_ohlc_columns(df, ohlc_cols)
        assert result is True
    
    def test_validate_negative_volume(self):
        """Test validation fails for negative volume."""
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0],
            'high': [101.0, 102.0, 103.0],
            'low': [99.0, 100.0, 101.0],
            'close': [100.5, 101.5, 102.5],
            'volume': [1000, -100, 1200]  # Negative volume (invalid!)
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        with pytest.raises(ValueError, match="negative.*volume|volume.*negative"):
            validate_ohlc_columns(df, ohlc_cols)


class TestErrorHandling:
    """Test custom exception handling for missing/invalid columns."""
    
    def test_ohlc_columns_not_found_error_creation(self):
        """Test OHLCColumnsNotFoundError can be created."""
        missing = ['open', 'high']
        error = OHLCColumnsNotFoundError(missing)
        
        assert isinstance(error, Exception)
        assert 'open' in str(error)
        assert 'high' in str(error)
    
    def test_ambiguous_column_error_creation(self):
        """Test AmbiguousColumnError can be created."""
        candidates = ['open', 'Open', 'OPEN']
        error = AmbiguousColumnError('open', candidates)
        
        assert isinstance(error, Exception)
        assert 'open' in str(error).lower()
        assert 'open' in str(error) or 'Open' in str(error)
    
    def test_require_ohlc_columns_all_present(self):
        """Test require_ohlc_columns passes when all required columns present."""
        df = pd.DataFrame({
            'open': [100.0], 'high': [101.0], 'low': [99.0], 'close': [100.5]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        # Should not raise exception
        require_ohlc_columns(ohlc_cols)
    
    def test_require_ohlc_columns_missing_one_required(self):
        """Test require_ohlc_columns raises when required column missing."""
        df = pd.DataFrame({
            'high': [101.0], 'low': [99.0], 'close': [100.5]
            # Missing 'open'
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        with pytest.raises(OHLCColumnsNotFoundError) as exc_info:
            require_ohlc_columns(ohlc_cols)
        
        # Check error message mentions missing column
        assert 'open' in str(exc_info.value).lower()
    
    def test_require_ohlc_columns_missing_multiple_required(self):
        """Test require_ohlc_columns raises when multiple columns missing."""
        df = pd.DataFrame({
            'low': [99.0], 'close': [100.5]
            # Missing 'open' and 'high'
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        with pytest.raises(OHLCColumnsNotFoundError) as exc_info:
            require_ohlc_columns(ohlc_cols)
        
        error_msg = str(exc_info.value).lower()
        assert 'open' in error_msg
        assert 'high' in error_msg
    
    def test_require_ohlc_columns_missing_all_required(self):
        """Test require_ohlc_columns raises when no OHLC columns found."""
        df = pd.DataFrame({
            'price': [100.0], 'quantity': [1000]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        with pytest.raises(OHLCColumnsNotFoundError) as exc_info:
            require_ohlc_columns(ohlc_cols)
        
        error_msg = str(exc_info.value)
        # Should list all required columns
        assert 'open' in error_msg.lower()
        assert 'high' in error_msg.lower()
        assert 'low' in error_msg.lower()
        assert 'close' in error_msg.lower()
    
    def test_require_ohlc_columns_volume_optional(self):
        """Test require_ohlc_columns doesn't require volume column."""
        df = pd.DataFrame({
            'open': [100.0], 'high': [101.0], 'low': [99.0], 'close': [100.5]
            # No volume - should be okay
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        # Should not raise exception even without volume
        require_ohlc_columns(ohlc_cols)
    
    def test_error_message_includes_suggestions(self):
        """Test error messages include helpful suggestions."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=3, freq='1min'),
            'price': [100.0, 101.0, 102.0],
            'quantity': [1000, 1100, 1200]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        with pytest.raises(OHLCColumnsNotFoundError) as exc_info:
            require_ohlc_columns(ohlc_cols)
        
        error_msg = str(exc_info.value)
        # Should include helpful suggestion
        assert 'rename' in error_msg.lower() or 'column' in error_msg.lower()
    
    def test_empty_dataframe_handling(self):
        """Test graceful handling of empty DataFrame."""
        df = pd.DataFrame()
        
        ohlc_cols = detect_ohlc_columns(df)
        
        with pytest.raises(OHLCColumnsNotFoundError):
            require_ohlc_columns(ohlc_cols)


class TestIndicatorDetection:
    """Test detection and classification of indicator columns."""
    
    def test_detect_indicator_columns_with_standard_indicators(self):
        """Test detection of indicator columns alongside OHLC."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=3, freq='1min'),
            'open': [100.0, 101.0, 102.0],
            'high': [101.0, 102.0, 103.0],
            'low': [99.0, 100.0, 101.0],
            'close': [100.5, 101.5, 102.5],
            'volume': [1000, 1100, 1200],
            'rsi_14': [45.0, 46.0, 47.0],
            'sma_20': [100.2, 100.8, 101.2],
            'ema_12': [100.3, 100.9, 101.3]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        indicators = detect_indicator_columns(df, ohlc_cols)
        
        assert 'rsi_14' in indicators
        assert 'sma_20' in indicators
        assert 'ema_12' in indicators
        assert len(indicators) == 3
    
    def test_detect_indicator_columns_excludes_ohlc(self):
        """Test that OHLC columns are excluded from indicators."""
        df = pd.DataFrame({
            'open': [100.0], 'high': [101.0], 'low': [99.0], 'close': [100.5],
            'volume': [1000],
            'rsi_14': [45.0], 'sma_20': [100.2]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        indicators = detect_indicator_columns(df, ohlc_cols)
        
        # OHLC columns should not be in indicators
        assert 'open' not in indicators
        assert 'high' not in indicators
        assert 'low' not in indicators
        assert 'close' not in indicators
        assert 'volume' not in indicators
    
    def test_detect_indicator_columns_excludes_timestamp(self):
        """Test that timestamp column is excluded from indicators."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=3, freq='1min'),
            'open': [100.0, 101.0, 102.0],
            'high': [101.0, 102.0, 103.0],
            'low': [99.0, 100.0, 101.0],
            'close': [100.5, 101.5, 102.5],
            'rsi_14': [45.0, 46.0, 47.0]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        indicators = detect_indicator_columns(df, ohlc_cols)
        
        assert 'timestamp' not in indicators
        assert 'rsi_14' in indicators
    
    def test_detect_indicator_columns_no_indicators(self):
        """Test with DataFrame containing only OHLC columns."""
        df = pd.DataFrame({
            'open': [100.0], 'high': [101.0], 'low': [99.0], 'close': [100.5]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        indicators = detect_indicator_columns(df, ohlc_cols)
        
        assert len(indicators) == 0
        assert isinstance(indicators, list)
    
    def test_detect_indicator_columns_mixed_case(self):
        """Test with mixed case OHLC column names."""
        df = pd.DataFrame({
            'Open': [100.0], 'High': [101.0], 'Low': [99.0], 'Close': [100.5],
            'RSI': [45.0], 'SMA': [100.2]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        indicators = detect_indicator_columns(df, ohlc_cols)
        
        # Should detect indicators regardless of case
        assert 'RSI' in indicators
        assert 'SMA' in indicators
        assert 'Open' not in indicators
    
    def test_detect_indicator_columns_with_custom_names(self):
        """Test with custom indicator names."""
        df = pd.DataFrame({
            'open': [100.0], 'high': [101.0], 'low': [99.0], 'close': [100.5],
            'my_custom_indicator': [45.0],
            'another_signal': [100.2]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        indicators = detect_indicator_columns(df, ohlc_cols)
        
        assert 'my_custom_indicator' in indicators
        assert 'another_signal' in indicators
        assert len(indicators) == 2


class TestIndicatorClassification:
    """Test classification of indicators as overlay or subplot."""
    
    def test_classify_sma_as_overlay(self):
        """Test that SMA indicators are classified as overlay."""
        indicators = ['sma_20', 'sma_50', 'sma_200']
        
        overlays, subplots = classify_indicators(indicators)
        
        assert 'sma_20' in overlays
        assert 'sma_50' in overlays
        assert 'sma_200' in overlays
        assert len(overlays) == 3
        assert len(subplots) == 0
    
    def test_classify_ema_as_overlay(self):
        """Test that EMA indicators are classified as overlay."""
        indicators = ['ema_12', 'ema_26', 'EMA_50']
        
        overlays, subplots = classify_indicators(indicators)
        
        assert 'ema_12' in overlays
        assert 'ema_26' in overlays
        assert 'EMA_50' in overlays
        assert len(overlays) == 3
    
    def test_classify_ma_as_overlay(self):
        """Test that generic MA indicators are classified as overlay."""
        indicators = ['ma_10', 'MA_20', 'moving_average_50']
        
        overlays, subplots = classify_indicators(indicators)
        
        assert 'ma_10' in overlays
        assert 'MA_20' in overlays
        assert 'moving_average_50' in overlays
    
    def test_classify_vwap_as_overlay(self):
        """Test that VWAP indicators are classified as overlay."""
        indicators = ['vwap', 'VWAP', 'vwap_daily']
        
        overlays, subplots = classify_indicators(indicators)
        
        assert 'vwap' in overlays
        assert 'VWAP' in overlays
        assert 'vwap_daily' in overlays
    
    def test_classify_bollinger_bands_as_overlay(self):
        """Test that Bollinger Bands indicators are classified as overlay."""
        indicators = ['bb_upper', 'bb_lower', 'bb_middle', 'bollinger_bands']
        
        overlays, subplots = classify_indicators(indicators)
        
        assert 'bb_upper' in overlays
        assert 'bb_lower' in overlays
        assert 'bb_middle' in overlays
        assert 'bollinger_bands' in overlays
    
    def test_classify_rsi_as_subplot(self):
        """Test that RSI indicators are classified as subplot."""
        indicators = ['rsi_14', 'RSI_21', 'rsi']
        
        overlays, subplots = classify_indicators(indicators)
        
        assert 'rsi_14' in subplots
        assert 'RSI_21' in subplots
        assert 'rsi' in subplots
        assert len(subplots) == 3
        assert len(overlays) == 0
    
    def test_classify_macd_as_subplot(self):
        """Test that MACD indicators are classified as subplot."""
        indicators = ['macd', 'macd_signal', 'macd_histogram', 'MACD']
        
        overlays, subplots = classify_indicators(indicators)
        
        assert 'macd' in subplots
        assert 'macd_signal' in subplots
        assert 'macd_histogram' in subplots
        assert 'MACD' in subplots
    
    def test_classify_stochastic_as_subplot(self):
        """Test that Stochastic indicators are classified as subplot."""
        indicators = ['stoch_k', 'stoch_d', 'stochastic']
        
        overlays, subplots = classify_indicators(indicators)
        
        assert 'stoch_k' in subplots
        assert 'stoch_d' in subplots
        assert 'stochastic' in subplots
    
    def test_classify_obv_as_subplot(self):
        """Test that OBV indicators are classified as subplot."""
        indicators = ['obv', 'OBV', 'obv_signal']
        
        overlays, subplots = classify_indicators(indicators)
        
        assert 'obv' in subplots
        assert 'OBV' in subplots
        assert 'obv_signal' in subplots
    
    def test_classify_cci_as_subplot(self):
        """Test that CCI indicators are classified as subplot."""
        indicators = ['cci', 'CCI_20', 'commodity_channel_index']
        
        overlays, subplots = classify_indicators(indicators)
        
        assert 'cci' in subplots
        assert 'CCI_20' in subplots
        assert 'commodity_channel_index' in subplots
    
    def test_classify_mixed_indicators(self):
        """Test classification of mixed overlay and subplot indicators."""
        indicators = [
            'sma_20', 'ema_12',  # Overlays
            'rsi_14', 'macd', 'stoch_k'  # Subplots
        ]
        
        overlays, subplots = classify_indicators(indicators)
        
        # Check overlays
        assert 'sma_20' in overlays
        assert 'ema_12' in overlays
        assert len(overlays) == 2
        
        # Check subplots
        assert 'rsi_14' in subplots
        assert 'macd' in subplots
        assert 'stoch_k' in subplots
        assert len(subplots) == 3
    
    def test_classify_case_insensitive(self):
        """Test that classification is case-insensitive."""
        indicators_lower = ['sma_20', 'rsi_14']
        indicators_upper = ['SMA_20', 'RSI_14']
        indicators_mixed = ['Sma_20', 'Rsi_14']
        
        overlays1, subplots1 = classify_indicators(indicators_lower)
        overlays2, subplots2 = classify_indicators(indicators_upper)
        overlays3, subplots3 = classify_indicators(indicators_mixed)
        
        # All should classify the same way
        assert len(overlays1) == len(overlays2) == len(overlays3) == 1
        assert len(subplots1) == len(subplots2) == len(subplots3) == 1
    
    def test_classify_empty_list(self):
        """Test classification with empty indicator list."""
        indicators = []
        
        overlays, subplots = classify_indicators(indicators)
        
        assert overlays == []
        assert subplots == []
        assert isinstance(overlays, list)
        assert isinstance(subplots, list)


class TestDefaultClassification:
    """Test default classification behavior for unknown indicators."""
    
    def test_unknown_indicator_defaults_to_subplot(self):
        """Test that unknown indicators are classified as subplot by default."""
        indicators = ['my_custom_indicator', 'unknown_signal', 'weird_metric']
        
        overlays, subplots = classify_indicators(indicators)
        
        # All unknown indicators should be in subplots
        assert len(overlays) == 0
        assert len(subplots) == 3
        assert 'my_custom_indicator' in subplots
        assert 'unknown_signal' in subplots
        assert 'weird_metric' in subplots
    
    def test_mixed_known_and_unknown_indicators(self):
        """Test classification with mix of known and unknown indicators."""
        indicators = [
            'sma_20',  # Known overlay
            'custom_indicator',  # Unknown -> subplot
            'rsi_14',  # Known subplot
            'my_signal'  # Unknown -> subplot
        ]
        
        overlays, subplots = classify_indicators(indicators)
        
        # Check overlay
        assert 'sma_20' in overlays
        assert len(overlays) == 1
        
        # Check subplots (known + unknown)
        assert 'rsi_14' in subplots
        assert 'custom_indicator' in subplots
        assert 'my_signal' in subplots
        assert len(subplots) == 3
    
    def test_numbers_in_unknown_indicator_names(self):
        """Test unknown indicators with numbers default to subplot."""
        indicators = ['indicator_1', 'signal_2', 'metric_3']
        
        overlays, subplots = classify_indicators(indicators)
        
        assert len(overlays) == 0
        assert len(subplots) == 3
        assert all(ind in subplots for ind in indicators)
    
    def test_special_characters_in_unknown_indicators(self):
        """Test unknown indicators with special characters."""
        indicators = ['custom-indicator', 'signal.value', 'metric_test']
        
        overlays, subplots = classify_indicators(indicators)
        
        # All should default to subplot
        assert len(overlays) == 0
        assert len(subplots) == 3
    
    def test_default_classification_safety(self):
        """Test that defaulting to subplot is safer than overlay."""
        # This is a design decision test: unknown indicators go to subplot
        # to avoid accidentally overlaying on price chart
        indicators = ['could_be_anything', 'totally_unknown']
        
        overlays, subplots = classify_indicators(indicators)
        
        # Verify they're NOT in overlays (safety)
        assert len(overlays) == 0
        # Verify they ARE in subplots
        assert 'could_be_anything' in subplots
        assert 'totally_unknown' in subplots
    
    def test_partial_match_still_requires_full_pattern(self):
        """Test that partial keyword matches don't classify as overlay."""
        # These contain 'ma' but not as part of moving average
        indicators = ['max_value', 'image_data', 'format_string']
        
        overlays, subplots = classify_indicators(indicators)
        
        # These should NOT match 'ma' pattern and default to subplot
        assert 'image_data' in subplots
        assert 'format_string' in subplots
        # 'max_value' might match 'ma' pattern depending on implementation
    
    def test_single_letter_indicators(self):
        """Test single letter indicator names default to subplot."""
        indicators = ['x', 'y', 'z']
        
        overlays, subplots = classify_indicators(indicators)
        
        # Single letters don't match any known pattern -> subplot
        assert len(overlays) == 0
        assert all(ind in subplots for ind in indicators)


class TestIntegrationWorkflow:
    """Test complete workflow from DataFrame to classified indicators."""
    
    def test_complete_pipeline_standard_data(self):
        """Test end-to-end workflow with standard OHLC + indicators."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='1min'),
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [101.0, 102.0, 103.0, 104.0, 105.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'volume': [1000, 1100, 1200, 1300, 1400],
            'sma_20': [100.2, 100.8, 101.2, 101.8, 102.2],
            'ema_12': [100.3, 100.9, 101.3, 101.9, 102.3],
            'rsi_14': [45.0, 46.0, 47.0, 48.0, 49.0],
            'macd': [0.5, 0.6, 0.7, 0.8, 0.9]
        })
        
        # Step 1: Detect OHLC columns
        ohlc_cols = detect_ohlc_columns(df)
        assert len(ohlc_cols) == 5  # open, high, low, close, volume
        
        # Step 2: Detect indicator columns
        indicators = detect_indicator_columns(df, ohlc_cols)
        assert len(indicators) == 4
        assert 'sma_20' in indicators
        assert 'ema_12' in indicators
        assert 'rsi_14' in indicators
        assert 'macd' in indicators
        
        # Step 3: Classify indicators
        overlays, subplots = classify_indicators(indicators)
        assert 'sma_20' in overlays
        assert 'ema_12' in overlays
        assert 'rsi_14' in subplots
        assert 'macd' in subplots
    
    def test_complete_pipeline_mixed_case(self):
        """Test workflow with mixed case column names."""
        df = pd.DataFrame({
            'Open': [100.0], 'High': [101.0], 'Low': [99.0], 'Close': [100.5],
            'Volume': [1000],
            'SMA_20': [100.2], 'RSI_14': [45.0]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        indicators = detect_indicator_columns(df, ohlc_cols)
        overlays, subplots = classify_indicators(indicators)
        
        assert 'SMA_20' in overlays
        assert 'RSI_14' in subplots
    
    def test_complete_pipeline_custom_indicators(self):
        """Test workflow with custom/unknown indicators."""
        df = pd.DataFrame({
            'open': [100.0], 'high': [101.0], 'low': [99.0], 'close': [100.5],
            'sma_20': [100.2],
            'my_custom_signal': [45.0],
            'another_metric': [0.5]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        indicators = detect_indicator_columns(df, ohlc_cols)
        overlays, subplots = classify_indicators(indicators)
        
        # Known overlay
        assert 'sma_20' in overlays
        # Unknown indicators should default to subplot
        assert 'my_custom_signal' in subplots
        assert 'another_metric' in subplots
    
    def test_complete_pipeline_no_indicators(self):
        """Test workflow with DataFrame containing only OHLC."""
        df = pd.DataFrame({
            'open': [100.0], 'high': [101.0], 'low': [99.0], 'close': [100.5]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        indicators = detect_indicator_columns(df, ohlc_cols)
        overlays, subplots = classify_indicators(indicators)
        
        assert len(indicators) == 0
        assert len(overlays) == 0
        assert len(subplots) == 0
    
    def test_complete_pipeline_abbreviated_ohlc(self):
        """Test workflow with abbreviated OHLC column names."""
        df = pd.DataFrame({
            'o': [100.0], 'h': [101.0], 'l': [99.0], 'c': [100.5], 'v': [1000],
            'sma': [100.2], 'rsi': [45.0]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        indicators = detect_indicator_columns(df, ohlc_cols)
        overlays, subplots = classify_indicators(indicators)
        
        # Verify OHLC detected
        assert len(ohlc_cols) == 5
        # Verify indicators detected
        assert 'sma' in indicators
        assert 'rsi' in indicators
        # Verify classification
        assert 'sma' in overlays
        assert 'rsi' in subplots
    
    def test_complete_pipeline_validates_data(self):
        """Test that complete pipeline includes validation."""
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0],
            'high': [101.0, 102.0, 103.0],
            'low': [99.0, 100.0, 101.0],
            'close': [100.5, 101.5, 102.5],
            'sma_20': [100.2, 100.8, 101.2]
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        
        # Should be able to validate OHLC columns
        is_valid = validate_ohlc_columns(df, ohlc_cols)
        assert is_valid is True
        
        # Then proceed with indicator detection
        indicators = detect_indicator_columns(df, ohlc_cols)
        overlays, subplots = classify_indicators(indicators)
        
        assert 'sma_20' in overlays
    
    def test_complete_pipeline_preserves_column_names(self):
        """Test that original column names are preserved throughout pipeline."""
        df = pd.DataFrame({
            'Open_Price': [100.0],  # Will not match pattern
            'open': [100.0], 'high': [101.0], 'low': [99.0], 'close': [100.5],
            'My_SMA_20': [100.2],  # Contains 'sma'
            'RSI_Custom_14': [45.0]  # Contains 'rsi'
        })
        
        ohlc_cols = detect_ohlc_columns(df)
        indicators = detect_indicator_columns(df, ohlc_cols)
        overlays, subplots = classify_indicators(indicators)
        
        # Original names should be preserved
        assert 'My_SMA_20' in overlays
        assert 'RSI_Custom_14' in subplots
        # Non-matching column should be in indicators
        assert 'Open_Price' in indicators

