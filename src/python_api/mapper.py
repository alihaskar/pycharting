"""
Column Mapping Utilities

Provides functions to map arbitrary DataFrame column names to standardized
OHLC format. Supports explicit mapping and auto-detection with comprehensive
validation.

Functions:
    map_columns: Map DataFrame columns to standard OHLC format
    detect_columns: Auto-detect OHLC columns using pattern matching
    validate_column_mapping: Validate a column mapping configuration
    suggest_columns: Suggest similar column names for missing columns

Exceptions:
    ColumnNotFoundError: Raised when specified column doesn't exist
    ColumnValidationError: Raised when column validation fails
"""

import pandas as pd
from typing import Optional, Dict, List
from difflib import SequenceMatcher


# Custom Exceptions
class ColumnNotFoundError(ValueError):
    """Raised when a specified column is not found in the DataFrame"""
    pass


class ColumnValidationError(TypeError):
    """Raised when a column fails validation (e.g., not numeric)"""
    pass


def map_columns(
    df: pd.DataFrame,
    open: Optional[str] = None,
    high: Optional[str] = None,
    low: Optional[str] = None,
    close: Optional[str] = None,
    volume: Optional[str] = None
) -> pd.DataFrame:
    """
    Map arbitrary DataFrame columns to standardized OHLC format.
    
    Creates a copy of the DataFrame with columns renamed to lowercase standard
    names: 'open', 'high', 'low', 'close', 'volume'. Volume is optional.
    
    Args:
        df: Input DataFrame with OHLC data
        open: Name of the open price column (default: auto-detect 'open')
        high: Name of the high price column (default: auto-detect 'high')
        low: Name of the low price column (default: auto-detect 'low')
        close: Name of the close price column (default: auto-detect 'close')
        volume: Name of the volume column (optional, default: auto-detect 'volume')
    
    Returns:
        DataFrame with standardized column names and preserved data
    
    Raises:
        ValueError: If required columns are missing or duplicate mappings exist
        TypeError: If specified columns are not numeric
    
    Examples:
        >>> df = pd.DataFrame({'Open': [100], 'High': [105], 'Low': [99], 'Close': [103]})
        >>> result = map_columns(df, open='Open', high='High', low='Low', close='Close')
        >>> list(result.columns)
        ['open', 'high', 'low', 'close']
    """
    # Make a copy to avoid modifying original
    result = df.copy()
    
    # Auto-detect standard lowercase names if not specified
    if open is None and 'open' in result.columns:
        open = 'open'
    if high is None and 'high' in result.columns:
        high = 'high'
    if low is None and 'low' in result.columns:
        low = 'low'
    if close is None and 'close' in result.columns:
        close = 'close'
    if volume is None and 'volume' in result.columns:
        volume = 'volume'
    
    # Check for duplicate SOURCE columns before building mapping
    source_columns = [col for col in [open, high, low, close, volume] if col is not None]
    if len(source_columns) != len(set(source_columns)):
        # Find the duplicate
        seen = set()
        for col in source_columns:
            if col in seen:
                raise ValueError(
                    f"Duplicate column mapping detected: '{col}' is mapped to multiple fields"
                )
            seen.add(col)
    
    # Build mapping dictionary
    mapping = {}
    if open is not None:
        mapping[open] = 'open'
    if high is not None:
        mapping[high] = 'high'
    if low is not None:
        mapping[low] = 'low'
    if close is not None:
        mapping[close] = 'close'
    if volume is not None:
        mapping[volume] = 'volume'
    
    # Validate required columns are present
    required = ['open', 'high', 'low', 'close']
    for field in required:
        if field not in mapping.values():
            # Suggest similar columns
            available_cols = result.columns.tolist()
            suggestions = suggest_columns(field, available_cols)
            
            error_msg = f"Missing required column: '{field}'.\n"
            if suggestions:
                error_msg += f"Did you mean: {', '.join(suggestions)}?\n"
            error_msg += f"Available columns: {available_cols}\n"
            error_msg += f"Please specify the column name using the '{field}=' parameter."
            raise ValueError(error_msg)
    
    # Validate specified columns exist in DataFrame
    for source_col in mapping.keys():
        if source_col not in result.columns:
            available_cols = result.columns.tolist()
            suggestions = suggest_columns(source_col, available_cols)
            
            error_msg = f"Column '{source_col}' not found in DataFrame."
            if suggestions:
                error_msg += f"\nDid you mean: {', '.join(suggestions)}?"
            error_msg += f"\nAvailable columns: {available_cols}"
            raise ColumnNotFoundError(error_msg)
    
    # Validate numeric types for OHLC columns
    for source_col, target_name in mapping.items():
        if target_name != 'volume':  # Volume will be checked separately if present
            if not pd.api.types.is_numeric_dtype(result[source_col]):
                raise ColumnValidationError(
                    f"Column '{source_col}' must be numeric (for {target_name}), "
                    f"but got dtype: {result[source_col].dtype}"
                )
    
    # Validate volume column if present
    if 'volume' in mapping.values():
        volume_col = [k for k, v in mapping.items() if v == 'volume'][0]
        if not pd.api.types.is_numeric_dtype(result[volume_col]):
            raise ColumnValidationError(
                f"Column '{volume_col}' must be numeric (for volume), "
                f"but got dtype: {result[volume_col].dtype}"
            )
    
    # Rename columns according to mapping
    result = result.rename(columns=mapping)
    
    return result


