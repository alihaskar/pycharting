"""Data Ingestion and Validation Module.

This module is responsible for:
1. Validating input data for integrity and consistency (e.g., ensuring arrays are the same length).
2. Enforcing financial data constraints (e.g., High must be >= Low).
3. Normalizing various input formats (lists, pandas Series/DataFrames) into optimized NumPy arrays.
4. Providing efficient, sliced access to large datasets for the API.

The `DataManager` class is the core component here, acting as the optimized data store for a chart session.
"""

from typing import Any, cast

import numpy as np
import pandas as pd

# A single subplot panel may be supplied as a plain array, as a config dict
# ({"data": ..., "type": ..., "color": ..., "label": ...}), or as a list of such
# dicts for a multi-series panel.
SubplotSpec = pd.Series | np.ndarray | list | dict[str, Any]


class DataValidationError(Exception):
    """Exception raised when input data fails validation checks."""

    pass


def validate_input(
    index: pd.Index | pd.Series | np.ndarray,
    open: pd.Series | np.ndarray | None = None,
    high: pd.Series | np.ndarray | None = None,
    low: pd.Series | np.ndarray | None = None,
    close: pd.Series | np.ndarray | None = None,
    overlays: dict[str, pd.Series | np.ndarray | list] | None = None,
    subplots: dict[str, SubplotSpec] | None = None,
    trades: pd.Series | np.ndarray | list | None = None,
) -> dict[str, Any]:
    """Validate and normalize input data for OHLC charting.

    Args:
        index (Union[pd.Index, np.ndarray]): The x-axis data.
        open (Optional[Union[pd.Series, np.ndarray]]): Opening prices.
        high (Optional[Union[pd.Series, np.ndarray]]): High prices.
        low (Optional[Union[pd.Series, np.ndarray]]): Low prices.
        close (Optional[Union[pd.Series, np.ndarray]]): Closing prices.
        overlays (Optional[Dict[str, Union[pd.Series, np.ndarray]]]): Dictionary of overlay series.
        subplots (Optional[Dict[str, Union[pd.Series, np.ndarray]]]): Dictionary of subplot series.
        trades (Optional[Union[pd.Series, np.ndarray, list]]): Trade markers aligned with the index,
            encoded as +1 (buy/long), -1 (sell/short), or 0 (no trade).

    Returns:
        Dict[str, Any]: A dictionary containing normalized `numpy.ndarray` objects for all inputs.

    Raises:
        DataValidationError: If any validation check fails.

    Example:
        A single series is mapped to ``close`` and rendered as a line chart,
        leaving the other price fields unset:

        >>> import numpy as np
        >>> result = validate_input(np.arange(3), close=np.array([10.0, 11.0, 12.0]))
        >>> result["close"].tolist()
        [10.0, 11.0, 12.0]
        >>> result["open"] is None
        True

        With open and close supplied, high and low are filled in from them:

        >>> result = validate_input(
        ...     np.arange(3),
        ...     open=np.array([10.0, 11.0, 12.0]),
        ...     close=np.array([11.0, 10.0, 13.0]),
        ... )
        >>> result["high"].tolist()
        [11.0, 11.0, 13.0]
        >>> result["low"].tolist()
        [10.0, 10.0, 12.0]

        A series whose length disagrees with the index is rejected:

        >>> validate_input(np.arange(3), close=np.array([1.0, 2.0]))
        Traceback (most recent call last):
            ...
        pycharting.data.ingestion.DataValidationError: Close length (2) does not match index length (3)
    """
    # Convert index to numpy array if needed
    if isinstance(index, (pd.Index, pd.Series)):
        index_array = index.to_numpy()
    elif isinstance(index, np.ndarray):
        index_array = index
    else:
        raise DataValidationError(f"Index must be a pd.Index or np.ndarray, got {type(index)}")  # noqa: TRY003

    n = len(index_array)

    # Helper function to convert to numpy array
    def to_array(data: pd.Series | np.ndarray | list | None, name: str) -> np.ndarray | None:
        """Convert ``data`` to a length-validated numpy array, or ``None`` if not provided."""
        if data is None:
            return None
        if isinstance(data, pd.Series):
            arr = data.to_numpy()
        elif isinstance(data, np.ndarray):
            arr = data
        elif isinstance(data, list):
            arr = np.array(data)
        else:
            raise DataValidationError(f"{name} must be array-like, got {type(data)}")  # noqa: TRY003

        if len(arr) != n:
            raise DataValidationError(f"{name} length ({len(arr)}) does not match index length ({n})")  # noqa: TRY003
        return arr

    # Convert inputs
    open_arr = to_array(open, "Open")
    high_arr = to_array(high, "High")
    low_arr = to_array(low, "Low")
    close_arr = to_array(close, "Close")

    # Determine Chart Mode
    # 1. Identify provided series
    provided_series = []
    if open_arr is not None:
        provided_series.append(open_arr)
    if high_arr is not None:
        provided_series.append(high_arr)
    if low_arr is not None:
        provided_series.append(low_arr)
    if close_arr is not None:
        provided_series.append(close_arr)

    if len(provided_series) == 0:
        raise DataValidationError("At least one data series (Open, High, Low, or Close) must be provided.")  # noqa: TRY003

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

        # 1. Ensure we have Open and Close (fall back to the other when one is missing)
        final_open = close_arr if open_arr is None and close_arr is not None else open_arr
        final_close = open_arr if close_arr is None and open_arr is not None else close_arr

        # If both were somehow None (should be caught by len check, but logic check):
        if final_open is None:
            final_open = provided_series[0]
        if final_close is None:
            final_close = provided_series[0]

        # 2. Ensure High and Low
        # If missing, calc from open/close
        max_oc = np.maximum(final_open, final_close)
        min_oc = np.minimum(final_open, final_close)

        if high_arr is None:
            final_high = max_oc
        else:
            final_high = high_arr
            if not np.all(final_high >= max_oc):
                invalid_indices = np.where(final_high < max_oc)[0]
                raise DataValidationError(  # noqa: TRY003
                    f"High must be >= max(Open, Close). Violations at indices: {invalid_indices[:5]}"
                )

        if low_arr is None:
            final_low = min_oc
        else:
            final_low = low_arr
            if not np.all(final_low <= min_oc):
                invalid_indices = np.where(final_low > min_oc)[0]
                raise DataValidationError(  # noqa: TRY003
                    f"Low must be <= min(Open, Close). Violations at indices: {invalid_indices[:5]}"
                )

    # Validate trades: array of +1 (buy/long), -1 (sell/short), 0 (no trade)
    trades_arr = None
    if trades is not None:
        trades_arr = to_array(trades, "Trades")
        if trades_arr is not None:
            unique = set(np.unique(trades_arr).tolist())
            valid_vals = {-1, 0, 1, -1.0}
            if not unique.issubset(valid_vals):
                raise DataValidationError(  # noqa: TRY003
                    f"Trades array must contain only -1, 0, or 1. Found: {unique - valid_vals}"
                )
            trades_arr = trades_arr.astype(np.int8)

    result = {
        "index": index_array,
        "open": final_open,
        "high": final_high,
        "low": final_low,
        "close": final_close,
        "overlays": {},
        "subplots": {},
        "trades": trades_arr,
    }

    # Validate and convert overlays
    if overlays:
        for name, data in overlays.items():
            arr = to_array(data, f"Overlay '{name}'")
            result["overlays"][name] = arr

    # Validate and convert subplots
    # Supported formats:
    #   "name": array                    → single line
    #   "name": {"data": array, "type": "bar"|"scatter", "color": "#hex"}  → single series
    #   "name": [{"data": array, "type": ..., "color": ..., "label": ...}, ...]  → multi-series panel
    subplot_meta = {}
    if subplots:
        for name, value in subplots.items():
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                panel_series = []
                for idx, raw_entry in enumerate(value):
                    entry = cast("dict[str, Any]", raw_entry)
                    key = f"{name}__{idx}"
                    arr = to_array(entry.get("data"), f"Subplot '{name}[{idx}]'")
                    result["subplots"][key] = arr
                    panel_series.append(
                        {
                            "key": key,
                            "type": entry.get("type", "line"),
                            "color": entry.get("color"),
                            "label": entry.get("label", f"{name}_{idx}"),
                        }
                    )
                subplot_meta[name] = panel_series
            elif isinstance(value, dict):
                spec = cast("dict[str, Any]", value)
                arr = to_array(spec.get("data"), f"Subplot '{name}'")
                result["subplots"][name] = arr
                subplot_meta[name] = [
                    {
                        "key": name,
                        "type": spec.get("type", "line"),
                        "color": spec.get("color"),
                        "label": name,
                    }
                ]
            else:
                arr = to_array(value, f"Subplot '{name}'")
                result["subplots"][name] = arr
                subplot_meta[name] = [
                    {
                        "key": name,
                        "type": "line",
                        "color": None,
                        "label": name,
                    }
                ]
    result["subplot_meta"] = subplot_meta

    return result


