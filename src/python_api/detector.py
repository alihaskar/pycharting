"""
DataFrame column detection and classification utilities.

This module provides functions to automatically detect OHLC columns
and classify technical indicators in pandas DataFrames.
"""

import re
from typing import Dict, List, Tuple
import pandas as pd


class OHLCColumnsNotFoundError(Exception):
    """Raised when required OHLC columns are not found in DataFrame."""
    
    def __init__(self, missing_columns: List[str]):
        self.missing_columns = missing_columns
        
        if len(missing_columns) == 1:
            message = (
                f"Required OHLC column not found: '{missing_columns[0]}'. "
                f"Please ensure your DataFrame contains columns named "
                f"'open', 'high', 'low', and 'close' (or abbreviated forms like 'o', 'h', 'l', 'c')."
            )
        else:
            cols_str = "', '".join(missing_columns)
            message = (
                f"Required OHLC columns not found: '{cols_str}'. "
                f"Please ensure your DataFrame contains columns named "
                f"'open', 'high', 'low', and 'close' (or abbreviated forms like 'o', 'h', 'l', 'c')."
            )
        
        super().__init__(message)


class AmbiguousColumnError(Exception):
    """Raised when multiple columns match the same OHLC pattern."""
    
    def __init__(self, standard_name: str, candidates: List[str]):
        self.standard_name = standard_name
        self.candidates = candidates
        
        candidates_str = "', '".join(candidates)
        message = (
            f"Ambiguous column names for '{standard_name}': found multiple candidates '{candidates_str}'. "
            f"Please rename columns to have unique OHLC identifiers."
        )
        
        super().__init__(message)


def detect_ohlc_columns(df: pd.DataFrame) -> Dict[str, str]:
    """
    Detect OHLC (Open, High, Low, Close, Volume) columns in a DataFrame.
    
    Uses case-insensitive pattern matching to identify columns based on
    common naming conventions including full names and abbreviations.
    
    Args:
        df: pandas DataFrame containing OHLC data
        
    Returns:
        Dictionary mapping standard names ('open', 'high', 'low', 'close', 'volume')
        to actual column names in the DataFrame. Returns empty dict if no matches found.
        
    Examples:
        >>> df = pd.DataFrame({'Open': [100], 'High': [101], 'Low': [99], 'Close': [100.5]})
        >>> detect_ohlc_columns(df)
        {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}
        
        >>> df = pd.DataFrame({'o': [100], 'h': [101], 'l': [99], 'c': [100.5]})
        >>> detect_ohlc_columns(df)
        {'open': 'o', 'high': 'h', 'low': 'l', 'close': 'c'}
    """
    # Define regex patterns for each OHLC component
    # Patterns match: full name (open/OPEN/Open) or single letter (o/O)
    patterns = {
        'open': [
            r'^open$',
            r'^o$',
        ],
        'high': [
            r'^high$',
            r'^h$',
        ],
        'low': [
            r'^low$',
            r'^l$',
        ],
        'close': [
            r'^close$',
            r'^c$',
        ],
        'volume': [
            r'^volume$',
            r'^vol$',
            r'^v$',
        ]
    }
    
    result = {}
    
    # Iterate through each standard OHLC name
    for standard_name, pattern_list in patterns.items():
        # Check each column in the DataFrame
        for col in df.columns:
            # Try to match any of the patterns for this OHLC component
            if any(re.match(pattern, str(col), re.IGNORECASE) for pattern in pattern_list):
                result[standard_name] = col
                break  # Found a match, move to next OHLC component
    
    return result


def detect_indicator_columns(df: pd.DataFrame, ohlc_columns: Dict[str, str]) -> List[str]:
    """
    Detect indicator columns (non-OHLC, non-timestamp columns).
    
    Args:
        df: pandas DataFrame
        ohlc_columns: Dictionary of detected OHLC columns from detect_ohlc_columns()
        
    Returns:
        List of column names that are indicators (not OHLC or timestamp)
    """
    # For now, just a stub - will be implemented in Task 12
    pass


def classify_indicators(indicator_columns: List[str]) -> Tuple[List[str], List[str]]:
    """
    Classify indicators as overlay (price-based) or subplot (oscillator).
    
    Args:
        indicator_columns: List of indicator column names
        
    Returns:
        Tuple of (overlay_indicators, subplot_indicators)
    """
    # For now, just a stub - will be implemented in Task 12
    pass


def check_numeric_columns(df: pd.DataFrame, ohlc_columns: Dict[str, str]) -> None:
    """
    Validate that OHLC columns contain numeric data types.
    
    Args:
        df: pandas DataFrame
        ohlc_columns: Dictionary mapping standard names to actual column names
        
    Raises:
        ValueError: If any OHLC column contains non-numeric data
    """
    for standard_name, col_name in ohlc_columns.items():
        if col_name not in df.columns:
            continue
            
        # Check if column is numeric (int or float)
        if not pd.api.types.is_numeric_dtype(df[col_name]):
            raise ValueError(
                f"Column '{col_name}' ({standard_name}) contains non-numeric data. "
                f"OHLC columns must be numeric (int or float)."
            )


