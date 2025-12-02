"""
Tests for DataFrame to CSV transformation.
Testing DataFrame copying, column renaming, and CSV generation.
"""

import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from datetime import datetime
from src.python_api.transformer import (
    transform_dataframe_to_csv,
    standardize_column_names,
    prepare_dataframe_for_csv,
    handle_datetime_index,
    generate_temp_filepath,
    create_temp_csv
)


class TestDataFrameCopyingAndRenaming:
    """Test DataFrame copying and OHLC column standardization."""
    
    def test_standardize_column_names_basic(self):
        """Test basic column name standardization."""
        df = pd.DataFrame({
            'Open': [100.0, 101.0],
            'High': [102.0, 103.0],
            'Low': [99.0, 100.0],
            'Close': [101.0, 102.0],
            'Volume': [1000, 1100]
        })
        
        ohlc_mapping = {
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }
        
        result = standardize_column_names(df, ohlc_mapping)
        
        # Check standardized column names
        assert 'open' in result.columns
        assert 'high' in result.columns
        assert 'low' in result.columns
        assert 'close' in result.columns
        assert 'volume' in result.columns
        
        # Check original names are gone
        assert 'Open' not in result.columns
        assert 'High' not in result.columns
    
    def test_standardize_preserves_data(self):
        """Test that data values are preserved during renaming."""
        df = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0],
            'High': [102.0, 103.0, 104.0],
            'Low': [99.0, 100.0, 101.0],
            'Close': [101.0, 102.0, 103.0]
        })
        
        ohlc_mapping = {
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close'
        }
        
        result = standardize_column_names(df, ohlc_mapping)
        
        # Verify data is preserved
        assert result['open'].tolist() == [100.0, 101.0, 102.0]
        assert result['high'].tolist() == [102.0, 103.0, 104.0]
        assert result['low'].tolist() == [99.0, 100.0, 101.0]
        assert result['close'].tolist() == [101.0, 102.0, 103.0]
    
    def test_standardize_does_not_modify_original(self):
        """Test that original DataFrame is not modified."""
        df = pd.DataFrame({
            'Open': [100.0, 101.0],
            'High': [102.0, 103.0],
            'Low': [99.0, 100.0],
            'Close': [101.0, 102.0]
        })
        
        ohlc_mapping = {
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close'
        }
        
        original_columns = df.columns.tolist()
        result = standardize_column_names(df, ohlc_mapping)
        
        # Original should be unchanged
        assert df.columns.tolist() == original_columns
        assert 'Open' in df.columns
        assert 'open' not in df.columns
    
    def test_standardize_with_abbreviated_names(self):
        """Test standardization with abbreviated OHLC column names."""
        df = pd.DataFrame({
            'o': [100.0], 'h': [102.0], 'l': [99.0], 'c': [101.0], 'v': [1000]
        })
        
        ohlc_mapping = {
            'open': 'o',
            'high': 'h',
            'low': 'l',
            'close': 'c',
            'volume': 'v'
        }
        
        result = standardize_column_names(df, ohlc_mapping)
        
        assert 'open' in result.columns
        assert 'high' in result.columns
        assert 'low' in result.columns
        assert 'close' in result.columns
        assert 'volume' in result.columns
    
    def test_standardize_preserves_indicator_columns(self):
        """Test that indicator columns are preserved with original names."""
        df = pd.DataFrame({
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0],
            'rsi_14': [45.0],
            'sma_20': [100.5]
        })
        
        ohlc_mapping = {
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close'
        }
        
        result = standardize_column_names(df, ohlc_mapping)
        
        # OHLC standardized
        assert 'open' in result.columns
        # Indicators preserved
        assert 'rsi_14' in result.columns
        assert 'sma_20' in result.columns
    
    def test_standardize_with_partial_mapping(self):
        """Test handling when only some OHLC columns are mapped."""
        df = pd.DataFrame({
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0]
        })
        
        # Only map open and close
        ohlc_mapping = {
            'open': 'Open',
            'close': 'Close'
        }
        
        result = standardize_column_names(df, ohlc_mapping)
        
        # Mapped columns standardized
        assert 'open' in result.columns
        assert 'close' in result.columns
        # Unmapped columns preserved
        assert 'High' in result.columns
        assert 'Low' in result.columns
    
    def test_standardize_empty_dataframe(self):
        """Test standardization with empty DataFrame."""
        df = pd.DataFrame()
        ohlc_mapping = {}
        
        result = standardize_column_names(df, ohlc_mapping)
        
        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)


