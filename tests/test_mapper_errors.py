"""
Tests for mapper error handling and custom exceptions

Tests cover:
- Custom exception classes
- Column suggestion system
- Error message quality
- Helpful error scenarios
"""
import pytest
import pandas as pd
from datetime import datetime


class TestCustomExceptions:
    """Test custom exception classes"""
    
    def test_column_not_found_error_exists(self):
        """ColumnNotFoundError should be importable"""
        from src.charting.mapper import ColumnNotFoundError
        assert ColumnNotFoundError is not None
    
    def test_column_validation_error_exists(self):
        """ColumnValidationError should be importable"""
        from src.charting.mapper import ColumnValidationError
        assert ColumnValidationError is not None
    
    def test_column_not_found_raised_with_suggestions(self):
        """ColumnNotFoundError should include column suggestions"""
        from src.charting.mapper import map_columns, ColumnNotFoundError
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'opening': [100.0, 101.0, 102.0, 103.0, 104.0],  # Similar to 'open'
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [103.0, 104.0, 105.0, 106.0, 107.0]
        })
        df.set_index('timestamp', inplace=True)
        
        with pytest.raises(ColumnNotFoundError) as exc_info:
            map_columns(df, open='Open')  # Doesn't exist, but 'opening' is similar
        
        error_msg = str(exc_info.value)
        assert 'Open' in error_msg
        assert 'Did you mean' in error_msg or 'suggestions' in error_msg.lower()
    
    def test_column_validation_error_for_non_numeric(self):
        """ColumnValidationError should be raised for non-numeric columns"""
        from src.charting.mapper import map_columns, ColumnValidationError
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': ['100', '101', '102', '103', '104'],  # Strings!
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [103.0, 104.0, 105.0, 106.0, 107.0]
        })
        df.set_index('timestamp', inplace=True)
        
        with pytest.raises(ColumnValidationError) as exc_info:
            map_columns(df, open='open')
        
        error_msg = str(exc_info.value)
        assert 'numeric' in error_msg.lower()
        assert 'open' in error_msg


class TestColumnSuggestions:
    """Test column suggestion system"""
    
    def test_suggest_similar_column_names(self):
        """Should suggest similar column names using fuzzy matching"""
        from src.charting.mapper import suggest_columns
        
        available_columns = ['opening', 'closing', 'highest', 'lowest', 'vol']
        missing = 'open'
        
        suggestions = suggest_columns(missing, available_columns)
        
        assert len(suggestions) > 0
        assert 'opening' in suggestions  # Most similar to 'open'
    
    def test_suggest_case_variations(self):
        """Should suggest case variations"""
        from src.charting.mapper import suggest_columns
        
        available_columns = ['Open', 'HIGH', 'low', 'Close']
        missing = 'open'
        
        suggestions = suggest_columns(missing, available_columns)
        
        assert 'Open' in suggestions  # Case-insensitive match
    
    def test_suggest_returns_empty_when_no_matches(self):
        """Should return empty list when no similar columns"""
        from src.charting.mapper import suggest_columns
        
        available_columns = ['foo', 'bar', 'baz']
        missing = 'open'
        
        suggestions = suggest_columns(missing, available_columns)
        
        # Should return empty or very low similarity matches
        assert isinstance(suggestions, list)
    
    def test_suggest_limits_number_of_suggestions(self):
        """Should limit suggestions to reasonable number (e.g., 3)"""
        from src.charting.mapper import suggest_columns
        
        available_columns = ['opening', 'opener', 'opened', 'opens', 'reopen', 'close']
        missing = 'open'
        
        suggestions = suggest_columns(missing, available_columns, max_suggestions=3)
        
        assert len(suggestions) <= 3


class TestErrorMessageQuality:
    """Test error message quality and helpfulness"""
    
    def test_missing_column_error_includes_available_columns(self):
        """Error should list available columns"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'price_open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'price_high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'price_low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'price_close': [103.0, 104.0, 105.0, 106.0, 107.0]
        })
        df.set_index('timestamp', inplace=True)
        
        with pytest.raises(Exception) as exc_info:
            map_columns(df, open='open')  # Doesn't exist
        
        error_msg = str(exc_info.value)
        # Should show what columns ARE available
        assert 'price_open' in error_msg or 'Available columns' in error_msg
    
    def test_duplicate_mapping_error_shows_which_column(self):
        """Error should clearly identify the duplicate column"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'price': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0]
        })
        df.set_index('timestamp', inplace=True)
        
        with pytest.raises(Exception) as exc_info:
            map_columns(df, open='price', close='price')  # Duplicate!
        
        error_msg = str(exc_info.value)
        assert 'price' in error_msg  # Should mention the problematic column
        assert 'duplicate' in error_msg.lower()
    
    def test_auto_detection_failure_suggests_explicit_mapping(self):
        """When auto-detection fails, suggest using explicit parameters"""
        from src.charting.mapper import detect_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'price_open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'price_high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'price_low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'price_close': [103.0, 104.0, 105.0, 106.0, 107.0]
        })
        df.set_index('timestamp', inplace=True)
        
        with pytest.raises(Exception) as exc_info:
            detect_columns(df)  # Can't auto-detect these names
        
        error_msg = str(exc_info.value)
        # Should suggest using map_columns() explicitly
        assert 'map_columns' in error_msg or 'explicitly' in error_msg.lower()

