"""Tests for data slicing functionality."""

import pytest
import numpy as np
import time
from src.data.ingestion import DataManager


class TestGetChunk:
    """Tests for the get_chunk method."""
    
    def test_basic_chunk(self):
        """Test basic chunk retrieval."""
        index = np.arange(10)
        open_data = np.array([100, 102, 101, 103, 102, 104, 103, 105, 104, 106])
        high = np.array([105, 106, 105, 107, 106, 108, 107, 109, 108, 110])
        low = np.array([99, 100, 99, 101, 100, 102, 101, 103, 102, 104])
        close = np.array([104, 103, 104, 105, 104, 106, 105, 107, 106, 108])
        
        dm = DataManager(index, open_data, high, low, close)
        chunk = dm.get_chunk(0, 5)
        
        assert len(chunk["index"]) == 5
        assert chunk["index"] == [0, 1, 2, 3, 4]
        assert chunk["open"] == [100, 102, 101, 103, 102]
        assert chunk["close"] == [104, 103, 104, 105, 104]
    
    def test_middle_chunk(self):
        """Test retrieving a chunk from the middle of data."""
        index = np.arange(10)
        open_data = np.arange(100, 110)
        high = np.arange(105, 115)
        low = np.arange(95, 105)
        close = np.arange(102, 112)
        
        dm = DataManager(index, open_data, high, low, close)
        chunk = dm.get_chunk(3, 7)
        
        assert len(chunk["index"]) == 4
        assert chunk["index"] == [3, 4, 5, 6]
        assert chunk["open"] == [103, 104, 105, 106]
    
    def test_chunk_with_none_start(self):
        """Test chunk with None start index (from beginning)."""
        index = np.arange(10)
        open_data = np.arange(100, 110)
        high = np.arange(105, 115)
        low = np.arange(95, 105)
        close = np.arange(102, 112)
        
        dm = DataManager(index, open_data, high, low, close)
        chunk = dm.get_chunk(None, 5)
        
        assert len(chunk["index"]) == 5
        assert chunk["index"] == [0, 1, 2, 3, 4]
    
    def test_chunk_with_none_end(self):
        """Test chunk with None end index (to end)."""
        index = np.arange(10)
        open_data = np.arange(100, 110)
        high = np.arange(105, 115)
        low = np.arange(95, 105)
        close = np.arange(102, 112)
        
        dm = DataManager(index, open_data, high, low, close)
        chunk = dm.get_chunk(7, None)
        
        assert len(chunk["index"]) == 3
        assert chunk["index"] == [7, 8, 9]
        assert chunk["open"] == [107, 108, 109]
    
    def test_chunk_with_both_none(self):
        """Test chunk with both indices None (entire dataset)."""
        index = np.arange(5)
        open_data = np.arange(100, 105)
        high = np.arange(105, 110)
        low = np.arange(95, 100)
        close = np.arange(102, 107)
        
        dm = DataManager(index, open_data, high, low, close)
        chunk = dm.get_chunk(None, None)
        
        assert len(chunk["index"]) == 5
        assert chunk["index"] == [0, 1, 2, 3, 4]
    
    def test_empty_chunk(self):
        """Test empty chunk when start equals end."""
        index = np.arange(10)
        open_data = np.arange(100, 110)
        high = np.arange(105, 115)
        low = np.arange(95, 105)
        close = np.arange(102, 112)
        
        dm = DataManager(index, open_data, high, low, close)
        chunk = dm.get_chunk(5, 5)
        
        assert len(chunk["index"]) == 0
        assert chunk["open"] == []
    
    def test_out_of_bounds_positive(self):
        """Test chunk with indices beyond data length."""
        index = np.arange(10)
        open_data = np.arange(100, 110)
        high = np.arange(105, 115)
        low = np.arange(95, 105)
        close = np.arange(102, 112)
        
        dm = DataManager(index, open_data, high, low, close)
        chunk = dm.get_chunk(8, 20)  # End beyond length
        
        assert len(chunk["index"]) == 2  # Clamped to available data
        assert chunk["index"] == [8, 9]
    
    def test_out_of_bounds_negative(self):
        """Test chunk with negative start index."""
        index = np.arange(10)
        open_data = np.arange(100, 110)
        high = np.arange(105, 115)
        low = np.arange(95, 105)
        close = np.arange(102, 112)
        
        dm = DataManager(index, open_data, high, low, close)
        chunk = dm.get_chunk(-5, 5)  # Negative start
        
        # Negative indices should be clamped to 0
        assert len(chunk["index"]) == 5
        assert chunk["index"] == [0, 1, 2, 3, 4]
    
    def test_inverted_indices(self):
        """Test chunk with start > end (should return empty)."""
        index = np.arange(10)
        open_data = np.arange(100, 110)
        high = np.arange(105, 115)
        low = np.arange(95, 105)
        close = np.arange(102, 112)
        
        dm = DataManager(index, open_data, high, low, close)
        chunk = dm.get_chunk(7, 3)  # Start > end
        
        # Should clamp end_index to be at least start_index
        assert len(chunk["index"]) == 0
    
    def test_chunk_with_overlays(self):
        """Test chunk includes overlay data."""
        index = np.arange(10)
        open_data = np.arange(100, 110)
        high = np.arange(105, 115)
        low = np.arange(95, 105)
        close = np.arange(102, 112)
        overlays = {
            "SMA20": np.arange(101, 111),
            "EMA10": np.arange(100.5, 110.5),
        }
        
        dm = DataManager(index, open_data, high, low, close, overlays=overlays)
        chunk = dm.get_chunk(2, 7)
        
        assert len(chunk["overlays"]) == 2
        assert "SMA20" in chunk["overlays"]
        assert "EMA10" in chunk["overlays"]
        assert chunk["overlays"]["SMA20"] == [103, 104, 105, 106, 107]
        assert len(chunk["overlays"]["EMA10"]) == 5
    
    def test_chunk_with_subplots(self):
        """Test chunk includes subplot data."""
        index = np.arange(10)
        open_data = np.arange(100, 110)
        high = np.arange(105, 115)
        low = np.arange(95, 105)
        close = np.arange(102, 112)
        subplots = {
            "Volume": np.arange(1000, 1010) * 100,
            "RSI": np.arange(50, 60),
        }
        
        dm = DataManager(index, open_data, high, low, close, subplots=subplots)
        chunk = dm.get_chunk(1, 6)
        
        assert len(chunk["subplots"]) == 2
        assert "Volume" in chunk["subplots"]
        assert "RSI" in chunk["subplots"]
        assert len(chunk["subplots"]["Volume"]) == 5
        assert chunk["subplots"]["RSI"] == [51, 52, 53, 54, 55]
    
    def test_chunk_json_serializable(self):
        """Test that chunk output is JSON serializable."""
        import json
        
        index = np.arange(5)
        open_data = np.arange(100, 105)
        high = np.arange(105, 110)
        low = np.arange(95, 100)
        close = np.arange(102, 107)
        
        dm = DataManager(index, open_data, high, low, close)
        chunk = dm.get_chunk(0, 5)
        
        # Should not raise any exception
        json_str = json.dumps(chunk)
        assert isinstance(json_str, str)
        
        # Verify round-trip
        recovered = json.loads(json_str)
        assert recovered["index"] == chunk["index"]
        assert recovered["open"] == chunk["open"]
    
    def test_performance_large_dataset(self):
        """Test performance with large dataset (100k points)."""
        n = 100000
        index = np.arange(n)
        open_data = np.random.uniform(100, 200, n)
        high = open_data + np.random.uniform(0, 10, n)
        low = open_data - np.random.uniform(0, 10, n)
        close = np.random.uniform(low, high)
        
        dm = DataManager(index, open_data, high, low, close)
        
        # Measure slicing performance
        start_time = time.time()
        chunk = dm.get_chunk(10000, 20000)  # 10k points
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Should be well under 100ms for 10k points
        assert elapsed_ms < 100, f"Slicing took {elapsed_ms:.2f}ms, expected <100ms"
        assert len(chunk["index"]) == 10000
    
    def test_performance_small_slice_large_dataset(self):
        """Test performance of small slice from large dataset."""
        n = 100000
        index = np.arange(n)
        open_data = np.random.uniform(100, 200, n)
        high = open_data + np.random.uniform(0, 10, n)
        low = open_data - np.random.uniform(0, 10, n)
        close = np.random.uniform(low, high)
        
        dm = DataManager(index, open_data, high, low, close)
        
        # Small slice should be extremely fast
        start_time = time.time()
        chunk = dm.get_chunk(50000, 50100)  # Just 100 points
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Should be very fast (< 10ms)
        assert elapsed_ms < 10, f"Small slice took {elapsed_ms:.2f}ms, expected <10ms"
        assert len(chunk["index"]) == 100
    
    def test_chunk_data_types(self):
        """Test that chunk returns proper Python types (not numpy)."""
        index = np.arange(5)
        open_data = np.array([100.5, 102.3, 101.7, 103.2, 102.8])
        high = np.array([105.1, 106.2, 105.4, 107.3, 106.9])
        low = np.array([99.2, 100.1, 99.5, 101.3, 100.7])
        close = np.array([104.3, 103.8, 104.2, 105.6, 104.9])
        
        dm = DataManager(index, open_data, high, low, close)
        chunk = dm.get_chunk(0, 3)
        
        # All values should be Python lists, not numpy arrays
        assert isinstance(chunk["index"], list)
        assert isinstance(chunk["open"], list)
        assert isinstance(chunk["high"], list)
        assert isinstance(chunk["low"], list)
        assert isinstance(chunk["close"], list)
        
        # Individual values should be Python numbers
        assert isinstance(chunk["open"][0], (int, float))
