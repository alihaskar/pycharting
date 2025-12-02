"""
Server utilities for local HTTP server management.

Provides port management and server lifecycle utilities for the
Python API's local server functionality.
"""

import socket
import logging
import threading
from typing import Optional, List
import uvicorn

logger = logging.getLogger(__name__)


def find_available_port(preferred_port: int = 8000, max_attempts: int = 10) -> int:
    """
    Find an available port for the local server.
    
    Tries to bind to the preferred port first. If occupied, tries
    sequential ports until an available one is found.
    
    Args:
        preferred_port: First port to try (default: 8000)
        max_attempts: Maximum number of ports to try (default: 10)
        
    Returns:
        Available port number
        
    Raises:
        RuntimeError: If no available ports found in the range
        
    Examples:
        >>> port = find_available_port()
        >>> port >= 8000
        True
        >>> port = find_available_port(preferred_port=9000, max_attempts=5)
        >>> port >= 9000
        True
    """
    for port in range(preferred_port, preferred_port + max_attempts):
        try:
            # Try to bind to the port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                # If binding succeeds, port is available
                logger.info(f"Found available port: {port}")
                return port
        except OSError as e:
            # Port is occupied or binding failed
            logger.debug(f"Port {port} unavailable: {e}")
            continue
    
    # No available ports found in range
    end_port = preferred_port + max_attempts - 1
    raise RuntimeError(
        f"No available ports found in range {preferred_port}-{end_port}. "
        f"All {max_attempts} ports are occupied."
    )


class ServerManager:
    """
    Manages lifecycle of local FastAPI server for chart rendering.
    
    Handles starting the server in a background thread, building URLs
    with indicator parameters, and graceful shutdown.
    """
    
    def __init__(self, app, port: Optional[int] = None):
        """
        Initialize ServerManager.
        
        Args:
            app: FastAPI application instance
            port: Port number to use, or None to auto-detect
        """
        self.app = app
        self.port = port if port is not None else find_available_port()
        self.server: Optional[uvicorn.Server] = None
        self.thread: Optional[threading.Thread] = None
        
        logger.info(f"ServerManager initialized on port {self.port}")
    
    def build_url(
        self, 
        csv_filename: str,
        overlays: Optional[List[str]] = None,
        subplots: Optional[List[str]] = None
    ) -> str:
        """
        Build URL with query parameters for chart data endpoint.
        
        Args:
            csv_filename: Name of CSV file to load
            overlays: List of overlay indicator column names
            subplots: List of subplot indicator column names
            
        Returns:
            Complete URL with query parameters
        """
        base_url = f"http://127.0.0.1:{self.port}"
        params = [f"filename={csv_filename}"]
        
        if overlays:
            params.append(f"overlays={','.join(overlays)}")
        
        if subplots:
            params.append(f"subplots={','.join(subplots)}")
        
        return f"{base_url}?{'&'.join(params)}"
    
    def get_url(self) -> str:
        """
        Get base server URL.
        
        Returns:
            Base server URL without parameters
        """
        return f"http://127.0.0.1:{self.port}"
    
    def is_running(self) -> bool:
        """
        Check if server is currently running.
        
        Returns:
            True if server is running, False otherwise
        """
        return self.thread is not None and self.thread.is_alive()
    
    def start(
        self,
        csv_path: str,
        overlays: Optional[List[str]] = None,
        subplots: Optional[List[str]] = None
    ) -> str:
        """
        Start uvicorn server in background thread.
        
        Args:
            csv_path: Path to CSV file
            overlays: List of overlay indicator names
            subplots: List of subplot indicator names
            
        Returns:
            URL with chart data endpoint and parameters
        """
        if self.is_running():
            logger.warning("Server is already running")
            return self.build_url(csv_path, overlays, subplots)
        
        # Configure uvicorn server
        config = uvicorn.Config(
            self.app,
            host="127.0.0.1",
            port=self.port,
            log_level="info"
        )
        self.server = uvicorn.Server(config)
        
        # Start server in background thread
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        
        logger.info(f"Server started on http://127.0.0.1:{self.port}")
        
        # Build and return URL with parameters
        return self.build_url(csv_path, overlays, subplots)
    
    def stop(self, timeout: float = 5.0) -> None:
        """
        Stop the server gracefully.
        
        Args:
            timeout: Maximum time to wait for server shutdown (seconds)
        """
        if not self.is_running():
            logger.info("Server is not running")
            return
        
        # Signal server to stop
        if self.server:
            self.server.should_exit = True
        
        # Wait for thread to finish
        if self.thread:
            self.thread.join(timeout=timeout)
            
            if self.thread.is_alive():
                logger.warning(f"Server thread did not stop within {timeout}s timeout")
            else:
                logger.info("Server stopped successfully")
        
        # Clean up
        self.server = None
        self.thread = None

