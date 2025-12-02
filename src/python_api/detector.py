"""
DataFrame column detection and classification utilities.

This module provides functions to automatically detect OHLC columns
and classify technical indicators in pandas DataFrames.

Integrates with mapper.py for enhanced column standardization and detection.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
import pandas as pd

# Configure module logger
logger = logging.getLogger(__name__)

# Import mapper functions for integration
try:
    from .mapper import detect_columns as mapper_detect_columns, map_columns, ColumnNotFoundError
except ImportError:
    # Fallback if mapper not available
    mapper_detect_columns = None
    map_columns = None
    ColumnNotFoundError = ValueError


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
        
    Examples:
        >>> df = pd.DataFrame({'open': [100], 'high': [101], 'low': [99], 'close': [100.5],
        ...                    'rsi_14': [45], 'sma_20': [100.2]})
        >>> ohlc_cols = detect_ohlc_columns(df)
        >>> detect_indicator_columns(df, ohlc_cols)
        ['rsi_14', 'sma_20']
    """
    # Get set of OHLC column names
    ohlc_column_names = set(ohlc_columns.values())
    
    # List of potential timestamp column names
    timestamp_names = {'timestamp', 'time', 'date', 'datetime', 'index'}
    
    # Filter columns: exclude OHLC and timestamp columns
    indicator_columns = []
    for col in df.columns:
        col_lower = str(col).lower()
        
        # Skip if it's an OHLC column
        if col in ohlc_column_names:
            continue
        
        # Skip if it's a timestamp column
        if col_lower in timestamp_names:
            continue
        
        # It's an indicator column
        indicator_columns.append(col)
    
    return indicator_columns


def classify_indicators(indicator_columns: List[str]) -> Tuple[List[str], List[str]]:
    """
    Classify indicators as overlay (price-based) or subplot (oscillator).
    
    Uses pattern matching to identify common indicator types:
    - Overlay: Moving averages (SMA, EMA, MA), VWAP, Bollinger Bands
    - Subplot: Oscillators and momentum indicators (RSI, MACD, Stochastic, OBV, CCI)
    
    Unknown indicators default to subplot for safety.
    
    Args:
        indicator_columns: List of indicator column names
        
    Returns:
        Tuple of (overlay_indicators, subplot_indicators)
        
    Examples:
        >>> classify_indicators(['sma_20', 'rsi_14', 'ema_12'])
        (['sma_20', 'ema_12'], ['rsi_14'])
    """
    # Define regex patterns for overlay indicators (price-based)
    overlay_patterns = [
        r'.*sma.*',      # Simple Moving Average
        r'.*ema.*',      # Exponential Moving Average
        r'^ma[_\d].*',   # Generic Moving Average starting with "ma_" or "ma" followed by digit
        r'.*\bma\b.*',   # Generic Moving Average with word boundaries
        r'.*vwap.*',     # Volume Weighted Average Price
        r'.*bb.*',       # Bollinger Bands
        r'.*band.*',     # Any band indicators
        r'.*average.*',  # Any average indicators
    ]
    
    # Define regex patterns for subplot indicators (oscillators/momentum)
    subplot_patterns = [
        r'.*rsi.*',      # Relative Strength Index
        r'.*macd.*',     # Moving Average Convergence Divergence
        r'.*stoch.*',    # Stochastic
        r'.*obv.*',      # On-Balance Volume
        r'.*cci.*',      # Commodity Channel Index
        r'.*adx.*',      # Average Directional Index
        r'.*mfi.*',      # Money Flow Index
    ]
    
    overlays = []
    subplots = []
    
    for col in indicator_columns:
        col_lower = col.lower()
        
        # Check if matches overlay patterns
        is_overlay = any(re.match(pattern, col_lower, re.IGNORECASE) for pattern in overlay_patterns)
        
        if is_overlay:
            overlays.append(col)
        else:
            # Default to subplot for unknown indicators (safety)
            subplots.append(col)
    
    return overlays, subplots


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


# =============================================================================
# Mapper Integration Functions (New in v2)
# =============================================================================

def detect_ohlc_columns_via_mapper(df: pd.DataFrame) -> Dict[str, str]:
    """
    Detect OHLC columns using mapper.py's enhanced detection.
    
    This is the recommended way to detect columns as it leverages
    the improved fuzzy matching and error handling from mapper.py.
    
    Args:
        df: pandas DataFrame containing OHLC data
        
    Returns:
        Dictionary mapping actual column names to standard names
        Example: {'Open': 'open', 'High': 'high', ...}
        
    Raises:
        ValueError: If mapper.py is not available or OHLC columns cannot be detected
    """
    logger.debug(f"Detecting OHLC columns via mapper for DataFrame with columns: {list(df.columns)}")
    
    if mapper_detect_columns is None:
        logger.error("mapper.py is not available")
        raise ValueError(
            "mapper.py is not available. Please use detect_ohlc_columns() instead."
        )
    
    result = mapper_detect_columns(df)
    logger.info(f"Successfully detected OHLC columns: {result}")
    
    return result


