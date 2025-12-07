"""
Server Lifecycle Management for PyCharting.

This module manages the background execution and lifecycle of the PyCharting server.
Since the main Python script (e.g., a data science notebook or script) needs to remain responsive,
the chart server runs in a separate background thread.

This module handles:
- **Thread Management:** Starting and stopping the server in a daemon thread.
- **Heartbeat Monitoring:** Checking for WebSocket connections from the frontend.
- **Auto-Shutdown:** Automatically stopping the server when the browser tab is closed (connection lost) to prevent orphaned processes.
"""

import threading
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import uvicorn
from fastapi import WebSocket, WebSocketDisconnect
from pycharting.core.server import create_app, find_free_port

logger = logging.getLogger(__name__)


class ChartServer:
    """
    A controller for managing the PyCharting background server.

    This class encapsulates the logic for running the FastAPI/Uvicorn server in a separate thread.
    It includes a heartbeat mechanism that monitors a WebSocket connection from the frontend.
    If the frontend disconnects (e.g., user closes the tab), the server can automatically shut down
    after a configurable timeout.

    Attributes:
        host (str): The hostname to bind to.
        port (int): The port to bind to.
        auto_shutdown_timeout (float): Time in seconds to wait before shutting down after connection loss.
        app (FastAPI): The underlying FastAPI application instance.
    """
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        auto_shutdown_timeout: float = 5.0,
    ):
        """
        Initialize the ChartServer controller.

        Args:
            host (str): Host to bind the server to. Defaults to "127.0.0.1".
            port (Optional[int]): Port to use. If None, an available port is found automatically.
            auto_shutdown_timeout (float): Seconds to wait before auto-shutdown after the last client disconnects.
                Defaults to 5.0 seconds.
        """
        self.host = host
        self.port = port or find_free_port()
        self.auto_shutdown_timeout = auto_shutdown_timeout
        
        self._server_thread: Optional[threading.Thread] = None
        self._server = None
        self._running = False
        self._shutdown_event = threading.Event()
        self._last_heartbeat: Optional[datetime] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._websocket_connected = False
        
        # Create app with WebSocket endpoint
        self.app = create_app()
        self._add_websocket_endpoint()
    
    def _add_websocket_endpoint(self):
        """Add WebSocket heartbeat endpoint to the app."""
        @self.app.websocket("/ws/heartbeat")
        async def websocket_heartbeat(websocket: WebSocket):
            """WebSocket endpoint for connection monitoring."""
            await websocket.accept()
            self._websocket_connected = True
            self._last_heartbeat = datetime.now()
            logger.info("WebSocket client connected")
            
            try:
                while True:
                    # Wait for heartbeat from client
                    data = await websocket.receive_text()
                    if data == "ping":
                        self._last_heartbeat = datetime.now()
                        await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
                self._websocket_connected = False
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self._websocket_connected = False
    
    def _monitor_connection(self):
        """Monitor WebSocket connection and trigger auto-shutdown if needed."""
        while self._running and not self._shutdown_event.is_set():
            time.sleep(1)
            
            if self._websocket_connected and self._last_heartbeat:
                # Check if heartbeat is stale
                elapsed = (datetime.now() - self._last_heartbeat).total_seconds()
                if elapsed > self.auto_shutdown_timeout:
                    logger.warning(
                        f"No heartbeat for {elapsed:.1f}s, initiating shutdown"
                    )
                    self._websocket_connected = False
                    self.stop_server()
                    break
            
            elif not self._websocket_connected and self._last_heartbeat:
                # Client disconnected, wait for timeout then shutdown
                logger.info(
                    f"Waiting {self.auto_shutdown_timeout}s before auto-shutdown"
                )
                time.sleep(self.auto_shutdown_timeout)
                if not self._websocket_connected:
                    logger.info("Auto-shutdown triggered")
                    self.stop_server()
                    break
    
    def _run_server(self):
        """Run the Uvicorn server (called in background thread)."""
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info",
            access_log=False,
        )
        self._server = uvicorn.Server(config)
        
        try:
            self._server.run()
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self._running = False
    
    def start_server(self) -> Dict[str, Any]:
        """
        Start the web server in a background daemon thread.

        This method:
        1. Checks if the server is already running.
        2. Starts the Uvicorn server in a separate thread.
        3. Starts a monitor thread to check for WebSocket heartbeats.
        4. Waits briefly to ensure the server is up.

        Returns:
            Dict[str, Any]: A dictionary containing connection details:
                - `host`: The server host.
                - `port`: The server port.
                - `url`: The full HTTP URL to the server.
                - `ws_url`: The WebSocket URL for heartbeats.
                - `running`: Boolean status.

        Raises:
            RuntimeError: If the server is already running.
        """
        if self._running:
            raise RuntimeError("Server is already running")
        
        self._running = True
        self._shutdown_event.clear()
        
        # Start server thread
        self._server_thread = threading.Thread(
            target=self._run_server,
            daemon=True,
            name="PyCharting-Server"
        )
        self._server_thread.start()
        
        # Start monitor thread
        self._monitor_thread = threading.Thread(
            target=self._monitor_connection,
            daemon=True,
            name="PyCharting-Monitor"
        )
        self._monitor_thread.start()
        
        # Wait for server to start
        time.sleep(1)
        
        url = f"http://{self.host}:{self.port}"
        logger.info(f"Server started at {url}")
        logger.info(f"API docs available at {url}/api/docs")
        logger.info(f"WebSocket heartbeat at ws://{self.host}:{self.port}/ws/heartbeat")
        
        return {
            "host": self.host,
            "port": self.port,
            "url": url,
            "ws_url": f"ws://{self.host}:{self.port}/ws/heartbeat",
            "running": self._running,
        }
    
    def stop_server(self):
        """
        Gracefully stop the background server and monitor threads.

        This method signals the server to shut down, closes the Uvicorn loop,
        and joins the background threads. It is safe to call multiple times.
        """
        if not self._running:
            logger.warning("Server is not running")
            return
        
        logger.info("Stopping server...")
        self._running = False
        self._shutdown_event.set()
        
        # Shutdown Uvicorn server
        if self._server:
            self._server.should_exit = True
        
        # Only join threads if not called from within them
        current_thread = threading.current_thread()
        
        # Wait for server thread to finish
        if self._server_thread and self._server_thread.is_alive() and self._server_thread != current_thread:
            self._server_thread.join(timeout=5)
        
        # Wait for monitor thread to finish
        if self._monitor_thread and self._monitor_thread.is_alive() and self._monitor_thread != current_thread:
            self._monitor_thread.join(timeout=2)
        
        logger.info("Server stopped")
    
    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running
    
    @property
    def server_info(self) -> Dict[str, Any]:
        """Get current server information."""
        return {
            "host": self.host,
            "port": self.port,
            "running": self._running,
            "websocket_connected": self._websocket_connected,
            "last_heartbeat": self._last_heartbeat.isoformat() if self._last_heartbeat else None,
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.start_server()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_server()
        return False
    
    def __repr__(self) -> str:
        """String representation."""
        status = "running" if self._running else "stopped"
        return f"ChartServer(host={self.host}, port={self.port}, status={status})"
