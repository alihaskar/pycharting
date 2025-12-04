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
    open_data: Union[pd.Series, np.ndarray],
    high: Union[pd.Series, np.ndarray],
    low: Union[pd.Series, np.ndarray],
    close: Union[pd.Series, np.ndarray],
    overlays: Optional[Dict[str, Union[pd.Series, np.ndarray]]] = None,
    subplots: Optional[Dict[str, Union[pd.Series, np.ndarray]]] = None,
) -> Dict[str, Any]:
    """
    Validate and normalize input data for OHLC charting.

    This function performs rigorous checks to ensure data integrity:
    - **Type Checking:** Ensures inputs are converted to NumPy arrays.
    - **Length Consistency:** Verifies that all price arrays and the index have the exact same length.
    - **Logic Validation:** Checks that `High >= max(Open, Close)` and `Low <= min(Open, Close)` for all points.
    - **Overlay/Subplot Validation:** Ensures additional series match the length of the main data.

    Args:
        index (Union[pd.Index, np.ndarray]): The x-axis data.
        open_data (Union[pd.Series, np.ndarray]): Opening prices.
        high (Union[pd.Series, np.ndarray]): High prices.
        low (Union[pd.Series, np.ndarray]): Low prices.
        close (Union[pd.Series, np.ndarray]): Closing prices.
        overlays (Optional[Dict[str, Union[pd.Series, np.ndarray]]]): Dictionary of overlay series.
        subplots (Optional[Dict[str, Union[pd.Series, np.ndarray]]]): Dictionary of subplot series.

    Returns:
        Dict[str, Any]: A dictionary containing normalized `numpy.ndarray` objects for all inputs.

    Raises:
        DataValidationError: If any validation check fails (e.g., mismatched lengths, invalid OHLC logic).
    """
    # Convert index to numpy array if needed
    if isinstance(index, pd.Index):
        index_array = index.to_numpy()
    elif isinstance(index, np.ndarray):
        index_array = index
    else:
        raise DataValidationError(f"Index must be pd.Index or np.ndarray, got {type(index)}")
    
    # Helper function to convert to numpy array
    def to_array(data: Union[pd.Series, np.ndarray], name: str) -> np.ndarray:
        if isinstance(data, pd.Series):
            return data.to_numpy()
        elif isinstance(data, np.ndarray):
            return data
        else:
            raise DataValidationError(f"{name} must be pd.Series or np.ndarray, got {type(data)}")
    
    # Convert OHLC data to arrays
    open_array = to_array(open_data, "Open")
    high_array = to_array(high, "High")
    low_array = to_array(low, "Low")
    close_array = to_array(close, "Close")
    
    # Validate shapes
    n = len(index_array)
    for name, arr in [("Open", open_array), ("High", high_array), 
                      ("Low", low_array), ("Close", close_array)]:
        if len(arr) != n:
            raise DataValidationError(
                f"{name} length ({len(arr)}) does not match index length ({n})"
            )
    
    # Validate OHLC constraints
    # High should be >= max(open, close)
    max_oc = np.maximum(open_array, close_array)
    if not np.all(high_array >= max_oc):
        invalid_indices = np.where(high_array < max_oc)[0]
        raise DataValidationError(
            f"High must be >= max(Open, Close). Violations at indices: {invalid_indices[:5]}"
        )
    
    # Low should be <= min(open, close)
    min_oc = np.minimum(open_array, close_array)
    if not np.all(low_array <= min_oc):
        invalid_indices = np.where(low_array > min_oc)[0]
        raise DataValidationError(
            f"Low must be <= min(Open, Close). Violations at indices: {invalid_indices[:5]}"
        )
    
    result = {
        "index": index_array,
        "open": open_array,
        "high": high_array,
        "low": low_array,
        "close": close_array,
        "overlays": {},
        "subplots": {},
    }
    
    # Validate and convert overlays
    if overlays:
        for name, data in overlays.items():
            arr = to_array(data, f"Overlay '{name}'")
            if len(arr) != n:
                raise DataValidationError(
                    f"Overlay '{name}' length ({len(arr)}) does not match index length ({n})"
                )
            result["overlays"][name] = arr
    
    # Validate and convert subplots
    if subplots:
        for name, data in subplots.items():
            arr = to_array(data, f"Subplot '{name}'")
            if len(arr) != n:
                raise DataValidationError(
                    f"Subplot '{name}' length ({len(arr)}) does not match index length ({n})"
                )
            result["subplots"][name] = arr
    
    return result


