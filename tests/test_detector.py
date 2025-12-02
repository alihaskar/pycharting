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
    require_ohlc_columns
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

