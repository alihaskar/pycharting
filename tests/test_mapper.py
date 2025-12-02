"""
Tests for src/python_api/mapper.py - Column mapping utilities

Tests cover:
- Standard column names (lowercase)
- Custom column names (various cases)
- Missing columns
- Non-numeric columns
- Duplicate mappings
- Volume column (optional)
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class TestMapColumnsBasic:
    """Test basic map_columns() functionality"""
    
    def test_standard_lowercase_names_pass_through(self):
        """Standard lowercase names should pass through unchanged"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [103.0, 104.0, 105.0, 106.0, 107.0],
            'volume': [1000, 1200, 1100, 1300, 1250]
        })
        df.set_index('timestamp', inplace=True)
        
        result = map_columns(df)
        
        assert list(result.columns) == ['open', 'high', 'low', 'close', 'volume']
        assert result['open'].iloc[0] == 100.0
        assert result['close'].iloc[-1] == 107.0
    
    def test_custom_uppercase_names_mapped(self):
        """Uppercase column names should be mapped to lowercase"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'OPEN': [100.0, 101.0, 102.0, 103.0, 104.0],
            'HIGH': [105.0, 106.0, 107.0, 108.0, 109.0],
            'LOW': [99.0, 100.0, 101.0, 102.0, 103.0],
            'CLOSE': [103.0, 104.0, 105.0, 106.0, 107.0],
            'VOLUME': [1000, 1200, 1100, 1300, 1250]
        })
        df.set_index('timestamp', inplace=True)
        
        result = map_columns(df, open='OPEN', high='HIGH', low='LOW', close='CLOSE', volume='VOLUME')
        
        assert list(result.columns) == ['open', 'high', 'low', 'close', 'volume']
        assert result['open'].iloc[0] == 100.0
    
    def test_custom_mixed_case_names_mapped(self):
        """Mixed case column names should be mapped"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'High': [105.0, 106.0, 107.0, 108.0, 109.0],
            'Low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'Close': [103.0, 104.0, 105.0, 106.0, 107.0]
        })
        df.set_index('timestamp', inplace=True)
        
        result = map_columns(df, open='Open', high='High', low='Low', close='Close')
        
        assert list(result.columns) == ['open', 'high', 'low', 'close']
        assert result['high'].iloc[0] == 105.0
    
    def test_volume_is_optional(self):
        """Volume column should be optional"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [103.0, 104.0, 105.0, 106.0, 107.0]
        })
        df.set_index('timestamp', inplace=True)
        
        result = map_columns(df)
        
        assert list(result.columns) == ['open', 'high', 'low', 'close']
        assert 'volume' not in result.columns


class TestMapColumnsValidation:
    """Test validation and error handling"""
    
    def test_missing_required_column_raises_error(self):
        """Missing required OHLC column should raise ValueError"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0]
            # Missing 'close'
        })
        df.set_index('timestamp', inplace=True)
        
        with pytest.raises(ValueError, match="Missing required column"):
            map_columns(df)
    
    def test_non_numeric_column_raises_error(self):
        """Non-numeric OHLC columns should raise TypeError"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': ['100', '101', '102', '103', '104'],  # Strings!
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [103.0, 104.0, 105.0, 106.0, 107.0]
        })
        df.set_index('timestamp', inplace=True)
        
        with pytest.raises(TypeError, match="must be numeric"):
            map_columns(df, open='open')
    
    def test_specified_column_not_found_raises_error(self):
        """Specifying non-existent column should raise ValueError"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [103.0, 104.0, 105.0, 106.0, 107.0]
        })
        df.set_index('timestamp', inplace=True)
        
        with pytest.raises(ValueError, match="Column 'OPEN_PRICE' not found"):
            map_columns(df, open='OPEN_PRICE')
    
    def test_duplicate_column_mapping_raises_error(self):
        """Mapping two OHLC fields to same column should raise ValueError"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'price': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0]
        })
        df.set_index('timestamp', inplace=True)
        
        with pytest.raises(ValueError, match="Duplicate column mapping"):
            map_columns(df, open='price', close='price')  # Both map to 'price'


class TestMapColumnsEdgeCases:
    """Test edge cases and unusual inputs"""
    
    def test_extra_columns_preserved(self):
        """Extra columns (like bid, ask) should be preserved"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [103.0, 104.0, 105.0, 106.0, 107.0],
            'bid': [102.5, 103.5, 104.5, 105.5, 106.5],
            'ask': [103.5, 104.5, 105.5, 106.5, 107.5]
        })
        df.set_index('timestamp', inplace=True)
        
        result = map_columns(df)
        
        assert 'bid' in result.columns
        assert 'ask' in result.columns
        assert result['bid'].iloc[0] == 102.5
    
    def test_single_row_dataframe(self):
        """Should work with single-row DataFrame"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=1, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': [100.0],
            'high': [105.0],
            'low': [99.0],
            'close': [103.0]
        })
        df.set_index('timestamp', inplace=True)
        
        result = map_columns(df)
        
        assert len(result) == 1
        assert result['close'].iloc[0] == 103.0
    
    def test_nan_values_preserved(self):
        """NaN values should be preserved in output"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': [100.0, 101.0, np.nan, 103.0, 104.0],
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [103.0, 104.0, 105.0, np.nan, 107.0]
        })
        df.set_index('timestamp', inplace=True)
        
        result = map_columns(df)
        
        assert pd.isna(result['open'].iloc[2])
        assert pd.isna(result['close'].iloc[3])


