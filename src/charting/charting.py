"""
Main Charting class for Python API.

Provides a simple interface for displaying Pandas DataFrames as
interactive charts in the browser with automatic OHLC and indicator detection.
"""

import os
import logging
from typing import Optional, List, Dict, Union
import pandas as pd

from .detector import (
    detect_ohlc_columns,
    detect_indicator_columns,
    classify_indicators
)
from .transformer import transform_dataframe_to_csv
from .server import ServerManager
from .browser import launch_browser

logger = logging.getLogger(__name__)


class Charting:
    """
    Main Charting class for displaying DataFrames as interactive charts.
    
    Examples:
        >>> chart = Charting()
        >>> chart.load(df)  # Auto-detects OHLC and indicators
        >>> chart.close()
        
        >>> chart = Charting(height=800, auto_open=False)
        >>> url = chart.load(df, overlays=['sma_20'], subplots=['rsi_14'])
        >>> print(url)
    """
    
    def __init__(
        self,
        height: int = 600,
        port: Optional[int] = None,
        auto_open: bool = True
    ):
        """
        Initialize Charting instance.
        
        Task 27.1: Class initialization and configuration
        
        Args:
            height: Chart height in pixels (default: 600)
            port: Server port, or None for auto-detection (default: None)
            auto_open: Automatically open browser (default: True)
            
        Raises:
            TypeError: If parameters are wrong type
            ValueError: If parameters are out of valid range
        """
        # Task 27.3: Parameter validation
        self._validate_init_params(height, port, auto_open)
        
        # Task 27.1: Store configuration
        self.height = height
        self.port = port
        self.auto_open = auto_open
        
        # Task 27.2: Initialize state management
        self.server_manager = None
        self.temp_files = []
        
        logger.info(f"Charting initialized: height={height}, port={port}, auto_open={auto_open}")
    
    def _validate_init_params(
        self,
        height: int,
        port: Optional[int],
        auto_open: bool
    ) -> None:
        """
        Validate initialization parameters.
        
        Task 27.3: Parameter validation and error handling
        
        Raises:
            TypeError: If parameters are wrong type
            ValueError: If parameters are out of valid range
        """
        # Validate height
        if not isinstance(height, int):
            raise TypeError("Height must be an integer")
        if height <= 0:
            raise ValueError("Height must be a positive integer")
        
        # Validate port
        if port is not None:
            if not isinstance(port, int):
                raise TypeError("Port must be an integer or None")
            if port < 1024 or port > 65535:
                raise ValueError("Port must be between 1024 and 65535")
        
        # Validate auto_open
        if not isinstance(auto_open, bool):
            raise TypeError("auto_open must be a boolean")
    
    def load(
        self,
        df: Union[pd.DataFrame, str],
        overlays: Optional[List[str]] = None,
        subplots: Optional[List[str]] = None,
        # Task 7.1: Explicit column mapping parameters
        open: Optional[str] = None,
        high: Optional[str] = None,
        low: Optional[str] = None,
        close: Optional[str] = None,
        volume: Optional[str] = None,
        # Task 7.1: Indicator classification dict
        indicators: Optional[Dict[str, bool]] = None
    ) -> str:
        """
        Load DataFrame and display as interactive chart.
        
        Task 28: DataFrame loading with auto-detection
        Task 7.1: Enhanced with explicit column mappings and indicator dict
        
        Args:
            df: Pandas DataFrame with OHLC data and optional indicators, OR path to CSV file
            overlays: List of overlay indicator column names (optional)
            subplots: List of subplot indicator column names (optional)
            open: Explicit column name for open prices (optional)
            high: Explicit column name for high prices (optional)
            low: Explicit column name for low prices (optional)
            close: Explicit column name for close prices (optional)
            volume: Explicit column name for volume (optional)
            indicators: Dict mapping indicator names to True (overlay) or False (subplot)
            
        Returns:
            URL of the chart
            
        Raises:
            ValueError: If DataFrame is invalid
            RuntimeError: If chart startup fails
            
        Examples:
            # Auto-detection (backward compatible)
            chart.load(df)
            
            # Load from CSV file
            chart.load("data.csv")
            
            # Explicit column mapping
            chart.load(df, open='PriceOpen', high='PriceHigh', ...)
            
            # Indicator classification
            chart.load(df, indicators={'sma_20': True, 'rsi_14': False})
        """
        logger.info("Loading DataFrame...")
        
        # Handle CSV file path
        if isinstance(df, str):
            logger.info(f"Reading CSV file: {df}")
            if not os.path.exists(df):
                raise FileNotFoundError(f"File not found: {df}")
            
            try:
                # Try to read with pandas
                # We assume 'timestamp' or similar is the index, or first column is date
                # We'll try to parse dates automatically
                df_obj = pd.read_csv(df, parse_dates=True)
                
                # Check if index is datetime, if not try to find a date column
                if not isinstance(df_obj.index, pd.DatetimeIndex):
                    # Look for common date column names
                    date_cols = [c for c in df_obj.columns if 'date' in c.lower() or 'time' in c.lower()]
                    if date_cols:
                        col = date_cols[0]
                        df_obj[col] = pd.to_datetime(df_obj[col])
                        df_obj.set_index(col, inplace=True)
                        logger.info(f"Set index to '{col}' column")
                    else:
                        # Fallback: try to parse first column as index if it looks like date
                        try:
                            df_obj.index = pd.to_datetime(df_obj.iloc[:, 0])
                            df_obj = df_obj.iloc[:, 1:] # Remove first column if it became index
                            logger.info("Parsed first column as datetime index")
                        except:
                            pass # Will be caught by _validate_dataframe
                            
                df = df_obj
                
            except Exception as e:
                raise ValueError(f"Failed to read CSV file '{df}': {e}")
        
        # Check if DataFrame has DatetimeIndex. If not, try to set it.
        if not isinstance(df.index, pd.DatetimeIndex):
             # Look for common date column names
            date_cols = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()]
            if date_cols:
                col = date_cols[0]
                try:
                    df[col] = pd.to_datetime(df[col])
                    df.set_index(col, inplace=True)
                    logger.info(f"Set index to '{col}' column")
                except Exception as e:
                    logger.warning(f"Failed to convert '{col}' to datetime index: {e}")
            else:
                # Fallback: try to parse first column as index if it looks like date
                # But don't force it if it's numeric
                try:
                    first_col = df.iloc[:, 0]
                    # Check if it looks like a date (string) or is actually object type
                    if pd.api.types.is_object_dtype(first_col) or pd.api.types.is_string_dtype(first_col):
                        df.index = pd.to_datetime(first_col)
                        df = df.iloc[:, 1:] # Remove first column if it became index
                        logger.info("Parsed first column as datetime index")
                except:
                    pass 

        # Task 28.1: Validate DataFrame
        self._validate_dataframe(df)
        
        # Task 7.1: Check for explicit column mappings
        explicit_mapping = {
            'open': open,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }
        has_explicit_mapping = any(v is not None for v in explicit_mapping.values())
        
        if has_explicit_mapping:
            # Task 7.1: Use explicit column mapping
            ohlc_mapping = {}
            for ohlc_name, col_name in explicit_mapping.items():
                if col_name is not None:
                    if col_name not in df.columns:
                        raise ValueError(
                            f"Column '{col_name}' for '{ohlc_name}' not found in DataFrame. "
                            f"Available columns: {list(df.columns)}"
                        )
                    ohlc_mapping[ohlc_name] = col_name
                else:
                    # Fall back to auto-detection for unspecified columns
                    pass
            
            # Auto-detect any unspecified columns
            auto_mapping = detect_ohlc_columns(df)
            for key in ['open', 'high', 'low', 'close', 'volume']:
                if key not in ohlc_mapping and auto_mapping.get(key):
                    ohlc_mapping[key] = auto_mapping[key]
            
            logger.info(f"Using explicit OHLC mapping: {ohlc_mapping}")
        else:
            # Task 28.2: Auto-detect OHLC columns
            ohlc_mapping = detect_ohlc_columns(df)
            logger.info(f"Detected OHLC columns: {ohlc_mapping}")
        
        if not ohlc_mapping.get('open') or not ohlc_mapping.get('close'):
            raise ValueError(
                "DataFrame must contain at least 'open' and 'close' columns. "
                f"Detected columns: {list(df.columns)}"
            )
        
        # Task 28.3: Detect and classify indicators
        indicator_columns = detect_indicator_columns(df, ohlc_mapping)
        logger.info(f"Detected indicator columns: {indicator_columns}")
        
        # Task 7.1: Handle indicators dict classification
        if indicators is not None:
            # Use explicit indicator classification
            overlays = overlays if overlays is not None else []
            subplots = subplots if subplots is not None else []
            
            for ind_name, is_overlay in indicators.items():
                if ind_name in df.columns:
                    if is_overlay:
                        if ind_name not in overlays:
                            overlays.append(ind_name)
                    else:
                        if ind_name not in subplots:
                            subplots.append(ind_name)
                else:
                    logger.warning(f"Indicator '{ind_name}' not found in DataFrame columns")
            
            logger.info(f"Using indicators dict: overlays={overlays}, subplots={subplots}")
        elif overlays is None or subplots is None:
            # Task 28.4: Auto-classify indicators
            auto_overlays, auto_subplots = classify_indicators(indicator_columns)
            overlays = overlays if overlays is not None else auto_overlays
            subplots = subplots if subplots is not None else auto_subplots
            logger.info(f"Auto-classified: overlays={overlays}, subplots={subplots}")
        else:
            logger.info(f"Using manual classification: overlays={overlays}, subplots={subplots}")
        
        # Task 28.5 / Task 29: Continue with transformation and server startup
        return self._start_chart(df, ohlc_mapping, overlays, subplots)
    
    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """
        Validate DataFrame structure.
        
        Task 28.1: DataFrame validation logic
        
        Raises:
            ValueError: If DataFrame is invalid
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError(
                "DataFrame must have DatetimeIndex. "
                f"Current index type: {type(df.index).__name__}"
            )
        
        if len(df) == 0:
            raise ValueError("DataFrame cannot be empty")
        
        logger.debug(f"DataFrame validated: {len(df)} rows")
    
    def _start_chart(
        self,
        df: pd.DataFrame,
        ohlc_mapping: Dict[str, str],
        overlays: List[str],
        subplots: List[str]
    ) -> str:
        """
        Start chart server and display in browser.
        
        Task 29: Complete load orchestration
        
        Args:
            df: Validated DataFrame
            ohlc_mapping: OHLC column mapping
            overlays: Overlay indicator columns
            subplots: Subplot indicator columns
            
        Returns:
            Chart URL
            
        Raises:
            RuntimeError: If chart startup fails
        """
        try:
            # Task 29.1: Transform DataFrame to CSV
            logger.info("Transforming DataFrame to CSV...")
            indicator_columns = overlays + subplots
            csv_path = transform_dataframe_to_csv(
                df,
                ohlc_mapping,
                indicator_columns
            )
            
            # Task 29.5: Track temp file for cleanup
            self.temp_files.append(csv_path)
            logger.info(f"CSV created: {csv_path}")
            
            # Task 29.2: Start server
            logger.info("Starting FastAPI server...")
            # Lazy import to avoid circular dependency with processor
            from src.api.main import app
            self.server_manager = ServerManager(app, self.port)
            chart_url = self.server_manager.start(
                csv_path,
                overlays=overlays,
                subplots=subplots
            )
            logger.info(f"Server started: {chart_url}")
            
            # Task 29.3: Launch browser
            if self.auto_open:
                logger.info("Launching browser...")
                launch_browser(chart_url)
            else:
                print(f"\nChart available at: {chart_url}\n")
            
            return chart_url
            
        except Exception as e:
            # Task 29.4: Error handling and cleanup
            logger.error(f"Failed to start chart: {e}")
            self.close()
            raise RuntimeError(f"Failed to start chart: {e}") from e
    
    def _cleanup_temp_files(self) -> None:
        """
        Clean up temporary CSV files.
        
        Task 27.2: Cleanup functionality
        """
        for filepath in self.temp_files:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logger.debug(f"Removed temp file: {filepath}")
            except OSError as e:
                logger.warning(f"Failed to remove temp file {filepath}: {e}")
        
        self.temp_files.clear()
    
    def close(self) -> None:
        """
        Stop server and cleanup resources.
        
        Task 27.2: Resource cleanup
        """
        logger.info("Closing Charting instance...")
        
        # Stop server if running
        if self.server_manager:
            try:
                self.server_manager.stop()
                logger.info("Server stopped")
            except Exception as e:
                logger.warning(f"Error stopping server: {e}")
            finally:
                self.server_manager = None
        
        # Cleanup temporary files
        self._cleanup_temp_files()
        
        logger.info("Charting instance closed")