class TestDateTimeIndexHandling:
    """Test datetime index conversion and handling."""
    
    def test_handle_datetime_index_basic(self):
        """Test basic datetime index to column conversion."""
        dates = pd.date_range('2024-01-01', periods=5, freq='1min')
        df = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'close': [101, 102, 103, 104, 105]
        }, index=dates)
        
        result = handle_datetime_index(df)
        
        # Index should be reset
        assert result.index.name is None or result.index.name != 'timestamp'
        # Timestamp column should exist
        assert 'timestamp' in result.columns
        # Should have 5 rows
        assert len(result) == 5
    
    def test_handle_datetime_index_preserves_data(self):
        """Test that datetime conversion preserves OHLC data."""
        dates = pd.date_range('2024-01-01', periods=3, freq='1min')
        df = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [102, 103, 104],
            'low': [99, 100, 101],
            'close': [101, 102, 103]
        }, index=dates)
        
        result = handle_datetime_index(df)
        
        # Data should be preserved
        assert result['open'].tolist() == [100, 101, 102]
        assert result['high'].tolist() == [102, 103, 104]
        assert result['low'].tolist() == [99, 100, 101]
        assert result['close'].tolist() == [101, 102, 103]
    
    def test_handle_datetime_index_with_timezone(self):
        """Test datetime index with timezone information."""
        dates = pd.date_range('2024-01-01', periods=3, freq='1min', tz='UTC')
        df = pd.DataFrame({
            'open': [100, 101, 102],
            'close': [101, 102, 103]
        }, index=dates)
        
        result = handle_datetime_index(df)
        
        # Timestamp column should be created
        assert 'timestamp' in result.columns
        # Should handle timezone gracefully
        assert len(result) == 3
    
    def test_handle_datetime_index_hourly_frequency(self):
        """Test datetime index with hourly frequency."""
        dates = pd.date_range('2024-01-01', periods=24, freq='1h')
        df = pd.DataFrame({
            'open': range(100, 124),
            'close': range(101, 125)
        }, index=dates)
        
        result = handle_datetime_index(df)
        
        assert 'timestamp' in result.columns
        assert len(result) == 24
    
    def test_handle_datetime_index_daily_frequency(self):
        """Test datetime index with daily frequency."""
        dates = pd.date_range('2024-01-01', periods=30, freq='1D')
        df = pd.DataFrame({
            'open': range(100, 130),
            'close': range(101, 131)
        }, index=dates)
        
        result = handle_datetime_index(df)
        
        assert 'timestamp' in result.columns
        assert len(result) == 30
    
    def test_handle_datetime_index_already_has_timestamp_column(self):
        """Test handling when DataFrame already has a timestamp column."""
        dates = pd.date_range('2024-01-01', periods=3, freq='1min')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': [100, 101, 102],
            'close': [101, 102, 103]
        }, index=dates)
        
        result = handle_datetime_index(df)
        
        # Should still have timestamp column
        assert 'timestamp' in result.columns
        # Should not duplicate
        assert result.columns.tolist().count('timestamp') == 1
    
    def test_handle_datetime_index_with_non_datetime_index(self):
        """Test handling DataFrame with non-datetime index."""
        df = pd.DataFrame({
            'open': [100, 101, 102],
            'close': [101, 102, 103]
        })
        
        result = handle_datetime_index(df)
        
        # Should handle gracefully
        assert isinstance(result, pd.DataFrame)
        # Original data preserved
        assert len(result) == 3
    
    def test_handle_datetime_index_timestamp_format(self):
        """Test that timestamp is in proper format for CSV."""
        dates = pd.date_range('2024-01-01', periods=3, freq='1min')
        df = pd.DataFrame({
            'open': [100, 101, 102],
            'close': [101, 102, 103]
        }, index=dates)
        
        result = handle_datetime_index(df)
        
        # Timestamp should be datetime-like or string
        assert 'timestamp' in result.columns
        # Verify it's a valid timestamp representation
        assert result['timestamp'].notna().all()


