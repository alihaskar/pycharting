"""
Tests for indicator column detection in processor.
Testing detection of pre-existing indicator columns in CSV files.
"""

import pytest
import pandas as pd
import numpy as np
from src.api.processor import detect_indicator_columns


class TestIndicatorColumnDetection:
    """Test detection of indicator columns in DataFrames."""
    
    def test_detect_indicators_basic(self):
        """Test basic indicator column detection."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=3),
            'open': [100, 101, 102],
            'high': [102, 103, 104],
            'low': [99, 100, 101],
            'close': [101, 102, 103],
            'volume': [1000, 1100, 1200],
            'rsi_14': [45, 46, 47],
            'sma_20': [100.5, 101.5, 102.5]
        })
        
        indicators = detect_indicator_columns(df)
        
        assert 'rsi_14' in indicators
        assert 'sma_20' in indicators
        assert len(indicators) == 2
    
    def test_detect_indicators_no_indicators(self):
        """Test detection when CSV has only OHLCV data."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=3),
            'open': [100, 101, 102],
            'high': [102, 103, 104],
            'low': [99, 100, 101],
            'close': [101, 102, 103],
            'volume': [1000, 1100, 1200]
        })
        
        indicators = detect_indicator_columns(df)
        
        assert indicators == []
    
    def test_detect_indicators_case_insensitive(self):
        """Test detection with various column name cases."""
        df = pd.DataFrame({
            'Timestamp': pd.date_range('2024-01-01', periods=3),
            'Open': [100, 101, 102],
            'High': [102, 103, 104],
            'Low': [99, 100, 101],
            'Close': [101, 102, 103],
            'Volume': [1000, 1100, 1200],
            'rsi_14': [45, 46, 47]
        })
        
        indicators = detect_indicator_columns(df)
        
        assert 'rsi_14' in indicators
        assert len(indicators) == 1
    
    def test_detect_indicators_multiple_types(self):
        """Test detection with multiple indicator types."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=3),
            'open': [100, 101, 102],
            'high': [102, 103, 104],
            'low': [99, 100, 101],
            'close': [101, 102, 103],
            'volume': [1000, 1100, 1200],
            'rsi_14': [45, 46, 47],
            'sma_10': [100, 101, 102],
            'sma_20': [100.5, 101.5, 102.5],
            'ema_12': [100.2, 101.2, 102.2],
            'macd': [0.5, 0.6, 0.7],
            'bb_upper': [105, 106, 107],
            'bb_lower': [95, 96, 97]
        })
        
        indicators = detect_indicator_columns(df)
        
        assert len(indicators) == 7
        assert all(ind in indicators for ind in ['rsi_14', 'sma_10', 'sma_20', 'ema_12', 'macd', 'bb_upper', 'bb_lower'])
    
    def test_detect_indicators_with_extra_columns(self):
        """Test detection with non-indicator extra columns."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=3),
            'open': [100, 101, 102],
            'high': [102, 103, 104],
            'low': [99, 100, 101],
            'close': [101, 102, 103],
            'volume': [1000, 1100, 1200],
            'symbol': ['AAPL', 'AAPL', 'AAPL'],  # Not an indicator
            'rsi_14': [45, 46, 47]
        })
        
        indicators = detect_indicator_columns(df)
        
        # Should include both non-OHLCV columns
        assert 'rsi_14' in indicators
        assert 'symbol' in indicators
        assert len(indicators) == 2
    
    def test_detect_indicators_preserves_order(self):
        """Test that detected indicators preserve column order."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=3),
            'open': [100, 101, 102],
            'high': [102, 103, 104],
            'low': [99, 100, 101],
            'close': [101, 102, 103],
            'volume': [1000, 1100, 1200],
            'sma_20': [100.5, 101.5, 102.5],
            'rsi_14': [45, 46, 47],
            'ema_12': [100.2, 101.2, 102.2]
        })
        
        indicators = detect_indicator_columns(df)
        
        # Should maintain column order
        assert indicators == ['sma_20', 'rsi_14', 'ema_12']
    
    def test_detect_indicators_empty_dataframe(self):
        """Test detection with empty DataFrame."""
        df = pd.DataFrame()
        
        indicators = detect_indicator_columns(df)
        
        assert indicators == []
    
    def test_detect_indicators_only_timestamp(self):
        """Test detection when DataFrame has only timestamp column."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=3)
        })
        
        indicators = detect_indicator_columns(df)
        
        assert indicators == []

