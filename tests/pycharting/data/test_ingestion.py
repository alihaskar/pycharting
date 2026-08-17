"""Tests for data ingestion, validation, and slicing (mirrors src/pycharting/data/ingestion.py)."""

import json
import time

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays

from pycharting.data.ingestion import DataManager, DataValidationError, validate_input

# ---------------------------------------------------------------------------
# validate_input — behaviour of the free function (unconstrained module tests)
# ---------------------------------------------------------------------------


def test_valid_pandas_input():
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


def test_valid_numpy_input():
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


def test_validate_with_overlays():
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


def test_validate_with_subplots():
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


def test_to_array_none_returns_none():
    """Verify omitted data series default to None in the result."""
    index = np.arange(5)
    close = np.array([100, 102, 103, 104, 105])
    result = validate_input(index, close=close)
    assert result["open"] is None
    assert result["high"] is None
    assert result["low"] is None


def test_to_array_list_input():
    """Verify plain Python lists are converted to numpy arrays."""
    index = np.arange(5)
    result = validate_input(
        index,
        [100, 102, 101, 103, 102],
        [105, 106, 105, 107, 106],
        [99, 100, 99, 101, 100],
        [104, 103, 104, 105, 104],
    )
    assert isinstance(result["open"], np.ndarray)
    assert np.array_equal(result["open"], [100, 102, 101, 103, 102])


def test_single_series_mode():
    """Verify passing only close yields a single-series result with other fields None."""
    index = np.arange(5)
    close = np.array([100, 102, 103, 104, 105])
    result = validate_input(index, close=close)
    assert result["open"] is None
    assert result["high"] is None
    assert result["low"] is None
    assert np.array_equal(result["close"], close)


def test_open_fallback_when_none():
    """Verify open falls back to close when open is None."""
    index = np.arange(5)
    high = np.array([106, 108, 107, 109, 108])
    low = np.array([99, 100, 99, 101, 100])
    close = np.array([104, 103, 104, 105, 104])
    result = validate_input(index, None, high, low, close)
    assert np.array_equal(result["open"], close)


def test_close_fallback_when_none():
    """Verify close falls back to open when close is None."""
    index = np.arange(5)
    open_data = np.array([100, 102, 101, 103, 102])
    high = np.array([105, 106, 105, 107, 106])
    low = np.array([99, 100, 99, 101, 100])
    result = validate_input(index, open_data, high, low, None)
    assert np.array_equal(result["close"], open_data)


def test_open_close_fallback_when_both_none():
    """When neither open nor close is given, both fall back to the first provided series."""
    index = np.arange(5)
    high = np.array([106, 108, 107, 109, 108])
    low = np.array([99, 100, 99, 101, 100])
    result = validate_input(index, None, high, low, None)
    # high is the first provided series, so open and close both default to it.
    assert np.array_equal(result["open"], high)
    assert np.array_equal(result["close"], high)


def test_high_auto_computed():
    """Verify high is auto-computed as the element-wise maximum of open and close."""
    index = np.arange(5)
    open_data = np.array([100, 102, 101, 103, 102])
    close = np.array([104, 101, 104, 102, 105])
    result = validate_input(index, open_data, None, None, close)
    assert np.array_equal(result["high"], np.maximum(open_data, close))


def test_low_auto_computed():
    """Verify low is auto-computed as the element-wise minimum of open and close."""
    index = np.arange(5)
    open_data = np.array([100, 102, 101, 103, 102])
    close = np.array([104, 101, 104, 102, 105])
    result = validate_input(index, open_data, None, None, close)
    assert np.array_equal(result["low"], np.minimum(open_data, close))


def test_trades_valid():
    """Verify a valid trades array is accepted and cast to int8."""
    index = np.arange(5)
    open_data = np.array([100, 102, 101, 103, 102])
    high = np.array([105, 106, 105, 107, 106])
    low = np.array([99, 100, 99, 101, 100])
    close = np.array([104, 103, 104, 105, 104])
    trades = np.array([1, 0, -1, 0, 1])
    result = validate_input(index, open_data, high, low, close, trades=trades)
    assert result["trades"] is not None
    assert result["trades"].dtype == np.int8


def test_subplot_multi_series_format():
    """Verify a list of subplot series is split into indexed keys with metadata."""
    index = np.arange(5)
    open_data = np.array([100, 102, 101, 103, 102])
    high = np.array([105, 106, 105, 107, 106])
    low = np.array([99, 100, 99, 101, 100])
    close = np.array([104, 103, 104, 105, 104])
    subplots = {
        "MACD": [
            {"data": np.array([1.0, 1.5, 2.0, 1.5, 1.0]), "type": "line", "label": "MACD", "color": "#f00"},
            {"data": np.array([0.5, 0.8, 1.0, 0.7, 0.5]), "type": "bar"},
        ]
    }
    result = validate_input(index, open_data, high, low, close, subplots=subplots)
    assert "MACD__0" in result["subplots"]
    assert "MACD__1" in result["subplots"]
    assert len(result["subplot_meta"]["MACD"]) == 2