class DataManager:
    """High-performance data container and manager.

    Validates and normalizes the supplied series once on construction, then
    serves arbitrary slices of them cheaply — one slice per viewport move.

    Example:
        >>> import numpy as np
        >>> dm = DataManager(np.arange(5), close=np.arange(5, dtype=float) * 10)
        >>> dm.length
        5
        >>> dm.close.tolist()
        [0.0, 10.0, 20.0, 30.0, 40.0]
    """

    def __init__(
        self,
        index: pd.Index | pd.Series | np.ndarray,
        open: pd.Series | np.ndarray | None = None,
        high: pd.Series | np.ndarray | None = None,
        low: pd.Series | np.ndarray | None = None,
        close: pd.Series | np.ndarray | None = None,
        overlays: dict[str, pd.Series | np.ndarray | list] | None = None,
        subplots: dict[str, SubplotSpec] | None = None,
        trades: pd.Series | np.ndarray | list | None = None,
    ) -> None:
        """Validate the supplied series and store the normalized arrays for fast slicing."""
        # Validate input and get normalized arrays
        validated = validate_input(index, open, high, low, close, overlays, subplots, trades)

        # Store references
        self._index = validated["index"]
        self._open = validated["open"]
        self._high = validated["high"]
        self._low = validated["low"]
        self._close = validated["close"]
        self._overlays = validated["overlays"]
        self._subplots = validated["subplots"]
        self._subplot_meta = validated["subplot_meta"]
        self._trades = validated["trades"]

        self._length = len(self._index)

    @property
    def index(self) -> np.ndarray:
        """The normalized x-axis (index) array."""
        return self._index

    @property
    def open(self) -> np.ndarray | None:
        """Opening prices, or ``None`` if not provided."""
        return self._open

    @property
    def high(self) -> np.ndarray | None:
        """High prices, or ``None`` if not provided."""
        return self._high

    @property
    def low(self) -> np.ndarray | None:
        """Low prices, or ``None`` if not provided."""
        return self._low

    @property
    def close(self) -> np.ndarray | None:
        """Closing prices, or ``None`` if not provided."""
        return self._close

    @property
    def overlays(self) -> dict[str, np.ndarray]:
        """Mapping of overlay names to their normalized arrays."""
        return self._overlays

    @property
    def subplots(self) -> dict[str, np.ndarray]:
        """Mapping of subplot keys to their normalized arrays."""
        return self._subplots

    @property
    def subplot_meta(self) -> dict[str, list]:
        """Per-subplot rendering metadata (type, color, label)."""
        return self._subplot_meta

    @property
    def trades(self) -> np.ndarray | None:
        """Trade marker array (+1/-1/0), or ``None`` if not provided."""
        return self._trades

    @property
    def length(self) -> int:
        """Number of data points held by this manager."""
        return self._length

    def __len__(self) -> int:
        """Return the number of data points."""
        return self._length

    def __repr__(self) -> str:
        """Return a concise summary of the manager's contents."""
        parts = [f"{self._length} points"]
        if self._overlays:
            parts.append(f"{len(self._overlays)} overlays")
        if self._subplots:
            parts.append(f"{len(self._subplots)} subplots")
        return f"DataManager({', '.join(parts)})"

    def get_chunk(
        self,
        start_index: int | None = None,
        end_index: int | None = None,
    ) -> dict[str, Any]:
        """Return a JSON-serializable slice of the data between ``start_index`` and ``end_index``.

        Indices are clamped to the available range, so an over-wide request
        returns what exists rather than raising.

        Example:
            >>> import numpy as np
            >>> dm = DataManager(np.arange(5), close=np.arange(5, dtype=float))
            >>> chunk = dm.get_chunk(1, 3)
            >>> chunk["index"]
            [1, 2]
            >>> chunk["close"]
            [1.0, 2.0]

            Omitting both bounds returns the whole series:

            >>> len(dm.get_chunk()["index"])
            5

            An end index past the last bar is clamped:

            >>> dm.get_chunk(3, 99)["close"]
            [3.0, 4.0]
        """
        # Handle default values
        if start_index is None:
            start_index = 0
        if end_index is None:
            end_index = self._length

        # Clamp indices
        start_index = max(0, min(start_index, self._length))
        end_index = max(start_index, min(end_index, self._length))

        # Slice index array
        index_slice = self._index[start_index:end_index]

        # Convert datetime types to Unix timestamps (milliseconds) for JavaScript
        if np.issubdtype(index_slice.dtype, np.datetime64):
            index_list = (index_slice.astype("datetime64[ms]").astype(np.int64)).tolist()
        elif len(index_slice) > 0:
            first_elem = index_slice[0]
            if isinstance(first_elem, (pd.Timestamp, pd.Period)):
                try:
                    index_list = (pd.Index(index_slice).astype(np.int64) // 1000000).tolist()
                except (ValueError, TypeError):  # pragma: no cover
                    index_list = index_slice.tolist()
            else:
                index_list = index_slice.tolist()
        else:
            index_list = index_slice.tolist()

        # Helper for slicing optional arrays
        def slice_opt(arr: np.ndarray | None) -> list[Any] | None:
            """Return the requested slice of ``arr`` as a list, or ``None`` if ``arr`` is ``None``."""
            return arr[start_index:end_index].tolist() if arr is not None else None

        result = {
            "index": index_list,
            "open": slice_opt(self._open),
            "high": slice_opt(self._high),
            "low": slice_opt(self._low),
            "close": slice_opt(self._close),
            "overlays": {},
            "subplots": {},
            "trades": slice_opt(self._trades),
        }

        for name, data in self._overlays.items():
            result["overlays"][name] = data[start_index:end_index].tolist()

        for name, data in self._subplots.items():
            result["subplots"][name] = data[start_index:end_index].tolist()

        if self._subplot_meta:
            result["subplot_meta"] = self._subplot_meta

        return result