class TestDetectColumnsBasic:
    """Test basic detect_columns() auto-detection functionality"""
    
    def test_detect_standard_lowercase_names(self):
        """Should detect standard lowercase OHLC names"""
        from src.charting.mapper import detect_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [103.0, 104.0, 105.0, 106.0, 107.0],
            'volume': [1000, 1200, 1100, 1300, 1250]
        })
        df.set_index('timestamp', inplace=True)
        
        result = detect_columns(df)
        
        assert result == {
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume'
        }
    
    def test_detect_uppercase_names(self):
        """Should detect uppercase OHLC names"""
        from src.charting.mapper import detect_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'OPEN': [100.0, 101.0, 102.0, 103.0, 104.0],
            'HIGH': [105.0, 106.0, 107.0, 108.0, 109.0],
            'LOW': [99.0, 100.0, 101.0, 102.0, 103.0],
            'CLOSE': [103.0, 104.0, 105.0, 106.0, 107.0]
        })
        df.set_index('timestamp', inplace=True)
        
        result = detect_columns(df)
        
        assert result == {
            'OPEN': 'open',
            'HIGH': 'high',
            'LOW': 'low',
            'CLOSE': 'close'
        }
    
    def test_detect_mixed_case_names(self):
        """Should detect mixed case names (Open, High, etc.)"""
        from src.charting.mapper import detect_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'High': [105.0, 106.0, 107.0, 108.0, 109.0],
            'Low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'Close': [103.0, 104.0, 105.0, 106.0, 107.0]
        })
        df.set_index('timestamp', inplace=True)
        
        result = detect_columns(df)
        
        assert result == {
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close'
        }
    
    def test_detect_abbreviations(self):
        """Should detect common abbreviations (o, h, l, c)"""
        from src.charting.mapper import detect_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'o': [100.0, 101.0, 102.0, 103.0, 104.0],
            'h': [105.0, 106.0, 107.0, 108.0, 109.0],
            'l': [99.0, 100.0, 101.0, 102.0, 103.0],
            'c': [103.0, 104.0, 105.0, 106.0, 107.0],
            'v': [1000, 1200, 1100, 1300, 1250]
        })
        df.set_index('timestamp', inplace=True)
        
        result = detect_columns(df)
        
        assert result == {
            'o': 'open',
            'h': 'high',
            'l': 'low',
            'c': 'close',
            'v': 'volume'
        }
    
    def test_volume_optional_in_detection(self):
        """Volume should be optional in auto-detection"""
        from src.charting.mapper import detect_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [103.0, 104.0, 105.0, 106.0, 107.0]
        })
        df.set_index('timestamp', inplace=True)
        
        result = detect_columns(df)
        
        assert 'volume' not in result.values()
        assert len(result) == 4


class TestDetectColumnsEdgeCases:
    """Test edge cases and unusual patterns"""
    
    def test_detect_vol_abbreviation(self):
        """Should detect 'vol' as volume"""
        from src.charting.mapper import detect_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [103.0, 104.0, 105.0, 106.0, 107.0],
            'vol': [1000, 1200, 1100, 1300, 1250]
        })
        df.set_index('timestamp', inplace=True)
        
        result = detect_columns(df)
        
        assert result['vol'] == 'volume'
    
    def test_missing_required_column_raises_error(self):
        """Should raise error when required column missing"""
        from src.charting.mapper import detect_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0]
            # Missing 'close'
        })
        df.set_index('timestamp', inplace=True)
        
        with pytest.raises(ValueError, match="Could not detect required column"):
            detect_columns(df)
    
    def test_ambiguous_columns_prefers_exact_match(self):
        """When multiple candidates exist, prefer exact match"""
        from src.charting.mapper import detect_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'Open': [100.5, 101.5, 102.5, 103.5, 104.5],  # Ambiguous!
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [103.0, 104.0, 105.0, 106.0, 107.0]
        })
        df.set_index('timestamp', inplace=True)
        
        result = detect_columns(df)
        
        # Should prefer lowercase exact match
        assert result['open'] == 'open'
        assert 'Open' not in result


class TestMapColumnsDataIntegrity:
    """Test that data values are correctly preserved"""
    
    def test_original_dataframe_not_modified(self):
        """Original DataFrame should not be modified"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'High': [105.0, 106.0, 107.0, 108.0, 109.0],
            'Low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'Close': [103.0, 104.0, 105.0, 106.0, 107.0]
        })
        df.set_index('timestamp', inplace=True)
        
        original_columns = list(df.columns)
        result = map_columns(df, open='Open', high='High', low='Low', close='Close')
        
        assert list(df.columns) == original_columns  # Original unchanged
        assert list(result.columns) != original_columns  # Result is different
    
    def test_data_values_correctly_mapped(self):
        """Data values should be correctly mapped to new column names"""
        from src.charting.mapper import map_columns
        
        dates = pd.date_range('2024-01-01', periods=3, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'o': [100.0, 101.0, 102.0],
            'h': [105.0, 106.0, 107.0],
            'l': [99.0, 100.0, 101.0],
            'c': [103.0, 104.0, 105.0]
        })
        df.set_index('timestamp', inplace=True)
        
        result = map_columns(df, open='o', high='h', low='l', close='c')
        
        # Verify exact values
        assert result['open'].tolist() == [100.0, 101.0, 102.0]
        assert result['high'].tolist() == [105.0, 106.0, 107.0]
        assert result['low'].tolist() == [99.0, 100.0, 101.0]
        assert result['close'].tolist() == [103.0, 104.0, 105.0]