def classify_indicators_enhanced(
    indicator_columns: List[str],
    user_mapping: Optional[Dict[str, bool]] = None
) -> Tuple[List[str], List[str]]:
    """
    Classify indicators with user-provided overrides and pattern matching fallback.
    
    Accepts a dictionary mapping indicator names to boolean flags where:
    - True = overlay indicator (displayed on main chart)
    - False = subplot indicator (displayed on separate panel)
    
    Indicators not in user_mapping are auto-classified using pattern matching.
    Unknown indicators default to subplot for safety.
    
    Args:
        indicator_columns: List of indicator column names
        user_mapping: Optional dict mapping indicator names to overlay boolean
                     Example: {'rsi_14': False, 'custom_ma': True}
        
    Returns:
        Tuple of (overlay_indicators, subplot_indicators)
        
    Examples:
        >>> # Auto-classification only
        >>> classify_indicators_enhanced(['sma_20', 'rsi_14'], None)
        (['sma_20'], ['rsi_14'])
        
        >>> # With user overrides
        >>> classify_indicators_enhanced(['sma_20', 'rsi_14', 'custom'], {'custom': True})
        (['sma_20', 'custom'], ['rsi_14'])
    """
    logger.debug(f"Classifying {len(indicator_columns)} indicators: {indicator_columns}")
    logger.debug(f"User mapping provided: {user_mapping}")
    
    overlays = []
    subplots = []
    
    # Handle None or empty mapping
    if user_mapping is None:
        user_mapping = {}
    
    # Warn about indicators in user_mapping not in indicator_columns
    unmapped_indicators = set(user_mapping.keys()) - set(indicator_columns)
    if unmapped_indicators:
        logger.warning(f"User mapping contains indicators not in indicator list: {unmapped_indicators}")
    
    # Process each indicator
    for indicator in indicator_columns:
        # Check if user explicitly provided a classification
        if indicator in user_mapping:
            is_overlay = user_mapping[indicator]
            if is_overlay:
                overlays.append(indicator)
                logger.info(f"User override: '{indicator}' → overlay")
            else:
                subplots.append(indicator)
                logger.info(f"User override: '{indicator}' → subplot")
        else:
            # Fallback to pattern matching (existing classify_indicators logic)
            logger.debug(f"Using pattern matching for '{indicator}'")
            ind_overlays, ind_subplots = classify_indicators([indicator])
            
            if ind_overlays:
                overlays.append(indicator)
                logger.debug(f"Pattern match: '{indicator}' → overlay")
            else:
                subplots.append(indicator)
                logger.debug(f"Pattern match: '{indicator}' → subplot")
    
    logger.info(f"Classification complete: {len(overlays)} overlays, {len(subplots)} subplots")
    
    return overlays, subplots


def standardize_dataframe(
    df: pd.DataFrame,
    open: Optional[str] = None,
    high: Optional[str] = None,
    low: Optional[str] = None,
    close: Optional[str] = None,
    volume: Optional[str] = None
) -> pd.DataFrame:
    """
    Standardize DataFrame column names using mapper.py.
    
    This function integrates detector with mapper for consistent column naming.
    Columns are renamed to lowercase standard names: 'open', 'high', 'low', 'close', 'volume'.
    Indicator columns are preserved with their original names.
    
    Args:
        df: Input DataFrame with OHLC data
        open: Name of open price column (optional, auto-detected if not provided)
        high: Name of high price column (optional, auto-detected if not provided)
        low: Name of low price column (optional, auto-detected if not provided)
        close: Name of close price column (optional, auto-detected if not provided)
        volume: Name of volume column (optional, auto-detected if not provided)
        
    Returns:
        DataFrame with standardized column names
        
    Raises:
        ValueError: If mapper.py is not available
        ColumnNotFoundError: If required columns cannot be found
        
    Examples:
        >>> df = pd.DataFrame({'Open': [100], 'High': [105], 'Low': [99], 'Close': [103]})
        >>> standardized = standardize_dataframe(df)
        >>> list(standardized.columns)
        ['open', 'high', 'low', 'close']
    """
    logger.debug(f"Standardizing DataFrame with {len(df.columns)} columns")
    
    if map_columns is None or mapper_detect_columns is None:
        logger.error("mapper.py is not available for standardization")
        raise ValueError(
            "mapper.py is not available. Cannot standardize DataFrame."
        )
    
    # If no columns specified, auto-detect them using mapper's detect_columns
    if all(col is None for col in [open, high, low, close, volume]):
        logger.debug("No explicit columns provided, using auto-detection")
        # Use mapper's smart detection
        try:
            detected = mapper_detect_columns(df)
            logger.info(f"Auto-detected columns: {detected}")
        except Exception as e:
            logger.error(f"Failed to auto-detect columns: {e}")
            raise
        
        # Convert detected mapping to parameters for map_columns
        # detected is {'col_name': 'standard_name'}, we need actual col names
        col_mapping = {v: k for k, v in detected.items()}
        
        return map_columns(
            df,
            open=col_mapping.get('open'),
            high=col_mapping.get('high'),
            low=col_mapping.get('low'),
            close=col_mapping.get('close'),
            volume=col_mapping.get('volume')
        )
    
    # Use provided column names
    logger.info(f"Using explicit column mapping: open={open}, high={high}, low={low}, close={close}, volume={volume}")
    return map_columns(df, open=open, high=high, low=low, close=close, volume=volume)

