"""
Main Charting class for Python API.

Provides a simple interface for displaying Pandas DataFrames as
interactive charts in the browser with automatic OHLC and indicator detection.
"""

import os
import logging
from typing import Optional, List, Dict
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
        df: pd.DataFrame,
        overlays: Optional[List[str]] = None,
        subplots: Optional[List[str]] = None
    ) -> str:
        """
        Load DataFrame and display as interactive chart.
        
        Task 28: DataFrame loading with auto-detection
        
        Args:
            df: Pandas DataFrame with OHLC data and optional indicators
            overlays: List of overlay indicator column names (optional)
            subplots: List of subplot indicator column names (optional)
            
        Returns:
            URL of the chart
            
        Raises:
            ValueError: If DataFrame is invalid
            RuntimeError: If chart startup fails
        """
        logger.info("Loading DataFrame...")
        
        # Task 28.1: Validate DataFrame
        self._validate_dataframe(df)
        
        # Task 28.2: Auto-detect OHLC columns
        ohlc_mapping = detect_ohlc_columns(df)
        
        if not ohlc_mapping.get('open') or not ohlc_mapping.get('close'):
            raise ValueError(
                "DataFrame must contain at least 'open' and 'close' columns. "
                f"Detected columns: {list(df.columns)}"
            )
        
        logger.info(f"Detected OHLC columns: {ohlc_mapping}")
        
        # Task 28.3: Detect and classify indicators
        indicator_columns = detect_indicator_columns(df, ohlc_mapping)
        logger.info(f"Detected indicator columns: {indicator_columns}")
        
        # Task 28.4: Handle manual override vs auto-classification
        if overlays is None or subplots is None:
            # Auto-classify indicators
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

