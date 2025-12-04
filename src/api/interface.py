"""Main Python API interface for PyCharting."""

import webbrowser
import time
import logging
from typing import Optional, Dict, Any, Union
import numpy as np
import pandas as pd

from data.ingestion import DataManager
from core.lifecycle import ChartServer
from api.routes import _data_managers

logger = logging.getLogger(__name__)

# Global server instance
_active_server: Optional[ChartServer] = None


def plot(
    index: Union[np.ndarray, pd.Series, list],
    open: Union[np.ndarray, pd.Series, list],
    high: Union[np.ndarray, pd.Series, list],
    low: Union[np.ndarray, pd.Series, list],
    close: Union[np.ndarray, pd.Series, list],
    overlays: Optional[Dict[str, Union[np.ndarray, pd.Series, list]]] = None,
    subplots: Optional[Dict[str, Union[np.ndarray, pd.Series, list]]] = None,
    session_id: str = "default",
    port: Optional[int] = None,
    open_browser: bool = True,
    server_timeout: float = 2.0,
) -> Dict[str, Any]:
    """
    Create and display an interactive OHLC chart.
    
    This is the main entry point for PyCharting. It creates a chart server,
    loads your data, and opens it in your default web browser.
    
    Args:
        index: Time or index values for x-axis
        open: Opening prices
        high: High prices
        low: Low prices
        close: Closing prices
        overlays: Optional dict of overlay series (e.g., moving averages)
        subplots: Optional dict of subplot series (e.g., volume, indicators)
        session_id: Unique identifier for this chart session
        port: Server port (None for auto-discovery)
        open_browser: Whether to automatically open the browser
        server_timeout: Seconds to wait for server startup
        
    Returns:
        Dict with server info including URL and status
        
    Example:
        ```python
        import numpy as np
        from pycharting import plot
        
        # Generate sample data
        n = 100
        index = np.arange(n)
        close = np.cumsum(np.random.randn(n)) + 100
        open = close + np.random.randn(n) * 0.5
        high = np.maximum(open, close) + np.abs(np.random.randn(n))
        low = np.minimum(open, close) - np.abs(np.random.randn(n))
        
        # Create interactive chart
        plot(index, open, high, low, close)
        ```
    """
    global _active_server
    
    try:
        # Convert lists to numpy arrays for convenience
        if isinstance(index, list):
            index = np.array(index)
        if isinstance(open, list):
            open = np.array(open)
        if isinstance(high, list):
            high = np.array(high)
        if isinstance(low, list):
            low = np.array(low)
        if isinstance(close, list):
            close = np.array(close)
        
        # Convert overlay lists
        if overlays:
            overlays = {
                k: np.array(v) if isinstance(v, list) else v
                for k, v in overlays.items()
            }
        
        # Convert subplot lists
        if subplots:
            subplots = {
                k: np.array(v) if isinstance(v, list) else v
                for k, v in subplots.items()
            }
        
        # Create DataManager with validation
        logger.info("Creating DataManager...")
        data_manager = DataManager(
            index=index,
            open=open,
            high=high,
            low=low,
            close=close,
            overlays=overlays,
            subplots=subplots
        )
        
        # Store in global session registry for API access
        _data_managers[session_id] = data_manager
        logger.info(f"Data loaded: {data_manager.length} points")
        
        # Start or reuse server
        if _active_server is None or not _active_server.is_running:
            logger.info("Starting ChartServer...")
            _active_server = ChartServer(
                host="127.0.0.1",
                port=port,
                auto_shutdown_timeout=300.0  # 5 minutes
            )
            server_info = _active_server.start_server()
            
            # Wait for server to be ready
            time.sleep(server_timeout)
            
        else:
            logger.info("Reusing existing ChartServer...")
            server_info = _active_server.server_info
            server_info['url'] = f"http://{server_info['host']}:{server_info['port']}"
        
        # Construct chart URL with session ID
        # Use viewport demo which pulls data from the API for the given session
        chart_url = f"{server_info['url']}/static/viewport-demo.html?session={session_id}"
        
        # Open browser if requested
        if open_browser:
            logger.info(f"Opening browser: {chart_url}")
            try:
                webbrowser.open(chart_url)
            except Exception as e:
                logger.warning(f"Could not open browser: {e}")
                print(f"Please open this URL manually: {chart_url}")
        
        result = {
            "status": "success",
            "url": chart_url,
            "server_url": server_info['url'],
            "session_id": session_id,
            "data_points": data_manager.length,
            "server_running": _active_server.is_running if _active_server else False,
        }
        
        # Print user-friendly message
        print(f"\n✓ Chart created successfully!")
        print(f"  URL: {chart_url}")
        print(f"  Data points: {data_manager.length:,}")
        if not open_browser:
            print(f"  Open the URL above in your browser to view the chart.")
        print()
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating chart: {e}", exc_info=True)
        print(f"\n✗ Error creating chart: {e}\n")
        
        return {
            "status": "error",
            "error": str(e),
            "session_id": session_id,
        }


def stop_server():
    """
    Stop the active chart server.
    
    Call this to manually stop the server when you're done viewing charts.
    The server also auto-stops after 5 minutes of inactivity.
    
    Example:
        ```python
        from pycharting import stop_server
        
        # When done with all charts
        stop_server()
        ```
    """
    global _active_server
    
    if _active_server and _active_server.is_running:
        logger.info("Stopping ChartServer...")
        _active_server.stop_server()
        print("✓ Chart server stopped")
    else:
        print("ⓘ No active server to stop")


def get_server_status() -> Dict[str, Any]:
    """
    Get the status of the active chart server.
    
    Returns:
        Dict with server status information
        
    Example:
        ```python
        from pycharting import get_server_status
        
        status = get_server_status()
        print(status)
        ```
    """
    global _active_server
    
    if _active_server:
        return {
            "running": _active_server.is_running,
            "server_info": _active_server.server_info,
            "active_sessions": len(_data_managers),
        }
    else:
        return {
            "running": False,
            "server_info": None,
            "active_sessions": 0,
        }


# Jupyter notebook support
def _repr_html_():
    """Jupyter notebook representation."""
    status = get_server_status()
    if status['running']:
        url = f"http://{status['server_info']['host']}:{status['server_info']['port']}"
        return f'''
        <div style="padding: 10px; background: #f0f0f0; border-radius: 5px;">
            <strong>PyCharting Server</strong><br>
            Status: <span style="color: green;">●</span> Running<br>
            URL: <a href="{url}" target="_blank">{url}</a><br>
            Active Sessions: {status['active_sessions']}
        </div>
        '''
    else:
        return '''
        <div style="padding: 10px; background: #f0f0f0; border-radius: 5px;">
            <strong>PyCharting Server</strong><br>
            Status: <span style="color: red;">●</span> Stopped
        </div>
        '''


# Export main functions
__all__ = ['plot', 'stop_server', 'get_server_status']