def test_subplot_dict_format():
    """Verify a single-dict subplot definition is parsed with its type metadata."""
    index = np.arange(5)
    open_data = np.array([100, 102, 101, 103, 102])
    high = np.array([105, 106, 105, 107, 106])
    low = np.array([99, 100, 99, 101, 100])
    close = np.array([104, 103, 104, 105, 104])
    subplots = {"Volume": {"data": np.array([1000, 1200, 800, 1500, 1100]), "type": "bar", "color": "#0f0"}}
    result = validate_input(index, open_data, high, low, close, subplots=subplots)
    assert "Volume" in result["subplots"]
    assert result["subplot_meta"]["Volume"][0]["type"] == "bar"


class TestDataValidationError:
    """Tests for the conditions that raise DataValidationError."""

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

        with pytest.raises(DataValidationError, match=r"Overlay.*does not match"):
            validate_input(index, open_data, high, low, close, overlays=overlays)

    def test_to_array_invalid_type_raises(self):
        """Verify passing a non-array-like type as a data series raises an error."""
        index = np.arange(5)
        with pytest.raises(DataValidationError):
            validate_input(index, "invalid", np.zeros(5), np.zeros(5), np.zeros(5))

    def test_no_series_raises(self):
        """Verify calling validate_input with no data series raises an error."""
        index = np.arange(5)
        with pytest.raises(DataValidationError, match="At least one data series"):
            validate_input(index)

    def test_trades_invalid_values_raise(self):
        """Verify a trades array with values outside -1, 0, 1 raises an error."""
        index = np.arange(5)
        close = np.array([100, 102, 103, 104, 105])
        with pytest.raises(DataValidationError, match="Trades array must contain only"):
            validate_input(index, close=close, trades=np.array([1, 2, -1, 0, 1]))

    def test_datamanager_propagates_validation_error(self):
        """Test that invalid OHLC data raises DataValidationError through DataManager."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([99, 106, 105, 107, 106])  # First high < open
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])

        with pytest.raises(DataValidationError):
            DataManager(index, open_data, high, low, close)


class TestDataManager:
    """Tests for the DataManager class, including its get_chunk slicing."""

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

        trades = np.array([1, 0, -1])
        subplots = {"Volume": {"data": np.array([10, 20, 30]), "type": "bar"}}

        dm = DataManager(index, open_data, high, low, close, subplots=subplots, trades=trades)

        assert np.array_equal(dm.index, index)
        assert np.array_equal(dm.open, open_data)
        assert np.array_equal(dm.high, high)
        assert np.array_equal(dm.low, low)
        assert np.array_equal(dm.close, close)
        assert isinstance(dm.overlays, dict)
        assert isinstance(dm.subplots, dict)
        assert np.array_equal(dm.trades, trades)
        assert dm.subplot_meta["Volume"][0]["type"] == "bar"

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

    def test_repr_with_subplots(self):
        """Verify the DataManager repr reports the number of subplots."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        subplots = {"RSI": np.array([55, 58, 52, 60, 57])}
        dm = DataManager(index, open_data, high, low, close, subplots=subplots)
        assert "1 subplots" in repr(dm)

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

    def test_timestamp_conversion_to_milliseconds(self):
        """Test that DatetimeIndex is converted to Unix timestamps in milliseconds."""
        # Create a DatetimeIndex with known timestamps
        index = pd.date_range("2024-01-01", periods=5, freq="h")
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])

        dm = DataManager(index, open_data, high, low, close)

        # Get chunk should return timestamps in milliseconds
        chunk = dm.get_chunk(0, 5)

        # Verify that index is a list of integers (Unix timestamps in milliseconds)
        assert isinstance(chunk["index"], list)
        assert all(isinstance(x, int) for x in chunk["index"])

        # Verify timestamps are in the correct range (milliseconds since epoch)
        # For 2024-01-01, timestamps should be around 1704067200000 (ms)
        expected_first_ts = int(pd.Timestamp("2024-01-01").timestamp() * 1000)
        assert chunk["index"][0] == expected_first_ts

        # Verify timestamps are 1 hour apart (3600000 ms)
        assert chunk["index"][1] - chunk["index"][0] == 3600000

    def test_numeric_index_unchanged(self):
        """Test that numeric indices are not converted to timestamps."""
        # Use plain numeric index
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])

        dm = DataManager(index, open_data, high, low, close)

        # Get chunk should return plain numeric indices
        chunk = dm.get_chunk(0, 5)

        # Verify that index is unchanged
        assert chunk["index"] == [0, 1, 2, 3, 4]

    def test_unix_timestamp_index_unchanged(self):
        """Test that raw Unix timestamps (already in milliseconds) pass through unchanged."""
        # Use Unix timestamps in milliseconds (like JavaScript Date.now())
        base_ts = 1704067200000  # 2024-01-01 in milliseconds
        index = np.array([base_ts + i * 3600000 for i in range(5)])
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])

        dm = DataManager(index, open_data, high, low, close)

        # Get chunk should return timestamps unchanged
        chunk = dm.get_chunk(0, 5)

        # Verify timestamps are preserved
        assert chunk["index"] == index.tolist()
        assert all(isinstance(x, int) for x in chunk["index"])

    def test_timezone_aware_index(self):
        """Test that timezone-aware indices are correctly converted to milliseconds."""
        # Create a timezone-aware index (UTC)
        index = pd.date_range("2024-01-01", periods=5, freq="h", tz="UTC")
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])

        dm = DataManager(index, open_data, high, low, close)

        # Get chunk should return valid integer timestamps, NOT Timestamps objects
        chunk = dm.get_chunk(0, 5)

        # Verify conversion
        assert isinstance(chunk["index"], list)
        assert all(isinstance(x, int) for x in chunk["index"])

        # Expected timestamp (1704067200000 for 2024-01-01 UTC)
        expected_ts = 1704067200000
        assert chunk["index"][0] == expected_ts

    def test_get_chunk_includes_subplot_meta(self):
        """Verify get_chunk includes subplot_meta with subplot keys in the result."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        subplots = {"Volume": np.array([1000, 1200, 1100, 1300, 1150])}
        dm = DataManager(index, open_data, high, low, close, subplots=subplots)
        chunk = dm.get_chunk(0, 5)
        assert "subplot_meta" in chunk
        assert "Volume" in chunk["subplot_meta"]

    def test_get_chunk_basic(self):
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

    def test_get_chunk_middle(self):
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

    def test_get_chunk_with_none_start(self):
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

    def test_get_chunk_with_none_end(self):
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

    def test_get_chunk_with_both_none(self):
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

    def test_get_chunk_empty(self):
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

    def test_get_chunk_out_of_bounds_positive(self):
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

    def test_get_chunk_out_of_bounds_negative(self):
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

    def test_get_chunk_inverted_indices(self):
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

    def test_get_chunk_with_overlays(self):
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

    def test_get_chunk_with_subplots(self):
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

    def test_get_chunk_json_serializable(self):
        """Test that chunk output is JSON serializable."""
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

    def test_get_chunk_performance_large_dataset(self):
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

    def test_get_chunk_performance_small_slice_large_dataset(self):
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

    def test_get_chunk_data_types(self):
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


# ---------------------------------------------------------------------------
# Property-based tests — run by `make hypothesis-test` (-m "hypothesis or property")
# and, being under tests/pycharting/, also by the regular `make test` run.
#
# validate_input's contract is stated as invariants rather than examples: every
# output is a length-n ndarray, length disagreement always raises, and the
# single-vs-multi series mode is decided purely by how many of OHLC are present.
# Those are properties, so they are tested as properties.
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(
    values=arrays(
        dtype=np.float64,
        shape=st.integers(min_value=1, max_value=200),
        elements=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False),
    ),
)
@settings(max_examples=50, deadline=None)
def test_close_only_input_always_normalizes_to_line_mode(values):
    """Any single series is mapped to `close`, leaving open/high/low unset."""
    result = validate_input(np.arange(len(values)), close=values)

    assert isinstance(result["close"], np.ndarray)
    assert len(result["close"]) == len(values)
    assert result["open"] is None
    assert result["high"] is None
    assert result["low"] is None


@pytest.mark.property
@given(
    n=st.integers(min_value=1, max_value=200),
    delta=st.integers(min_value=1, max_value=20),
)
@settings(max_examples=50, deadline=None)
def test_length_mismatch_always_raises(n, delta):
    """A series whose length differs from the index is always rejected."""
    index = np.arange(n)
    close = np.zeros(n + delta)

    with pytest.raises(DataValidationError, match="does not match index length"):
        validate_input(index, close=close)


@pytest.mark.property
@given(
    values=arrays(
        dtype=np.float64,
        shape=st.integers(min_value=1, max_value=100),
        elements=st.floats(min_value=1.0, max_value=1e5, allow_nan=False),
    ),
)
@settings(max_examples=50, deadline=None)
def test_ohlc_high_is_never_below_low(values):
    """With open and close supplied, the auto-filled high never falls below low."""
    result = validate_input(np.arange(len(values)), open=values, close=values + 1.0)

    assert np.all(result["high"] >= result["low"])


@pytest.mark.property
@given(
    values=st.lists(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False), min_size=1, max_size=100),
)
@settings(max_examples=50, deadline=None)
def test_list_series_and_ndarray_series_agree(values):
    """Passing a list and the equivalent ndarray produce the same normalized output."""
    index = np.arange(len(values))

    from_list = validate_input(index, close=values)
    from_array = validate_input(index, close=np.array(values, dtype=np.float64))

    assert np.array_equal(from_list["close"], from_array["close"])
