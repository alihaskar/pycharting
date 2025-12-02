"""
Main Charting class for Python API.

Provides a simple interface for displaying Pandas DataFrames as
interactive charts in the browser with automatic OHLC and indicator detection.
"""

import os
import logging
from typing import Optional, List
import pandas as pd

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
        # Stub - will be implemented in Task 28
        raise NotImplementedError("load() will be implemented in Task 28")
    
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

