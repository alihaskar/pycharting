"""
DataFrame column detection and classification utilities.

This module provides functions to automatically detect OHLC columns
and classify technical indicators in pandas DataFrames.
"""

import re
from typing import Dict, List, Tuple
import pandas as pd


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