class TestTemporaryFileCreation:
    """Test temporary file creation and management."""
    
    def test_generate_temp_filepath_creates_unique_filename(self):
        """Test that generate_temp_filepath creates unique filenames."""
        filepath1 = generate_temp_filepath()
        filepath2 = generate_temp_filepath()
        
        # Filenames should be different due to timestamp
        assert filepath1 != filepath2
        assert os.path.basename(filepath1) != os.path.basename(filepath2)
    
    def test_generate_temp_filepath_uses_system_temp_dir(self):
        """Test that files are created in system temp directory."""
        filepath = generate_temp_filepath()
        
        # Should be in temp directory
        temp_dir = tempfile.gettempdir()
        assert filepath.startswith(temp_dir)
    
    def test_generate_temp_filepath_has_correct_extension(self):
        """Test that generated files have .csv extension."""
        filepath = generate_temp_filepath()
        
        assert filepath.endswith('.csv')
    
    def test_generate_temp_filepath_format(self):
        """Test filename format matches expected pattern."""
        filepath = generate_temp_filepath()
        filename = os.path.basename(filepath)
        
        # Should match pattern: chart_data_{timestamp}.csv
        assert filename.startswith('chart_data_')
        assert filename.endswith('.csv')
    
    def test_create_temp_csv_creates_file(self):
        """Test that create_temp_csv actually creates a file."""
        df = pd.DataFrame({
            'open': [100, 101, 102],
            'close': [101, 102, 103]
        })
        
        filepath = create_temp_csv(df)
        
        try:
            # File should exist
            assert os.path.exists(filepath)
            assert os.path.isfile(filepath)
        finally:
            # Cleanup
            if os.path.exists(filepath):
                os.remove(filepath)
    
    def test_create_temp_csv_writes_valid_csv(self):
        """Test that created CSV file is valid and readable."""
        df = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [102, 103, 104],
            'low': [99, 100, 101],
            'close': [101, 102, 103]
        })
        
        filepath = create_temp_csv(df)
        
        try:
            # Should be readable by pandas
            df_read = pd.read_csv(filepath)
            assert len(df_read) == 3
            assert 'open' in df_read.columns
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
    
    def test_create_temp_csv_preserves_data(self):
        """Test that CSV file contains correct data."""
        df = pd.DataFrame({
            'open': [100, 101, 102],
            'close': [101, 102, 103]
        })
        
        filepath = create_temp_csv(df)
        
        try:
            df_read = pd.read_csv(filepath)
            assert df_read['open'].tolist() == [100, 101, 102]
            assert df_read['close'].tolist() == [101, 102, 103]
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
    
    def test_create_temp_csv_no_index_column(self):
        """Test that CSV doesn't include pandas index column."""
        df = pd.DataFrame({
            'open': [100, 101, 102],
            'close': [101, 102, 103]
        })
        
        filepath = create_temp_csv(df)
        
        try:
            df_read = pd.read_csv(filepath)
            # Should have same number of columns
            assert len(df_read.columns) == len(df.columns)
            # Should not have 'Unnamed: 0' or similar index columns
            assert not any('unnamed' in col.lower() for col in df_read.columns)
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
    
    def test_create_temp_csv_with_large_dataframe(self):
        """Test creating CSV with larger DataFrame."""
        df = pd.DataFrame({
            'open': range(1000),
            'high': range(1, 1001),
            'low': range(0, 1000),
            'close': range(1, 1001)
        })
        
        filepath = create_temp_csv(df)
        
        try:
            assert os.path.exists(filepath)
            # Check file size is reasonable (should be > 0)
            assert os.path.getsize(filepath) > 0
            # Verify data integrity
            df_read = pd.read_csv(filepath)
            assert len(df_read) == 1000
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

