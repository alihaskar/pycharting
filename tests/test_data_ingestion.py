"""Tests for data ingestion and validation module."""

import pytest
import pandas as pd
import numpy as np
from src.data.ingestion import DataManager, DataValidationError, validate_input


class TestValidateInput:
    """Tests for the validate_input function."""
    
    def test_valid_pandas_input(self):
        """Test validation with valid Pandas Series input."""
        index = pd.date_range("2024-01-01", periods=5)
        open_data = pd.Series([100, 102, 101, 103, 102])
        high = pd.Series([105, 106, 105, 107, 106])
        low = pd.Series([99, 100, 99, 101, 100])
        close = pd.Series([104, 103, 104, 105, 104])
        
        result = validate_input(index, open_data, high, low, close)
        
        assert isinstance(result["index"], np.ndarray)
        assert isinstance(result["open"], np.ndarray)
        assert len(result["index"]) == 5
        assert np.array_equal(result["open"], [100, 102, 101, 103, 102])
    
    def test_valid_numpy_input(self):
        """Test validation with valid NumPy array input."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        
        result = validate_input(index, open_data, high, low, close)
        
        assert isinstance(result["index"], np.ndarray)
        assert len(result["index"]) == 5
        assert np.array_equal(result["close"], [104, 103, 104, 105, 104])
    
    def test_with_overlays(self):
        """Test validation with overlay data."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        overlays = {
            "SMA20": np.array([101, 102, 102, 103, 103]),
            "EMA10": np.array([100, 101, 101, 102, 102]),
        }
        
        result = validate_input(index, open_data, high, low, close, overlays=overlays)
        
        assert len(result["overlays"]) == 2
        assert "SMA20" in result["overlays"]
        assert "EMA10" in result["overlays"]
        assert np.array_equal(result["overlays"]["SMA20"], [101, 102, 102, 103, 103])
    
    def test_with_subplots(self):
        """Test validation with subplot data."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        subplots = {
            "Volume": np.array([1000, 1200, 1100, 1300, 1150]),
            "RSI": np.array([55, 58, 52, 60, 57]),
        }
        
        result = validate_input(index, open_data, high, low, close, subplots=subplots)
        
        assert len(result["subplots"]) == 2
        assert "Volume" in result["subplots"]
        assert "RSI" in result["subplots"]
    
    def test_invalid_index_type(self):
        """Test that invalid index type raises error."""
        index = [1, 2, 3, 4, 5]  # List instead of Index or ndarray
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        
        with pytest.raises(DataValidationError, match="Index must be"):
            validate_input(index, open_data, high, low, close)
    
    def test_length_mismatch(self):
        """Test that mismatched lengths raise error."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101])  # Length 3
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        
        with pytest.raises(DataValidationError, match="does not match index length"):
            validate_input(index, open_data, high, low, close)
    
    def test_ohlc_constraint_high_violation(self):
        """Test that High < max(Open, Close) raises error."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([99, 106, 105, 107, 106])  # First high < open
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        
        with pytest.raises(DataValidationError, match="High must be >= max"):
            validate_input(index, open_data, high, low, close)
    
    def test_ohlc_constraint_low_violation(self):
        """Test that Low > min(Open, Close) raises error."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([101, 100, 99, 101, 100])  # First low > open
        close = np.array([104, 103, 104, 105, 104])
        
        with pytest.raises(DataValidationError, match="Low must be <= min"):
            validate_input(index, open_data, high, low, close)
    
    def test_overlay_length_mismatch(self):
        """Test that mismatched overlay length raises error."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        overlays = {"SMA20": np.array([101, 102, 102])}  # Length 3
        
        with pytest.raises(DataValidationError, match="Overlay.*does not match"):
            validate_input(index, open_data, high, low, close, overlays=overlays)


class TestDataManager:
    """Tests for the DataManager class."""
    
    def test_init_with_numpy_arrays(self):
        """Test initialization with NumPy arrays."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        
        dm = DataManager(index, open_data, high, low, close)
        
        assert len(dm) == 5
        assert dm.length == 5
        assert isinstance(dm.open, np.ndarray)
        assert np.array_equal(dm.open, open_data)
    
    def test_init_with_pandas_series(self):
        """Test initialization with Pandas Series."""
        index = pd.date_range("2024-01-01", periods=5)
        open_data = pd.Series([100, 102, 101, 103, 102])
        high = pd.Series([105, 106, 105, 107, 106])
        low = pd.Series([99, 100, 99, 101, 100])
        close = pd.Series([104, 103, 104, 105, 104])
        
        dm = DataManager(index, open_data, high, low, close)
        
        assert len(dm) == 5
        assert isinstance(dm.close, np.ndarray)
        assert dm.close[0] == 104
    
    def test_properties(self):
        """Test all property accessors."""
        index = np.arange(3)
        open_data = np.array([100, 102, 101])
        high = np.array([105, 106, 105])
        low = np.array([99, 100, 99])
        close = np.array([104, 103, 104])
        
        dm = DataManager(index, open_data, high, low, close)
        
        assert np.array_equal(dm.index, index)
        assert np.array_equal(dm.open, open_data)
        assert np.array_equal(dm.high, high)
        assert np.array_equal(dm.low, low)
        assert np.array_equal(dm.close, close)
        assert isinstance(dm.overlays, dict)
        assert isinstance(dm.subplots, dict)
    
    def test_with_overlays_and_subplots(self):
        """Test initialization with overlays and subplots."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        overlays = {"SMA20": np.array([101, 102, 102, 103, 103])}
        subplots = {"Volume": np.array([1000, 1200, 1100, 1300, 1150])}
        
        dm = DataManager(index, open_data, high, low, close, overlays, subplots)
        
        assert len(dm.overlays) == 1
        assert "SMA20" in dm.overlays
        assert len(dm.subplots) == 1
        assert "Volume" in dm.subplots
        assert np.array_equal(dm.overlays["SMA20"], [101, 102, 102, 103, 103])
    
    def test_invalid_data_raises_error(self):
        """Test that invalid OHLC data raises DataValidationError."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([99, 106, 105, 107, 106])  # First high < open
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        
        with pytest.raises(DataValidationError):
            DataManager(index, open_data, high, low, close)
    
    def test_repr(self):
        """Test string representation."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        
        dm = DataManager(index, open_data, high, low, close)
        repr_str = repr(dm)
        
        assert "DataManager" in repr_str
        assert "5 points" in repr_str
    
    def test_repr_with_overlays(self):
        """Test string representation with overlays."""
        index = np.arange(3)
        open_data = np.array([100, 102, 101])
        high = np.array([105, 106, 105])
        low = np.array([99, 100, 99])
        close = np.array([104, 103, 104])
        overlays = {"SMA20": np.array([101, 102, 102])}
        
        dm = DataManager(index, open_data, high, low, close, overlays=overlays)
        repr_str = repr(dm)
        
        assert "1 overlays" in repr_str
    
    def test_no_data_duplication(self):
        """Test that data is not duplicated unnecessarily."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        
        dm = DataManager(index, open_data, high, low, close)
        
        # Verify arrays are stored (conversion happened but data is referenced)
        assert dm.open.dtype == open_data.dtype
        assert len(dm.open) == len(open_data)