def detect_columns(df: pd.DataFrame) -> Dict[str, str]:
    """
    Auto-detect OHLC columns using case-insensitive matching and common patterns.
    
    Tries to identify OHLC columns using:
    1. Exact case-insensitive matches (open, Open, OPEN)
    2. Common abbreviations (o, h, l, c, vol)
    3. Numbered patterns (open_1, high_2, etc.)
    
    Args:
        df: Input DataFrame to analyze
    
    Returns:
        Dictionary mapping detected column names to standard names
        Example: {'Open': 'open', 'High': 'high', ...}
    
    Raises:
        ValueError: If required OHLC columns cannot be detected
    
    Examples:
        >>> df = pd.DataFrame({'Open': [100], 'High': [105], 'Low': [99], 'Close': [103]})
        >>> detect_columns(df)
        {'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close'}
    """
    detected = {}
    columns = df.columns.tolist()
    
    # Define patterns for each OHLC field (in priority order)
    patterns = {
        'open': ['open', 'o'],
        'high': ['high', 'h'],
        'low': ['low', 'l'],
        'close': ['close', 'c'],
        'volume': ['volume', 'vol', 'v']
    }
    
    # Try to detect each field
    for field, pattern_list in patterns.items():
        found = None
        
        # Try each pattern in priority order
        for pattern in pattern_list:
            # Case-insensitive match
            for col in columns:
                if col.lower() == pattern:
                    # Prefer lowercase exact match if available
                    if col == pattern:
                        found = col
                        break
                    # Otherwise use first match found
                    if found is None:
                        found = col
            
            if found is not None:
                break
        
        # Record detection
        if found is not None:
            detected[found] = field
    
    # Validate required columns were detected
    required = ['open', 'high', 'low', 'close']
    detected_fields = set(detected.values())
    missing = [field for field in required if field not in detected_fields]
    
    if missing:
        # Suggest similar columns for each missing field
        suggestions_text = []
        for field in missing:
            suggestions = suggest_columns(field, columns)
            if suggestions:
                suggestions_text.append(f"  - {field}: Did you mean {', '.join(suggestions)}?")
        
        error_msg = f"Could not detect required column(s): {', '.join(missing)}.\n"
        if suggestions_text:
            error_msg += "Suggestions:\n" + "\n".join(suggestions_text) + "\n"
        error_msg += f"Available columns: {columns}\n"
        error_msg += "Please specify column names explicitly using map_columns()."
        
        raise ValueError(error_msg)
    
    return detected


def suggest_columns(missing: str, available: List[str], max_suggestions: int = 3) -> List[str]:
    """
    Suggest similar column names using fuzzy string matching.
    
    Uses SequenceMatcher to find columns similar to the missing column name.
    Prioritizes case-insensitive exact matches, then similarity score.
    
    Args:
        missing: The column name that was not found
        available: List of available column names in the DataFrame
        max_suggestions: Maximum number of suggestions to return
    
    Returns:
        List of suggested column names, ordered by similarity
    
    Examples:
        >>> suggest_columns('open', ['opening', 'Open', 'opener'])
        ['Open', 'opening', 'opener']
    """
    suggestions = []
    
    # First, check for case-insensitive exact match
    for col in available:
        if col.lower() == missing.lower():
            suggestions.append(col)
    
    # If exact match found, return it
    if suggestions:
        return suggestions[:max_suggestions]
    
    # Calculate similarity scores for all columns
    similarities = []
    for col in available:
        # Calculate similarity ratio
        ratio = SequenceMatcher(None, missing.lower(), col.lower()).ratio()
        if ratio > 0.5:  # Only suggest if reasonably similar
            similarities.append((col, ratio))
    
    # Sort by similarity (highest first)
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Return top N suggestions
    suggestions = [col for col, _ in similarities[:max_suggestions]]
    return suggestions


def validate_column_mapping(df: pd.DataFrame, mapping: Dict[str, str]) -> tuple[bool, List[str]]:
    """
    Validate a column mapping configuration.
    
    Checks that:
    - All source columns exist in DataFrame
    - All source columns are numeric
    - All required OHLC fields are present
    - No duplicate mappings
    
    Args:
        df: Input DataFrame
        mapping: Dictionary mapping source column names to standard names
    
    Returns:
        Tuple of (is_valid, error_messages)
    
    Examples:
        >>> df = pd.DataFrame({'Open': [100], 'High': [105], 'Low': [99], 'Close': [103]})
        >>> mapping = {'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close'}
        >>> validate_column_mapping(df, mapping)
        (True, [])
    """
    # TODO: Implement in subtask 1.3
    raise NotImplementedError("validate_column_mapping() will be implemented in subtask 1.3")

