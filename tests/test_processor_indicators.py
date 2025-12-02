"""
Tests for indicator column detection in processor.
Testing detection of pre-existing indicator columns in CSV files.
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
from src.api.processor import detect_indicator_columns, filter_indicator_data, load_and_process_data


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


class TestDataFilteringAndExtraction:
    """Test filtering and extraction of indicator data."""
    
    def test_filter_indicator_data_overlays_only(self):
        """Test filtering overlay indicators."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=3),
            'open': [100, 101, 102],
            'close': [101, 102, 103],
            'sma_20': [100.5, 101.5, 102.5],
            'ema_12': [100.2, 101.2, 102.2],
            'rsi_14': [45, 46, 47]
        })
        
        overlays, subplots = filter_indicator_data(
            df,
            overlays=['sma_20', 'ema_12'],
            subplots=None
        )
        
        assert overlays == ['sma_20', 'ema_12']
        assert subplots == []
    
    def test_filter_indicator_data_subplots_only(self):
        """Test filtering subplot indicators."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=3),
            'open': [100, 101, 102],
            'close': [101, 102, 103],
            'sma_20': [100.5, 101.5, 102.5],
            'rsi_14': [45, 46, 47],
            'macd': [0.5, 0.6, 0.7]
        })
        
        overlays, subplots = filter_indicator_data(
            df,
            overlays=None,
            subplots=['rsi_14', 'macd']
        )
        
        assert overlays == []
        assert subplots == ['rsi_14', 'macd']
    
    def test_filter_indicator_data_both_types(self):
        """Test filtering both overlay and subplot indicators."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=3),
            'open': [100, 101, 102],
            'close': [101, 102, 103],
            'sma_20': [100.5, 101.5, 102.5],
            'rsi_14': [45, 46, 47]
        })
        
        overlays, subplots = filter_indicator_data(
            df,
            overlays=['sma_20'],
            subplots=['rsi_14']
        )
        
        assert overlays == ['sma_20']
        assert subplots == ['rsi_14']
    
    def test_filter_indicator_data_no_filters(self):
        """Test when no filters are specified."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=3),
            'open': [100, 101, 102],
            'close': [101, 102, 103],
            'sma_20': [100.5, 101.5, 102.5],
            'rsi_14': [45, 46, 47]
        })
        
        overlays, subplots = filter_indicator_data(df, overlays=None, subplots=None)
        
        assert overlays == []
        assert subplots == []
    
    def test_filter_indicator_data_missing_columns(self):
        """Test filtering when requested columns don't exist."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=3),
            'open': [100, 101, 102],
            'close': [101, 102, 103],
            'sma_20': [100.5, 101.5, 102.5]
        })
        
        overlays, subplots = filter_indicator_data(
            df,
            overlays=['sma_20', 'nonexistent'],
            subplots=['rsi_14']
        )
        
        # Should only include existing columns
        assert overlays == ['sma_20']
        assert subplots == []
    
    def test_filter_indicator_data_empty_lists(self):
        """Test filtering with empty lists."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=3),
            'open': [100, 101, 102],
            'close': [101, 102, 103],
            'sma_20': [100.5, 101.5, 102.5]
        })
        
        overlays, subplots = filter_indicator_data(df, overlays=[], subplots=[])
        
        assert overlays == []
        assert subplots == []
    
    def test_filter_indicator_data_preserves_order(self):
        """Test that filtering preserves requested order."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=3),
            'open': [100, 101, 102],
            'close': [101, 102, 103],
            'sma_20': [100.5, 101.5, 102.5],
            'ema_12': [100.2, 101.2, 102.2],
            'rsi_14': [45, 46, 47]
        })
        
        # Request in specific order
        overlays, subplots = filter_indicator_data(
            df,
            overlays=['ema_12', 'sma_20'],
            subplots=None
        )
        
        # Should preserve requested order
        assert overlays == ['ema_12', 'sma_20']


class TestResponseFormatEnhancement:
    """Test response format includes indicator metadata."""
    
    def setup_method(self):
        """Set up test CSV files."""
        self.temp_dir = tempfile.mkdtemp()
        os.environ['DATA_DIR'] = self.temp_dir
    
    def teardown_method(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        if 'DATA_DIR' in os.environ:
            del os.environ['DATA_DIR']
    
    def create_test_csv(self, filename, include_indicators=True):
        """Create a test CSV file."""
        dates = pd.date_range('2024-01-01', periods=10, freq='1min')
        data = {
            'timestamp': dates,
            'open': range(100, 110),
            'high': range(102, 112),
            'low': range(99, 109),
            'close': range(101, 111),
            'volume': range(1000, 1010)
        }
        
        if include_indicators:
            data['rsi_14'] = range(45, 55)
            data['sma_20'] = [x + 0.5 for x in range(100, 110)]
        
        df = pd.DataFrame(data)
        filepath = Path(self.temp_dir) / filename
        df.to_csv(filepath, index=False)
        return filename
    
    def test_metadata_includes_available_indicators(self):
        """Test that metadata includes list of available indicators."""
        filename = self.create_test_csv('test_indicators.csv', include_indicators=True)
        
        data, metadata = load_and_process_data(filename)
        
        assert 'available_indicators' in metadata
        assert isinstance(metadata['available_indicators'], list)
        assert 'rsi_14' in metadata['available_indicators']
        assert 'sma_20' in metadata['available_indicators']
    
    def test_metadata_no_indicators_in_csv(self):
        """Test metadata when CSV has no indicators."""
        filename = self.create_test_csv('test_no_indicators.csv', include_indicators=False)
        
        data, metadata = load_and_process_data(filename)
        
        assert 'available_indicators' in metadata
        assert metadata['available_indicators'] == []
    
    def test_metadata_preserves_backward_compatibility(self):
        """Test that existing metadata fields are still present."""
        filename = self.create_test_csv('test_compat.csv', include_indicators=True)
        
        data, metadata = load_and_process_data(filename)
        
        # Existing fields should still be present
        assert 'filename' in metadata
        assert 'rows' in metadata
        assert 'columns' in metadata
        assert 'timeframe' in metadata
        assert 'indicators' in metadata  # Calculated indicators
    
    def test_metadata_distinguishes_calculated_vs_csv_indicators(self):
        """Test that metadata distinguishes calculated vs CSV indicators."""
        filename = self.create_test_csv('test_distinction.csv', include_indicators=True)
        
        # Request calculation of new indicator
        data, metadata = load_and_process_data(filename, indicators=['RSI:10'])
        
        # available_indicators = from CSV
        assert 'rsi_14' in metadata['available_indicators']
        assert 'sma_20' in metadata['available_indicators']
        
        # indicators = calculated by API
        assert 'rsi_10' in metadata['indicators']
    
    def test_data_includes_indicator_columns(self):
        """Test that data array includes indicator columns."""
        filename = self.create_test_csv('test_data_inclusion.csv', include_indicators=True)
        
        data, metadata = load_and_process_data(filename)
        
        # Data should have more than just OHLCV (6 columns)
        # Should include timestamp + OHLCV + indicators
        assert len(data) > 6
        assert metadata['columns'] > 6

