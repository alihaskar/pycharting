"""
Tests for DataFrame OHLC column detection.
Testing pattern matching with various naming conventions.
"""

import pytest
import pandas as pd
import numpy as np
from src.python_api.detector import detect_ohlc_columns


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

