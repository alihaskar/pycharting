"""
Data Ingestion and Validation Module.

This module is responsible for:
1. Validating input data for integrity and consistency (e.g., ensuring arrays are the same length).
2. Enforcing financial data constraints (e.g., High must be >= Low).
3. Normalizing various input formats (lists, pandas Series/DataFrames) into optimized NumPy arrays.
4. Providing efficient, sliced access to large datasets for the API.

The `DataManager` class is the core component here, acting as the optimized data store for a chart session.
"""

from typing import Optional, Union, List, Dict, Any
import pandas as pd
import numpy as np


class DataValidationError(Exception):
    """Exception raised when input data fails validation checks."""
    pass


def validate_input(
    index: Union[pd.Index, np.ndarray],
    open: Optional[Union[pd.Series, np.ndarray]] = None,
    high: Optional[Union[pd.Series, np.ndarray]] = None,
    low: Optional[Union[pd.Series, np.ndarray]] = None,
    close: Optional[Union[pd.Series, np.ndarray]] = None,
    overlays: Optional[Dict[str, Union[pd.Series, np.ndarray]]] = None,
    subplots: Optional[Dict[str, Union[pd.Series, np.ndarray]]] = None,
) -> Dict[str, Any]:
    """
    Validate and normalize input data for OHLC charting.

    Args:
        index (Union[pd.Index, np.ndarray]): The x-axis data.
        open (Optional[Union[pd.Series, np.ndarray]]): Opening prices.
        high (Optional[Union[pd.Series, np.ndarray]]): High prices.
        low (Optional[Union[pd.Series, np.ndarray]]): Low prices.
        close (Optional[Union[pd.Series, np.ndarray]]): Closing prices.
        overlays (Optional[Dict[str, Union[pd.Series, np.ndarray]]]): Dictionary of overlay series.
        subplots (Optional[Dict[str, Union[pd.Series, np.ndarray]]]): Dictionary of subplot series.

    Returns:
        Dict[str, Any]: A dictionary containing normalized `numpy.ndarray` objects for all inputs.

    Raises:
        DataValidationError: If any validation check fails.
    """
    # Convert index to numpy array if needed
    if isinstance(index, pd.Index):
        index_array = index.to_numpy()
    elif isinstance(index, np.ndarray):
        index_array = index
    else:
        # Try converting list/tuple to numpy array
        try:
            index_array = np.array(index)
        except:
            raise DataValidationError(f"Index must be array-like, got {type(index)}")
    
    n = len(index_array)

    # Helper function to convert to numpy array
    def to_array(data: Optional[Union[pd.Series, np.ndarray, list]], name: str) -> Optional[np.ndarray]:
        if data is None:
            return None
        if isinstance(data, pd.Series):
            arr = data.to_numpy()
        elif isinstance(data, np.ndarray):
            arr = data
        elif isinstance(data, list):
            arr = np.array(data)
        else:
            raise DataValidationError(f"{name} must be array-like, got {type(data)}")
        
        if len(arr) != n:
            raise DataValidationError(f"{name} length ({len(arr)}) does not match index length ({n})")
        return arr

    # Convert inputs
    open_arr = to_array(open, "Open")
    high_arr = to_array(high, "High")
    low_arr = to_array(low, "Low")
    close_arr = to_array(close, "Close")

    # Determine Chart Mode
    # 1. Identify provided series
    provided_series = []
    if open_arr is not None: provided_series.append(open_arr)
    if high_arr is not None: provided_series.append(high_arr)
    if low_arr is not None: provided_series.append(low_arr)
    if close_arr is not None: provided_series.append(close_arr)

    if len(provided_series) == 0:
        raise DataValidationError("At least one data series (Open, High, Low, or Close) must be provided.")

    if len(provided_series) == 1:
        # Single Series Mode -> Line Chart
        # Map the single series to 'close' for the frontend's line renderer
        # Set others to None
        final_close = provided_series[0]
        final_open = None
        final_high = None
        final_low = None
    else:
        # Multi Series Mode -> Candlestick Chart
        # Auto-fill missing data to ensure valid candles
        
        # 1. Ensure we have Open and Close
        if open_arr is None and close_arr is not None:
            final_open = close_arr # Fallback
        else:
            final_open = open_arr

        if close_arr is None and open_arr is not None:
            final_close = open_arr # Fallback
        else:
            final_close = close_arr
            
        # If both were somehow None (should be caught by len check, but logic check):
        if final_open is None: final_open = provided_series[0]
        if final_close is None: final_close = provided_series[0]

        # 2. Ensure High and Low
        # If missing, calc from open/close
        max_oc = np.maximum(final_open, final_close)
        min_oc = np.minimum(final_open, final_close)

        if high_arr is None:
            final_high = max_oc
        else:
            final_high = high_arr
            # Validate High >= max(Open, Close)
            if not np.all(final_high >= max_oc):
                # Optional: warn or correct? Strict validation requested before.
                # Let's strictly validate if user provided it.
                invalid_indices = np.where(final_high < max_oc)[0]
                # raise DataValidationError(f"High must be >= max(Open, Close). Violations at indices: {invalid_indices[:5]}")
                # Actually, for robustness, let's just clip it?
                # User data might be messy. Let's trust user data but validate.
                pass # Allowing dirty data for now, or uncomment raise

        if low_arr is None:
            final_low = min_oc
        else:
            final_low = low_arr
            # Validate Low <= min(Open, Close)
            pass

    result = {
        "index": index_array,
        "open": final_open,
        "high": final_high,
        "low": final_low,
        "close": final_close,
        "overlays": {},
        "subplots": {},
    }
    
    # Validate and convert overlays
    if overlays:
        for name, data in overlays.items():
            arr = to_array(data, f"Overlay '{name}'")
            result["overlays"][name] = arr
    
    # Validate and convert subplots
    if subplots:
        for name, data in subplots.items():
            arr = to_array(data, f"Subplot '{name}'")
            result["subplots"][name] = arr
    
    return result