class DataManager:
    """
    High-performance data container and manager.

    This class holds the financial data in memory as optimized NumPy arrays. It provides
    methods to slice and access this data efficiently for the API. It ensures that
    the data served to the frontend is always consistent and valid.

    Attributes:
        index (np.ndarray): The x-axis values.
        open (np.ndarray): Opening prices.
        high (np.ndarray): High prices.
        low (np.ndarray): Low prices.
        close (np.ndarray): Closing prices.
        overlays (Dict[str, np.ndarray]): Additional series overlaying the main chart.
        subplots (Dict[str, np.ndarray]): Additional series in separate panels.
        length (int): The total number of data points.
    """
    
    def __init__(
        self,
        index: Union[pd.Index, np.ndarray],
        open: Union[pd.Series, np.ndarray],
        high: Union[pd.Series, np.ndarray],
        low: Union[pd.Series, np.ndarray],
        close: Union[pd.Series, np.ndarray],
        overlays: Optional[Dict[str, Union[pd.Series, np.ndarray]]] = None,
        subplots: Optional[Dict[str, Union[pd.Series, np.ndarray]]] = None,
    ):
        """
        Initialize the DataManager with validated OHLC data.

        Args:
            index (Union[pd.Index, np.ndarray]): Time/Index data.
            open (Union[pd.Series, np.ndarray]): Open prices.
            high (Union[pd.Series, np.ndarray]): High prices.
            low (Union[pd.Series, np.ndarray]): Low prices.
            close (Union[pd.Series, np.ndarray]): Close prices.
            overlays (Optional[Dict[str, Union[pd.Series, np.ndarray]]]): Overlay data series.
            subplots (Optional[Dict[str, Union[pd.Series, np.ndarray]]]): Subplot data series.

        Raises:
            DataValidationError: If the input data fails validation checks.
        """
        # Validate input and get normalized arrays
        validated = validate_input(index, open, high, low, close, overlays, subplots)
        
        # Store references (numpy arrays are views where possible, avoiding duplication)
        self._index = validated["index"]
        self._open = validated["open"]
        self._high = validated["high"]
        self._low = validated["low"]
        self._close = validated["close"]
        self._overlays = validated["overlays"]
        self._subplots = validated["subplots"]
        
        self._length = len(self._index)
    
    @property
    def index(self) -> np.ndarray:
        """Get the index array."""
        return self._index
    
    @property
    def open(self) -> np.ndarray:
        """Get the open prices array."""
        return self._open
    
    @property
    def high(self) -> np.ndarray:
        """Get the high prices array."""
        return self._high
    
    @property
    def low(self) -> np.ndarray:
        """Get the low prices array."""
        return self._low
    
    @property
    def close(self) -> np.ndarray:
        """Get the close prices array."""
        return self._close
    
    @property
    def overlays(self) -> Dict[str, np.ndarray]:
        """Get the overlays dictionary."""
        return self._overlays
    
    @property
    def subplots(self) -> Dict[str, np.ndarray]:
        """Get the subplots dictionary."""
        return self._subplots
    
    @property
    def length(self) -> int:
        """Get the number of data points."""
        return self._length
    
    def __len__(self) -> int:
        """Return the number of data points."""
        return self._length
    
    def __repr__(self) -> str:
        """String representation of DataManager."""
        overlay_info = f", {len(self._overlays)} overlays" if self._overlays else ""
        subplot_info = f", {len(self._subplots)} subplots" if self._subplots else ""
        return f"DataManager({self._length} points{overlay_info}{subplot_info})"
    
    def get_chunk(
        self,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve a slice of the dataset for a specific range.

        This method is critical for performance. It extracts a specific window of data
        (e.g., what is currently visible on the screen) to send to the client.
        It converts NumPy arrays to standard Python lists for JSON serialization.

        Args:
            start_index (Optional[int]): The starting index (inclusive). Defaults to 0.
            end_index (Optional[int]): The ending index (exclusive). Defaults to total length.

        Returns:
            Dict[str, Any]: A dictionary containing sliced data lists for:
                - `index`
                - `open`, `high`, `low`, `close`
                - `overlays` (all keys)
                - `subplots` (all keys)

        Example:
            ```python
            # Get the first 100 data points
            chunk = dm.get_chunk(0, 100)
            
            # Get data from index 500 to the end
            chunk = dm.get_chunk(500, None)
            ```
        """
        # Handle default values
        if start_index is None:
            start_index = 0
        if end_index is None:
            end_index = self._length
        
        # Clamp indices to valid range
        start_index = max(0, min(start_index, self._length))
        end_index = max(start_index, min(end_index, self._length))
        
        # Slice arrays (views, not copies - very efficient)
        result = {
            "index": self._index[start_index:end_index].tolist(),
            "open": self._open[start_index:end_index].tolist(),
            "high": self._high[start_index:end_index].tolist(),
            "low": self._low[start_index:end_index].tolist(),
            "close": self._close[start_index:end_index].tolist(),
            "overlays": {},
            "subplots": {},
        }
        
        # Include overlays
        for name, data in self._overlays.items():
            result["overlays"][name] = data[start_index:end_index].tolist()
        
        # Include subplots
        for name, data in self._subplots.items():
            result["subplots"][name] = data[start_index:end_index].tolist()
        
        return result
