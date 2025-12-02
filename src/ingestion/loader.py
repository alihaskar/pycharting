"""CSV data ingestion module for loading OHLC data."""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union


class CSVLoadError(Exception):
    """Custom exception for CSV loading errors."""
    pass


def load_csv(file_path: Union[str, Path]) -> pd.DataFrame:
    """
    Load OHLC data from a CSV file.
    
    Args:
        file_path: Path to the CSV file (string or Path object)
    
    Returns:
        pandas DataFrame with raw data (no type conversions yet)
    
    Raises:
        CSVLoadError: If file cannot be loaded or is invalid
    """
    # Validate file_path
    if file_path is None:
        raise CSVLoadError("Invalid file path: path cannot be None")
    
    # Convert to Path object
    try:
        path = Path(file_path)
    except (TypeError, ValueError) as e:
        raise CSVLoadError(f"Invalid file path: {e}")
    
    # Check if file exists
    if not path.exists():
        raise CSVLoadError(f"File not found: {file_path}")
    
    # Check if path is a directory
    if path.is_dir():
        raise CSVLoadError(f"Path is a directory, not a file: {file_path}")
    
    # Required columns for OHLC data
    required_columns = {"timestamp", "open", "high", "low", "close", "volume"}
    
    try:
        # Load CSV with encoding detection
        # Try UTF-8 first (most common)
        try:
            df = pd.read_csv(path, encoding="utf-8")
        except UnicodeDecodeError:
            # Fallback to latin-1 if UTF-8 fails
            df = pd.read_csv(path, encoding="latin-1")
        
        # Check if DataFrame is empty
        if df.empty:
            raise CSVLoadError(f"No data found in CSV file: {file_path}")
        
        # Validate required columns exist
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            raise CSVLoadError(
                f"Missing required columns: {missing_columns}. "
                f"Found columns: {list(df.columns)}"
            )
        
        return df
        
    except pd.errors.EmptyDataError:
        raise CSVLoadError(f"No data found in CSV file: {file_path}")
    except pd.errors.ParserError as e:
        raise CSVLoadError(f"Malformed CSV file: {e}")
    except Exception as e:
        # Catch any other pandas exceptions
        if isinstance(e, CSVLoadError):
            raise
        raise CSVLoadError(f"Error loading CSV file: {e}")


