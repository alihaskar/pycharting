"""
DataFrame to CSV transformation utilities.

This module provides functions to convert DataFrames to temporary CSV files
with standardized column names for backend processing.
"""

import os
import tempfile
import time
import random
from typing import Dict, List, Optional
import pandas as pd


def standardize_column_names(df: pd.DataFrame, ohlc_mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Standardize OHLC column names while preserving indicator columns.
    
    Creates a copy of the DataFrame and renames OHLC columns from their
    detected names to standard names (open, high, low, close, volume).
    Indicator columns maintain their original names.
    
    Args:
        df: pandas DataFrame with OHLC and indicator data
        ohlc_mapping: Dictionary mapping standard names to detected column names
                     e.g., {'open': 'Open', 'high': 'High', ...}
        
    Returns:
        New DataFrame with standardized OHLC column names
        
    Examples:
        >>> df = pd.DataFrame({'Open': [100], 'High': [101], 'rsi_14': [45]})
        >>> mapping = {'open': 'Open', 'high': 'High'}
        >>> result = standardize_column_names(df, mapping)
        >>> list(result.columns)
        ['open', 'high', 'rsi_14']
    """
    # Create a deep copy to avoid modifying the original DataFrame
    df_copy = df.copy()
    
    # Create reverse mapping: detected name -> standard name
    rename_map = {detected_name: standard_name 
                  for standard_name, detected_name in ohlc_mapping.items()}
    
    # Apply column renaming
    df_copy.rename(columns=rename_map, inplace=True)
    
    return df_copy


def prepare_dataframe_for_csv(
    df: pd.DataFrame,
    ohlc_mapping: Dict[str, str],
    indicator_columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Prepare DataFrame for CSV export by standardizing column names.
    
    Args:
        df: pandas DataFrame
        ohlc_mapping: Dictionary mapping standard names to detected column names
        indicator_columns: Optional list of indicator column names
        
    Returns:
        Prepared DataFrame ready for CSV export
    """
    # Standardize OHLC column names
    df_prepared = standardize_column_names(df, ohlc_mapping)
    
    return df_prepared


def handle_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert datetime index to timestamp column for CSV compatibility.
    
    Resets the DataFrame index to convert a datetime index into a regular
    timestamp column. Handles timezone-aware timestamps and preserves
    datetime precision.
    
    Args:
        df: pandas DataFrame with datetime index
        
    Returns:
        DataFrame with datetime index converted to timestamp column
        
    Examples:
        >>> dates = pd.date_range('2024-01-01', periods=3, freq='1min')
        >>> df = pd.DataFrame({'open': [100, 101, 102]}, index=dates)
        >>> result = handle_datetime_index(df)
        >>> 'timestamp' in result.columns
        True
    """
    # Create a copy to avoid modifying original
    df_copy = df.copy()
    
    # Check if index is datetime-like
    if isinstance(df_copy.index, pd.DatetimeIndex):
        # Reset index to create timestamp column
        df_copy.reset_index(inplace=True)
        
        # Rename index column to 'timestamp' if it has a different name
        if df_copy.columns[0] != 'timestamp':
            # Check if 'timestamp' already exists
            if 'timestamp' not in df_copy.columns:
                df_copy.rename(columns={df_copy.columns[0]: 'timestamp'}, inplace=True)
    else:
        # If not a datetime index, just reset it
        # This handles regular integer indices
        df_copy.reset_index(drop=True, inplace=True)
    
    return df_copy


def generate_temp_filepath(prefix: str = "chart_data") -> str:
    """
    Generate a unique temporary file path with timestamp-based naming.
    
    Creates a filepath in the system's temporary directory with a unique
    timestamp-based filename to prevent collisions.
    
    Args:
        prefix: Filename prefix (default: "chart_data")
        
    Returns:
        Full path to temporary file location
        
    Examples:
        >>> filepath = generate_temp_filepath()
        >>> filepath.endswith('.csv')
        True
        >>> 'chart_data_' in filepath
        True
    """
    # Get system temp directory
    temp_dir = tempfile.gettempdir()
    
    # Generate unique filename using timestamp and random component
    timestamp = int(time.time() * 1000000)  # Microsecond precision
    random_suffix = random.randint(1000, 9999)  # Add random component for uniqueness
    filename = f"{prefix}_{timestamp}_{random_suffix}.csv"
    
    # Construct full file path
    filepath = os.path.join(temp_dir, filename)
    
    return filepath


def create_temp_csv(df: pd.DataFrame, filepath: Optional[str] = None) -> str:
    """
    Create a temporary CSV file from DataFrame.
    
    Writes the DataFrame to a CSV file in the system temp directory
    with proper formatting for backend consumption.
    
    Args:
        df: pandas DataFrame to write
        filepath: Optional custom filepath (generates one if not provided)
        
    Returns:
        Path to the created CSV file
        
    Examples:
        >>> df = pd.DataFrame({'open': [100], 'close': [101]})
        >>> filepath = create_temp_csv(df)
        >>> os.path.exists(filepath)
        True
    """
    # Generate filepath if not provided
    if filepath is None:
        filepath = generate_temp_filepath()
    
    # Write DataFrame to CSV
    # index=False to avoid writing pandas index column
    df.to_csv(filepath, index=False)
    
    return filepath


def transform_dataframe_to_csv(
    df: pd.DataFrame,
    ohlc_mapping: Dict[str, str],
    indicator_columns: Optional[List[str]] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Transform DataFrame to CSV file with standardized column names.
    
    Performs complete transformation pipeline:
    1. Standardizes OHLC column names
    2. Converts datetime index to timestamp column
    3. Writes to temporary CSV file
    
    Args:
        df: pandas DataFrame with OHLC and indicator data
        ohlc_mapping: Dictionary mapping standard names to detected column names
        indicator_columns: Optional list of indicator column names
        output_path: Optional custom output path (defaults to temp directory)
        
    Returns:
        Path to the generated CSV file
        
    Examples:
        >>> dates = pd.date_range('2024-01-01', periods=3, freq='1min')
        >>> df = pd.DataFrame({'Open': [100, 101, 102]}, index=dates)
        >>> mapping = {'open': 'Open'}
        >>> filepath = transform_dataframe_to_csv(df, mapping)
        >>> os.path.exists(filepath)
        True
    """
    # Step 1: Standardize OHLC column names
    df_transformed = standardize_column_names(df, ohlc_mapping)
    
    # Step 2: Handle datetime index (convert to timestamp column)
    df_transformed = handle_datetime_index(df_transformed)
    
    # Step 3: Create CSV file
    filepath = create_temp_csv(df_transformed, filepath=output_path)
    
    return filepath

