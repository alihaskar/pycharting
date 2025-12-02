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
from charting.api.processor import detect_indicator_columns, filter_indicator_data, load_and_process_data


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


class TestIntegrationWithExistingOHLC:
    """Test integration with existing OHLC processing."""
    
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
    
    def create_test_csv(self, filename, include_indicators=False):
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
    
    def test_backward_compatibility_ohlc_only(self):
        """Test that OHLC-only CSV still works correctly."""
        filename = self.create_test_csv('ohlc_only.csv', include_indicators=False)
        
        data, metadata = load_and_process_data(filename)
        
        # Should process successfully
        assert len(data) == 6  # timestamp + OHLCV
        assert metadata['available_indicators'] == []
        assert metadata['indicators'] == []
        assert metadata['filename'] == filename
        assert metadata['rows'] == 10
    
    def test_csv_with_indicators_preserves_ohlc(self):
        """Test that OHLC processing is not affected by indicators."""
        filename = self.create_test_csv('with_indicators.csv', include_indicators=True)
        
        data, metadata = load_and_process_data(filename)
        
        # OHLC data should be first 6 columns
        timestamps = data[0]
        opens = data[1]
        highs = data[2]
        lows = data[3]
        closes = data[4]
        volumes = data[5]
        
        # Verify OHLC data is correct
        assert len(timestamps) == 10
        assert opens[0] == 100
        assert highs[0] == 102
        assert lows[0] == 99
        assert closes[0] == 101
        assert volumes[0] == 1000
    
    def test_end_to_end_with_resampling(self):
        """Test end-to-end pipeline with resampling."""
        filename = self.create_test_csv('resample_test.csv', include_indicators=True)
        
        # Process with resampling
        data, metadata = load_and_process_data(filename, timeframe='5min')
        
        # Should process successfully
        assert metadata['timeframe'] == '5min'
        assert len(data) >= 6  # At least OHLCV columns
        assert metadata['available_indicators'] == ['rsi_14', 'sma_20']
    
    def test_end_to_end_with_date_filtering(self):
        """Test end-to-end pipeline with date filtering."""
        filename = self.create_test_csv('date_filter_test.csv', include_indicators=True)
        
        # Filter to specific date range
        data, metadata = load_and_process_data(
            filename,
            start_date='2024-01-01 00:03:00',
            end_date='2024-01-01 00:07:00'
        )
        
        # Should have filtered rows
        assert metadata['rows'] < 10  # Less than original 10 rows
        assert metadata['available_indicators'] == ['rsi_14', 'sma_20']
    
    def test_csv_indicators_plus_calculated_indicators(self):
        """Test CSV indicators combined with calculated indicators."""
        filename = self.create_test_csv('combined_indicators.csv', include_indicators=True)
        
        # Request calculation of additional indicator
        data, metadata = load_and_process_data(filename, indicators=['RSI:10'])
        
        # CSV indicators
        assert 'rsi_14' in metadata['available_indicators']
        assert 'sma_20' in metadata['available_indicators']
        
        # Calculated indicator
        assert 'rsi_10' in metadata['indicators']
        
        # Data should include all
        assert len(data) > 6  # OHLCV + CSV indicators + calculated
    
    def test_no_regression_in_calculated_indicators(self):
        """Test that existing calculated indicator functionality still works."""
        filename = self.create_test_csv('calc_indicators.csv', include_indicators=False)
        
        # Calculate indicators on OHLC-only data
        data, metadata = load_and_process_data(
            filename,
            indicators=['RSI:14', 'SMA:5']
        )
        
        # Calculated indicators should work
        assert 'rsi_14' in metadata['indicators']
        assert 'sma_5' in metadata['indicators']
        assert metadata['available_indicators'] == []
    
    def test_data_integrity_maintained(self):
        """Test that data values are preserved correctly."""
        filename = self.create_test_csv('integrity_test.csv', include_indicators=True)
        
        data, metadata = load_and_process_data(filename)
        
        # Indicator data should be in output (columns 6 and 7)
        rsi_data = data[6]
        sma_data = data[7]
        
        # Verify indicator values are present and numeric
        assert len(rsi_data) == 10
        assert len(sma_data) == 10
        assert all(isinstance(x, (int, float)) or x is None for x in rsi_data)
        assert all(isinstance(x, (int, float)) or x is None for x in sma_data)
    
    def test_metadata_columns_count_accurate(self):
        """Test that metadata columns count includes all data."""
        filename = self.create_test_csv('column_count.csv', include_indicators=True)
        
        data, metadata = load_and_process_data(filename)
        
        # Columns count should match data length
        assert metadata['columns'] == len(data)
        # Should be: timestamp + OHLCV (6) + 2 indicators = 8
        assert metadata['columns'] == 8
    
    def test_empty_indicators_list_handled(self):
        """Test that empty indicators list doesn't break processing."""
        filename = self.create_test_csv('empty_list.csv', include_indicators=True)
        
        # Pass empty indicators list
        data, metadata = load_and_process_data(filename, indicators=[])
        
        # Should process successfully
        assert metadata['indicators'] == []
        assert metadata['available_indicators'] == ['rsi_14', 'sma_20']

