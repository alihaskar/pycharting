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

# Import mapper/detector for column standardization
# Note: Import directly from modules to avoid circular dependency through __init__.py
try:
    import src.charting.detector as detector_module
    import src.charting.mapper as mapper_module
    standardize_dataframe = detector_module.standardize_dataframe
    ColumnNotFoundError = mapper_module.ColumnNotFoundError
    ColumnValidationError = mapper_module.ColumnValidationError
    MAPPER_AVAILABLE = True
    logger.info("Mapper/detector modules loaded successfully")
except ImportError as e:
    logger.warning(f"Mapper/detector not available: {e}")
    MAPPER_AVAILABLE = False
    standardize_dataframe = None
    ColumnNotFoundError = ValueError
    ColumnValidationError = TypeError


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


def is_safe_absolute_path(filepath: str) -> bool:
    """
    Check if an absolute path is safe (e.g., in temp directory).
    """
    import tempfile
    temp_dir = tempfile.gettempdir()
    try:
        resolved = str(Path(filepath).resolve())
        return resolved.startswith(temp_dir) and filepath.endswith('.csv')
    except Exception:
        return False


def validate_filename(filename: str, allow_temp: bool = True) -> None:
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
    
    # Check for absolute paths (allow temp directory paths)
    if filename.startswith('/') or (len(filename) > 1 and filename[1] == ':'):
        if allow_temp and is_safe_absolute_path(filename):
            return  # Safe temp path, skip remaining validation
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
    overlays: Optional[List[str]] = None,
    subplots: Optional[List[str]] = None,
    timeframe: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    column_open: Optional[str] = None,
    column_high: Optional[str] = None,
    column_low: Optional[str] = None,
    column_close: Optional[str] = None,
    column_volume: Optional[str] = None
) -> tuple[List[List], Dict[str, Any]]:
    """
    Load CSV file and process data with indicators and resampling.
    
    Args:
        filename: CSV filename to load
        indicators: Optional list of indicator strings for calculation
        overlays: Optional list of overlay indicator column names from CSV
        subplots: Optional list of subplot indicator column names from CSV
        timeframe: Optional timeframe for resampling
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        column_open: Optional custom column name for open prices
        column_high: Optional custom column name for high prices
        column_low: Optional custom column name for low prices
        column_close: Optional custom column name for close prices
        column_volume: Optional custom column name for volume
        
    Returns:
        Tuple of (uplot_data, metadata)
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If data processing fails or filename is invalid
        
    Note:
        Column mapping parameters (column_*) will be integrated with
        mapper/detector modules in future updates.
    """
    # Validate filename for security
    validate_filename(filename)
    
    # Handle absolute paths (temp files) vs relative paths (data dir)
    if filename.startswith('/') or (len(filename) > 1 and filename[1] == ':'):
        # Absolute path - use directly (already validated as safe temp path)
        file_path = Path(filename)
    else:
        # Relative path - look in data directory
        filename = sanitize_filename(filename)
        data_dir = get_data_directory()
        file_path = data_dir / filename
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {filename}")
    
    logger.info(f"Loading file: {file_path}")
    logger.debug(f"MAPPER_AVAILABLE={MAPPER_AVAILABLE}, custom_columns={[column_open, column_high, column_low, column_close, column_volume]}")
    
    # Always load CSV without strict validation first if mapper available (allows for column standardization)
    if MAPPER_AVAILABLE:
        # Load CSV without validation - we'll standardize columns first
        logger.info("Loading CSV with mapper/detector support")
        try:
            df = pd.read_csv(file_path, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding="latin-1")
        
        if df.empty:
            raise ValueError(f"No data found in CSV file: {filename}")
        
        # Parse datetime before standardization
        df = parse_datetime(df)
        
        # Standardize column names (explicit mapping or auto-detection)
        has_custom_columns = any([column_open, column_high, column_low, column_close, column_volume])
        if has_custom_columns:
            logger.info("Using explicit column mapping")
            try:
                df = standardize_dataframe(
                    df,
                    open=column_open,
                    high=column_high,
                    low=column_low,
                    close=column_close,
                    volume=column_volume
                )
                logger.info("Column standardization successful")
            except (ColumnNotFoundError, ColumnValidationError) as e:
                logger.error(f"Column mapping error: {e}")
                raise ValueError(str(e))
        else:
            logger.info("Auto-detecting and standardizing columns")
            try:
                df = standardize_dataframe(df)
                logger.info("Auto-detection successful")
            except (ColumnNotFoundError, ColumnValidationError) as e:
                logger.debug(f"Auto-detection failed, continuing with original columns: {e}")
                # If auto-detection fails, validate that required columns exist
                required_columns = {"timestamp", "open", "high", "low", "close", "volume"}
                missing_columns = required_columns - set(df.columns)
                if missing_columns:
                    raise ValueError(f"Missing required columns: {missing_columns}. Found columns: {list(df.columns)}")
    else:
        # Standard flow with validation (backward compatibility)
        df = load_csv(str(file_path))
        df = parse_datetime(df)
    
    # Clean missing values
    df = clean_missing_values(df)
    
    # Optimize DataFrame
    df = optimize_dataframe(df)
    
    # Detect pre-existing indicator columns in CSV
    available_indicators = detect_indicator_columns(df)
    
    # Filter requested overlays and subplots
    filtered_overlays, filtered_subplots = filter_indicator_data(df, overlays, subplots)
    
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
        "available_indicators": available_indicators,  # Pre-existing indicators from CSV
        "overlays": filtered_overlays,  # Requested overlay indicators
        "subplots": filtered_subplots  # Requested subplot indicators
    }
    
    return uplot_data, metadata

