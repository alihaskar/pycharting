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
    prepare_dataframe_for_csv
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