def parse_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse timestamp column to datetime type with automatic format detection.
    
    Handles multiple datetime formats:
    - ISO 8601 (YYYY-MM-DD HH:MM:SS, YYYY-MM-DDTHH:MM:SS)
    - Unix timestamps (seconds since epoch)
    - US format (MM/DD/YYYY HH:MM:SS)
    - EU format (DD-MM-YYYY HH:MM:SS)
    - Various other common formats
    
    Args:
        df: DataFrame with 'timestamp' column
    
    Returns:
        DataFrame with timestamp column converted to datetime64 and sorted chronologically
    
    Raises:
        ValueError: If timestamp column is missing or cannot be parsed
    """
    if "timestamp" not in df.columns:
        raise ValueError("Column 'timestamp' not found in DataFrame")
    
    # If already datetime, just return sorted
    if pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df_copy = df.copy()
        df_copy = df_copy.sort_values("timestamp")
        df_copy = df_copy.reset_index(drop=True)
        return df_copy
    
    df_copy = df.copy()
    
    # Try to detect if it's a Unix timestamp (all numeric)
    unix_timestamp_converted = False
    try:
        # Check if all values are numeric (could be Unix timestamps)
        timestamp_sample = df_copy["timestamp"].iloc[0]
        
        # Check if it's numeric (including numpy types)
        is_numeric = False
        if isinstance(timestamp_sample, (int, float, np.integer, np.floating)):
            is_numeric = True
        elif isinstance(timestamp_sample, str):
            try:
                float(timestamp_sample)
                is_numeric = True
            except ValueError:
                pass
        
        if is_numeric:
            # Convert to numeric first
            numeric_timestamps = pd.to_numeric(df_copy["timestamp"], errors="coerce")
            
            # Check if values look like Unix timestamps (reasonable range)
            # Unix timestamps for dates between 2000 and 2100 are roughly 9.5e8 to 4e9
            sample_val = numeric_timestamps.iloc[0]
            
            if 9e8 < sample_val < 4e9:  # Seconds since epoch
                df_copy["timestamp"] = pd.to_datetime(numeric_timestamps, unit="s")
                unix_timestamp_converted = True
            elif 9e11 < sample_val < 4e12:  # Milliseconds since epoch
                df_copy["timestamp"] = pd.to_datetime(numeric_timestamps, unit="ms")
                unix_timestamp_converted = True
            # If values don't match expected ranges, fall through to string parsing
    except (IndexError, KeyError, TypeError):
        pass
    
    # If still not datetime and we didn't convert Unix timestamp, try pandas' automatic parsing
    if not unix_timestamp_converted and not pd.api.types.is_datetime64_any_dtype(df_copy["timestamp"]):
        try:
            # Let pandas infer the format automatically
            df_copy["timestamp"] = pd.to_datetime(
                df_copy["timestamp"],
                errors="coerce"  # Convert unparseable to NaT
            )
            
            # Check for parsing failures
            if df_copy["timestamp"].isna().any():
                # Try with dayfirst=False (US format: MM/DD/YYYY)
                df_copy["timestamp"] = pd.to_datetime(
                    df["timestamp"],
                    format="mixed",
                    dayfirst=False,
                    errors="coerce"
                )
                
                # If still have NaT, try with dayfirst=True (EU format: DD/MM/YYYY)
                if df_copy["timestamp"].isna().any():
                    df_copy["timestamp"] = pd.to_datetime(
                        df["timestamp"],
                        format="mixed",
                        dayfirst=True,
                        errors="coerce"
                    )
        except Exception as e:
            raise ValueError(f"Failed to parse timestamp column: {e}")
    
    # Check if we have any valid timestamps after parsing
    if df_copy["timestamp"].isna().all():
        raise ValueError("Could not parse any timestamps from the timestamp column")
    
    # Sort by timestamp chronologically
    df_copy = df_copy.sort_values("timestamp")
    df_copy = df_copy.reset_index(drop=True)
    
    return df_copy


def clean_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values in OHLC data.
    
    Strategy:
    - Remove rows with missing timestamps (critical data)
    - Forward-fill missing price data (open, high, low, close)
    - Interpolate missing volume data
    - Handle edge cases like consecutive missing values
    
    Args:
        df: DataFrame with potential missing values
    
    Returns:
        DataFrame with missing values handled
    """
    df_copy = df.copy()
    
    # Remove rows with missing timestamps (critical data)
    if "timestamp" in df_copy.columns:
        df_copy = df_copy.dropna(subset=["timestamp"])
        df_copy = df_copy.reset_index(drop=True)
    
    # If DataFrame is empty after removing missing timestamps, return it
    if df_copy.empty:
        return df_copy
    
    # Price columns to forward-fill
    price_columns = ["open", "high", "low", "close"]
    
    # Forward-fill missing price values (use previous valid value)
    for col in price_columns:
        if col in df_copy.columns:
            # Forward fill (use previous value)
            df_copy[col] = df_copy[col].ffill()
            
            # If there are still NaN values at the beginning (no previous value to fill from),
            # use backward fill
            df_copy[col] = df_copy[col].bfill()
    
    # Interpolate missing volume values (linear interpolation)
    if "volume" in df_copy.columns:
        # First try linear interpolation
        df_copy["volume"] = df_copy["volume"].interpolate(method="linear")
        
        # If there are still NaN values (e.g., all values are NaN or edges),
        # fill with 0 or forward/backward fill
        if df_copy["volume"].isna().any():
            # Try forward fill first
            df_copy["volume"] = df_copy["volume"].ffill()
            # Then backward fill
            df_copy["volume"] = df_copy["volume"].bfill()
            # If still have NaN (all were NaN), fill with 0
            df_copy["volume"] = df_copy["volume"].fillna(0)
    
    return df_copy


def optimize_dataframe(df: pd.DataFrame, source: str = None) -> pd.DataFrame:
    """
    Optimize DataFrame for time-series operations.
    
    Optimizations:
    - Set timestamp as datetime index for efficient time-based operations
    - Sort by timestamp (chronological order)
    - Optimize memory usage with appropriate data types
    - Validate required columns
    - Add metadata attributes
    
    Args:
        df: DataFrame with timestamp column
        source: Optional source identifier for metadata
    
    Returns:
        Optimized DataFrame with datetime index
    
    Raises:
        ValueError: If required columns are missing
    """
    # Required columns for OHLC data
    required_columns = ["timestamp", "open", "high", "low", "close", "volume"]
    
    # Validate required columns
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}. "
            f"Found columns: {list(df.columns)}"
        )
    
    df_copy = df.copy()
    
    # Set timestamp as index
    if "timestamp" in df_copy.columns:
        df_copy = df_copy.set_index("timestamp")
    
    # Sort by timestamp (chronological order)
    df_copy = df_copy.sort_index()
    
    # Optimize memory usage
    # Convert price columns to float32 (sufficient precision for most use cases)
    price_columns = ["open", "high", "low", "close"]
    for col in price_columns:
        if col in df_copy.columns:
            df_copy[col] = df_copy[col].astype(np.float32)
    
    # Convert volume to int32 if all values are integers, otherwise float32
    if "volume" in df_copy.columns:
        # Check if all values are integers (within floating point precision)
        if (df_copy["volume"] % 1 == 0).all():
            # Convert to int32 for memory efficiency
            df_copy["volume"] = df_copy["volume"].astype(np.int32)
        else:
            # Keep as float32 for fractional volumes
            df_copy["volume"] = df_copy["volume"].astype(np.float32)
    
    # Add metadata attributes
    from datetime import datetime
    df_copy.attrs = {
        "source": source,
        "processed_at": datetime.now().isoformat(),
        "optimized": True
    }
    
    return df_copy

