"""
Integration tests for detector.py using mapper.py

Tests that detector.py correctly integrates with mapper.py for
column standardization and indicator detection.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime


class TestDetectorMapperIntegration:
    """Test integration of detector with mapper for column standardization"""
    
    def test_detector_uses_mapper_for_column_detection(self):
        """detector should use mapper.detect_columns() instead of own logic"""
        from src.python_api.detector import detect_ohlc_columns_via_mapper
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'High': [105.0, 106.0, 107.0, 108.0, 109.0],
            'Low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'Close': [103.0, 104.0, 105.0, 106.0, 107.0]
        }, index=dates)
        
        result = detect_ohlc_columns_via_mapper(df)
        
        # Should use mapper's detect_columns
        assert 'Open' in result.keys()
        assert result['Open'] == 'open'  # Maps actual col to standard name
    
    def test_detector_standardizes_dataframe_columns(self):
        """detector should return DataFrame with standardized column names"""
        from src.python_api.detector import standardize_dataframe
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'High': [105.0, 106.0, 107.0, 108.0, 109.0],
            'Low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'Close': [103.0, 104.0, 105.0, 106.0, 107.0]
        }, index=dates)
        
        result = standardize_dataframe(df)
        
        # Should have standardized lowercase names
        assert list(result.columns) == ['open', 'high', 'low', 'close']
    
    def test_detector_handles_custom_column_names(self):
        """detector should handle user-specified column mappings"""
        from src.python_api.detector import standardize_dataframe
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'price_open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'price_high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'price_low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'price_close': [103.0, 104.0, 105.0, 106.0, 107.0]
        }, index=dates)
        
        result = standardize_dataframe(
            df,
            open='price_open',
            high='price_high',
            low='price_low',
            close='price_close'
        )
        
        assert list(result.columns) == ['open', 'high', 'low', 'close']
    
    def test_detector_preserves_indicator_columns(self):
        """detector should preserve indicator columns during standardization"""
        from src.python_api.detector import standardize_dataframe
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'High': [105.0, 106.0, 107.0, 108.0, 109.0],
            'Low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'Close': [103.0, 104.0, 105.0, 106.0, 107.0],
            'rsi_14': [50.0, 55.0, 60.0, 65.0, 70.0],
            'sma_20': [101.0, 102.0, 103.0, 104.0, 105.0]
        }, index=dates)
        
        result = standardize_dataframe(df)
        
        # Should have OHLC + indicators
        assert 'open' in result.columns
        assert 'rsi_14' in result.columns
        assert 'sma_20' in result.columns
    
    def test_detector_integration_with_existing_functions(self):
        """Existing detect_indicator_columns should work with standardized data"""
        from src.python_api.detector import standardize_dataframe, detect_indicator_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'High': [105.0, 106.0, 107.0, 108.0, 109.0],
            'Low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'Close': [103.0, 104.0, 105.0, 106.0, 107.0],
            'rsi_14': [50.0, 55.0, 60.0, 65.0, 70.0],
            'sma_20': [101.0, 102.0, 103.0, 104.0, 105.0]
        }, index=dates)
        
        # Standardize first
        standardized = standardize_dataframe(df)
        
        # Detect indicators on standardized data
        ohlc_cols = {'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close'}
        indicators = detect_indicator_columns(standardized, ohlc_cols)
        
        assert 'rsi_14' in indicators
        assert 'sma_20' in indicators


class TestMapperErrorHandling:
    """Test that detector properly handles mapper errors"""
    
    def test_detector_raises_on_missing_columns(self):
        """detector should raise clear error when OHLC columns missing"""
        from src.python_api.detector import standardize_dataframe
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'price': [100.0, 101.0, 102.0, 103.0, 104.0],
            'volume': [1000, 1100, 1200, 1300, 1400]
        }, index=dates)
        
        with pytest.raises(Exception):  # Should raise ValueError or custom error
            standardize_dataframe(df)
    
    def test_detector_provides_helpful_error_messages(self):
        """detector errors should include suggestions from mapper"""
        from src.python_api.detector import standardize_dataframe
        from src.python_api.mapper import ColumnNotFoundError
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'opening': [100.0, 101.0, 102.0, 103.0, 104.0],
            'highest': [105.0, 106.0, 107.0, 108.0, 109.0],
            'lowest': [99.0, 100.0, 101.0, 102.0, 103.0],
            'closing': [103.0, 104.0, 105.0, 106.0, 107.0]
        }, index=dates)
        
        try:
            standardize_dataframe(df, open='open')  # Wrong column name
            assert False, "Should have raised error"
        except (ValueError, ColumnNotFoundError) as e:
            error_msg = str(e)
            # Should suggest similar columns
            assert 'opening' in error_msg or 'Did you mean' in error_msg


class TestBackwardCompatibility:
    """Test that existing detector functions still work"""
    
    def test_old_detect_ohlc_columns_still_works(self):
        """Original detect_ohlc_columns should remain functional"""
        from src.python_api.detector import detect_ohlc_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [103.0, 104.0, 105.0, 106.0, 107.0]
        }, index=dates)
        
        result = detect_ohlc_columns(df)
        
        assert result['open'] == 'open'
        assert result['high'] == 'high'
    
    def test_classify_indicators_still_works(self):
        """classify_indicators should work unchanged"""
        from src.python_api.detector import classify_indicators
        
        indicators = ['sma_20', 'rsi_14', 'ema_12', 'macd']
        overlays, subplots = classify_indicators(indicators)
        
        assert 'sma_20' in overlays
        assert 'ema_12' in overlays
        assert 'rsi_14' in subplots
        assert 'macd' in subplots