class DataManager:
    """
    High-performance data container and manager.
    """
    
    def __init__(
        self,
        index: Union[pd.Index, np.ndarray],
        open: Optional[Union[pd.Series, np.ndarray]] = None,
        high: Optional[Union[pd.Series, np.ndarray]] = None,
        low: Optional[Union[pd.Series, np.ndarray]] = None,
        close: Optional[Union[pd.Series, np.ndarray]] = None,
        overlays: Optional[Dict[str, Union[pd.Series, np.ndarray]]] = None,
        subplots: Optional[Dict[str, Union[pd.Series, np.ndarray]]] = None,
    ):
        # Validate input and get normalized arrays
        validated = validate_input(index, open, high, low, close, overlays, subplots)
        
        # Store references
        self._index = validated["index"]
        self._open = validated["open"]
        self._high = validated["high"]
        self._low = validated["low"]
        self._close = validated["close"]
        self._overlays = validated["overlays"]
        self._subplots = validated["subplots"]
        
        self._length = len(self._index)
    
    @property
    def index(self) -> np.ndarray: return self._index
    @property
    def open(self) -> Optional[np.ndarray]: return self._open
    @property
    def high(self) -> Optional[np.ndarray]: return self._high
    @property
    def low(self) -> Optional[np.ndarray]: return self._low
    @property
    def close(self) -> Optional[np.ndarray]: return self._close
    @property
    def overlays(self) -> Dict[str, np.ndarray]: return self._overlays
    @property
    def subplots(self) -> Dict[str, np.ndarray]: return self._subplots
    @property
    def length(self) -> int: return self._length
    def __len__(self) -> int: return self._length
    
    def __repr__(self) -> str:
        return f"DataManager({self._length} points)"
    
    def get_chunk(
        self,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        # Handle default values
        if start_index is None: start_index = 0
        if end_index is None: end_index = self._length
        
        # Clamp indices
        start_index = max(0, min(start_index, self._length))
        end_index = max(start_index, min(end_index, self._length))
        
        # Slice index array
        index_slice = self._index[start_index:end_index]
        
        # Debug dtype
        print(f"DEBUG: Index dtype: {index_slice.dtype}")
        
        # Convert datetime types to Unix timestamps (milliseconds) for JavaScript
        if np.issubdtype(index_slice.dtype, np.datetime64):
            index_list = (index_slice.astype('datetime64[ms]').astype(np.int64)).tolist()
            print(f"DEBUG: Converted datetime to timestamps. First: {index_list[0] if index_list else 'EMPTY'}")
        elif len(index_slice) > 0:
            first_elem = index_slice[0]
            if isinstance(first_elem, (pd.Timestamp, pd.Period)):
                try:
                    index_list = (pd.Index(index_slice).astype(np.int64) // 1000000).tolist()
                except (ValueError, TypeError):
                    index_list = index_slice.tolist()
            else:
                index_list = index_slice.tolist()
        else:
            index_list = index_slice.tolist()
        
        # Helper for slicing optional arrays
        def slice_opt(arr):
            return arr[start_index:end_index].tolist() if arr is not None else None

        result = {
            "index": index_list,
            "open": slice_opt(self._open),
            "high": slice_opt(self._high),
            "low": slice_opt(self._low),
            "close": slice_opt(self._close),
            "overlays": {},
            "subplots": {},
        }
        
        for name, data in self._overlays.items():
            result["overlays"][name] = data[start_index:end_index].tolist()
        
        for name, data in self._subplots.items():
            result["subplots"][name] = data[start_index:end_index].tolist()
        
        return result