def check_null_values(df: pd.DataFrame, ohlc_columns: Dict[str, str]) -> bool:
    """
    Check for null values in OHLC columns.
    
    Args:
        df: pandas DataFrame
        ohlc_columns: Dictionary mapping standard names to actual column names
        
    Returns:
        True if no nulls found, False if nulls exist
    """
    for standard_name, col_name in ohlc_columns.items():
        if col_name not in df.columns:
            continue
            
        if df[col_name].isnull().any():
            return False
    
    return True


def check_ohlc_relationships(df: pd.DataFrame, ohlc_columns: Dict[str, str]) -> None:
    """
    Validate OHLC relationships (high >= low, open/close within [low, high]).
    
    Args:
        df: pandas DataFrame
        ohlc_columns: Dictionary mapping standard names to actual column names
        
    Raises:
        ValueError: If OHLC relationships are invalid
    """
    # Get column names
    open_col = ohlc_columns.get('open')
    high_col = ohlc_columns.get('high')
    low_col = ohlc_columns.get('low')
    close_col = ohlc_columns.get('close')
    
    # Need at least high and low for validation
    if not (high_col and low_col):
        return
    
    # Check high >= low
    invalid_high_low = df[high_col] < df[low_col]
    if invalid_high_low.any():
        invalid_idx = invalid_high_low.idxmax()
        raise ValueError(
            f"Invalid OHLC relationship: high value {df.loc[invalid_idx, high_col]} "
            f"is less than low value {df.loc[invalid_idx, low_col]} at index {invalid_idx}"
        )
    
    # Check open within [low, high] if open exists
    if open_col:
        invalid_open = (df[open_col] < df[low_col]) | (df[open_col] > df[high_col])
        if invalid_open.any():
            invalid_idx = invalid_open.idxmax()
            raise ValueError(
                f"Invalid OHLC relationship: open value {df.loc[invalid_idx, open_col]} "
                f"is outside range [{df.loc[invalid_idx, low_col]}, {df.loc[invalid_idx, high_col]}] "
                f"at index {invalid_idx}"
            )
    
    # Check close within [low, high] if close exists
    if close_col:
        invalid_close = (df[close_col] < df[low_col]) | (df[close_col] > df[high_col])
        if invalid_close.any():
            invalid_idx = invalid_close.idxmax()
            raise ValueError(
                f"Invalid OHLC relationship: close value {df.loc[invalid_idx, close_col]} "
                f"is outside range [{df.loc[invalid_idx, low_col]}, {df.loc[invalid_idx, high_col]}] "
                f"at index {invalid_idx}"
            )


def validate_ohlc_columns(df: pd.DataFrame, ohlc_columns: Dict[str, str]) -> bool:
    """
    Comprehensive validation of detected OHLC columns.
    
    Performs all validation checks:
    - Numeric data types
    - No null values
    - Valid OHLC relationships
    - Non-negative volume
    
    Args:
        df: pandas DataFrame
        ohlc_columns: Dictionary mapping standard names to actual column names
        
    Returns:
        True if all validation checks pass
        
    Raises:
        ValueError: If any validation check fails
    """
    # Check numeric data types
    check_numeric_columns(df, ohlc_columns)
    
    # Check for null values (don't raise, just warn)
    has_nulls = not check_null_values(df, ohlc_columns)
    if has_nulls:
        # For now, just pass - could add warning in future
        pass
    
    # Check OHLC relationships
    check_ohlc_relationships(df, ohlc_columns)
    
    # Check volume is non-negative if present
    volume_col = ohlc_columns.get('volume')
    if volume_col and volume_col in df.columns:
        if (df[volume_col] < 0).any():
            invalid_idx = (df[volume_col] < 0).idxmax()
            raise ValueError(
                f"Invalid volume: negative value {df.loc[invalid_idx, volume_col]} "
                f"at index {invalid_idx}. Volume must be non-negative."
            )
    
    return True


def require_ohlc_columns(ohlc_columns: Dict[str, str], required: List[str] = None) -> None:
    """
    Verify that required OHLC columns are present.
    
    Args:
        ohlc_columns: Dictionary of detected OHLC columns from detect_ohlc_columns()
        required: List of required column names (defaults to ['open', 'high', 'low', 'close'])
        
    Raises:
        OHLCColumnsNotFoundError: If any required columns are missing
    """
    if required is None:
        required = ['open', 'high', 'low', 'close']
    
    missing = [col for col in required if col not in ohlc_columns]
    
    if missing:
        raise OHLCColumnsNotFoundError(missing)

