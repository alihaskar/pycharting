"""CSV data ingestion module for loading OHLC data."""
import pandas as pd
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

