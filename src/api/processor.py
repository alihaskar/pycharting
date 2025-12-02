"""Data processing logic for API endpoints."""
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
import os
import re
import logging

from src.ingestion.loader import load_csv, parse_datetime, clean_missing_values, optimize_dataframe
from src.processing.indicators import calculate_indicator
from src.processing.resampler import resample_ohlc
from src.processing.pivot import to_uplot_format

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Raw filename string
        
    Returns:
        Sanitized filename
    """
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[^\w\s\-.]', '', filename)
    return sanitized.strip()


def validate_filename(filename: str) -> None:
    """
    Validate filename for security.
    
    Checks for:
    - Directory traversal attempts
    - Absolute paths
    - Invalid file extensions
    - Hidden files
    - Path separators
    - Null bytes
    - Excessive length
    
    Args:
        filename: Filename to validate
        
    Raises:
        ValueError: If filename is invalid or potentially malicious
    """
    # Check for empty or whitespace-only
    if not filename or not filename.strip():
        raise ValueError("Filename cannot be empty")
    
    # Check length
    if len(filename) > 255:
        raise ValueError("Filename too long")
    
    # Check for null bytes
    if '\x00' in filename:
        raise ValueError("Invalid filename: contains null byte")
    
    # Check for directory traversal
    if '..' in filename:
        raise ValueError("Invalid filename: directory traversal not allowed")
    
    # Check for absolute paths
    if filename.startswith('/') or (len(filename) > 1 and filename[1] == ':'):
        raise ValueError("Invalid filename: absolute paths not allowed")
    
    # Check for path separators (only basename allowed)
    if '/' in filename or '\\' in filename:
        raise ValueError("Invalid filename: subdirectories not allowed")
    
    # Check for hidden files
    if filename.startswith('.'):
        raise ValueError("Invalid filename: hidden files not allowed")
    
    # Check file extension (must be .csv, case insensitive)
    if not filename.lower().endswith('.csv'):
        raise ValueError("Invalid file extension: only .csv files allowed")
    
    # Additional Unicode checks
    # Remove right-to-left override and other problematic Unicode
    if '\u202e' in filename or '\u200e' in filename or '\u200f' in filename:
        raise ValueError("Invalid filename: suspicious Unicode characters")


def get_data_directory() -> Path:
    """
    Get the data directory path.
    
    Returns:
        Path to data directory
    """
    # Check for environment variable first (for testing)
    data_dir = os.getenv("DATA_DIR")
    if data_dir:
        return Path(data_dir)
    
    # Default to data/ directory in project root
    return Path("data")


def detect_indicator_columns(df: pd.DataFrame) -> List[str]:
    """
    Detect indicator columns in DataFrame by excluding standard OHLCV columns.
    
    Identifies columns that are not part of the standard OHLCV dataset
    (timestamp, open, high, low, close, volume). These are assumed to be
    pre-calculated indicators or other data columns.
    
    Args:
        df: pandas DataFrame to analyze
        
    Returns:
        List of indicator column names in original order
        
    Examples:
        >>> df = pd.DataFrame({'timestamp': [...], 'open': [...], 'rsi_14': [...]})
        >>> detect_indicator_columns(df)
        ['rsi_14']
    """
    # Standard OHLCV columns (case-insensitive matching)
    standard_columns = {'timestamp', 'open', 'high', 'low', 'close', 'volume'}
    
    # Get all column names
    all_columns = df.columns.tolist()
    
    # Filter out standard OHLCV columns (case-insensitive)
    indicator_columns = [
        col for col in all_columns
        if col.lower() not in standard_columns
    ]
    
    return indicator_columns


def filter_indicator_data(
    df: pd.DataFrame,
    overlays: Optional[List[str]] = None,
    subplots: Optional[List[str]] = None
) -> tuple[List[str], List[str]]:
    """
    Filter and extract indicator data based on overlay and subplot parameters.
    
    Validates that requested indicator columns exist in the DataFrame and
    returns filtered lists of valid overlay and subplot column names.
    
    Args:
        df: pandas DataFrame containing indicator columns
        overlays: Optional list of overlay indicator column names
        subplots: Optional list of subplot indicator column names
        
    Returns:
        Tuple of (filtered_overlays, filtered_subplots) containing only
        columns that exist in the DataFrame
        
    Examples:
        >>> df = pd.DataFrame({'rsi_14': [...], 'sma_20': [...]})
        >>> filter_indicator_data(df, overlays=['sma_20'], subplots=['rsi_14'])
        (['sma_20'], ['rsi_14'])
    """
    # Get available columns
    available_columns = set(df.columns)
    
    # Filter overlays to only include existing columns
    filtered_overlays = []
    if overlays:
        filtered_overlays = [
            col for col in overlays
            if col in available_columns
        ]
    
    # Filter subplots to only include existing columns
    filtered_subplots = []
    if subplots:
        filtered_subplots = [
            col for col in subplots
            if col in available_columns
        ]
    
    return filtered_overlays, filtered_subplots


def parse_indicator_string(indicator_str: str) -> tuple[str, Dict[str, Any]]:
    """
    Parse indicator string into type and parameters.
    
    Args:
        indicator_str: String like "RSI:14" or "SMA:20"
        
    Returns:
        Tuple of (indicator_type, params_dict)
        
    Example:
        >>> parse_indicator_string("RSI:14")
        ('RSI', {'period': 14})
    """
    parts = indicator_str.split(":")
    indicator_type = parts[0].upper()
    
    params = {}
    if len(parts) > 1:
        try:
            params["period"] = int(parts[1])
        except ValueError:
            logger.warning(f"Invalid period in indicator: {indicator_str}")
    
    return indicator_type, params


def load_and_process_data(
    filename: str,
    indicators: Optional[List[str]] = None,
    timeframe: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> tuple[List[List], Dict[str, Any]]:
    """
    Load CSV file and process data with indicators and resampling.
    
    Args:
        filename: CSV filename to load
        indicators: Optional list of indicator strings
        timeframe: Optional timeframe for resampling
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        
    Returns:
        Tuple of (uplot_data, metadata)
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If data processing fails or filename is invalid
    """
    # Validate filename for security
    validate_filename(filename)
    
    # Sanitize filename
    filename = sanitize_filename(filename)
    
    # Get data directory and construct file path
    data_dir = get_data_directory()
    file_path = data_dir / filename
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {filename}")
    
    logger.info(f"Loading file: {file_path}")
    
    # Load CSV
    df = load_csv(str(file_path))
    
    # Parse datetime (automatically detects timestamp column)
    df = parse_datetime(df)
    
    # Clean missing values
    df = clean_missing_values(df)
    
    # Optimize DataFrame
    df = optimize_dataframe(df)
    
    # Detect pre-existing indicator columns in CSV
    available_indicators = detect_indicator_columns(df)
    
    # Apply time filtering if specified
    if start_date:
        df = df[df.index >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df.index <= pd.to_datetime(end_date)]
    
    # Apply resampling if specified
    if timeframe:
        logger.info(f"Resampling to timeframe: {timeframe}")
        df = resample_ohlc(df, timeframe)
    
    # Calculate indicators if specified
    indicator_names = []
    if indicators:
        for indicator_str in indicators:
            indicator_type, params = parse_indicator_string(indicator_str)
            logger.info(f"Calculating indicator: {indicator_type} with params {params}")
            
            try:
                # Calculate indicator on close prices
                result = calculate_indicator(df["close"], indicator_type, params)
                
                # Add to DataFrame with descriptive name
                period = params.get("period", "")
                col_name = f"{indicator_type.lower()}_{period}" if period else indicator_type.lower()
                df[col_name] = result
                indicator_names.append(col_name)
                
            except Exception as e:
                logger.warning(f"Failed to calculate {indicator_type}: {e}")
                # Continue processing other indicators
    
    # Convert to uPlot format
    uplot_data = to_uplot_format(df, timestamp_unit="ms")
    
    # Create metadata
    metadata = {
        "filename": filename,
        "rows": len(df),
        "columns": len(uplot_data),
        "timeframe": timeframe,
        "indicators": indicator_names,  # Calculated indicators
        "available_indicators": available_indicators  # Pre-existing indicators from CSV
    }
    
    return uplot_data, metadata

