"""
Core Server Module for PyCharting.

This module implements the FastAPI-based web server that powers the interactive charts.
It handles serving static assets (HTML, JS, CSS) and providing API endpoints for data retrieval.
The server is designed to run locally and provide a seamless bridge between the Python runtime
and the browser-based visualization.

Key Responsibilities:
- **Port Management:** Automatically finding available ports for the server.
- **Application Factory:** Creating and configuring the FastAPI application instance.
- **Static File Serving:** Serving the frontend assets required for the chart UI.
- **API Routing:** Connecting API routes to the application.
- **Server Execution:** Launching the Uvicorn server.
"""

import socket
import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_free_port(start_port: int = 8000, end_port: int = 9000) -> int:
    """
    Find an available TCP port in the specified range.

    This utility function iterates through a range of ports to find one that is currently
    not in use. This is crucial for ensuring the chart server can start without conflicts,
    even if the default port is occupied or multiple instances are running.

    Args:
        start_port (int): The starting port number to search from (inclusive). Defaults to 8000.
        end_port (int): The ending port number to search to (exclusive). Defaults to 9000.

    Returns:
        int: An available port number found within the range.

    Raises:
        RuntimeError: If no free port can be found in the specified range.

    Example:
        ```python
        port = find_free_port(8000, 8010)
        print(f"Found free port: {port}")
        ```
    """
    for port in range(start_port, end_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                return port
        except OSError:
            continue
    
    raise RuntimeError(f"No free port found in range {start_port}-{end_port}")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.

    This factory function initializes the FastAPI app with necessary configurations:
    - Sets up metadata (title, description, version).
    - Configures CORS (Cross-Origin Resource Sharing) to allow local browser access.
    - Mounts the static files directory to serve the frontend application.
    - Configures the root endpoint to serve the main HTML entry point.
    - Includes the API router for data endpoints.
    - Sets up global exception handlers and health check endpoints.

    The application is stateless regarding data; data is managed via the `_data_managers`
    registry in `src.api.routes` which is accessed by the API routes included here.

    Returns:
        FastAPI: The fully configured FastAPI application ready to be run by Uvicorn.
    """
    app = FastAPI(
        title="PyCharting",
        description="Interactive charting and data visualization API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )
    
    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify exact origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Set up static files directory
    static_dir = Path(__file__).parent.parent / "web" / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # Mount static files
    try:
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info(f"Static files mounted from: {static_dir}")
    except Exception as e:
        logger.warning(f"Could not mount static files: {e}")
    
    # Root endpoint
    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Serve the main chart page."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>PyCharting</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background: #f5f5f5;
                }
                .container {
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #333;
                    margin-bottom: 10px;
                }
                p {
                    color: #666;
                    line-height: 1.6;
                }
                .api-link {
                    display: inline-block;
                    margin-top: 20px;
                    padding: 10px 20px;
                    background: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                }
                .api-link:hover {
                    background: #0056b3;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>PyCharting Server</h1>
                <p>Welcome to PyCharting - Interactive charting and data visualization.</p>
                <p>The server is running successfully!</p>
                <a href="/api/docs" class="api-link">View API Documentation</a>
            </div>
        </body>
        </html>
        """
    
    # Include API routes
    from pycharting.api.routes import router as api_router
    app.include_router(api_router)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "pycharting"}
    
    # Error handlers
    @app.exception_handler(404)
    async def not_found_handler(request, exc):
        """Handle 404 errors."""
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=404,
            content={"error": "Not found", "path": str(request.url.path)}
        )
    
    @app.exception_handler(500)
    async def server_error_handler(request, exc):
        """Handle 500 errors."""
        from fastapi.responses import JSONResponse
        logger.error(f"Server error: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
    
    return app


def run_server(
    host: str = "127.0.0.1",
    port: Optional[int] = None,
    auto_port: bool = True,
    reload: bool = False,
) -> None:
    """
    Launch the PyCharting web server.

    This function is the main entry point for running the server directly (e.g., for development).
    It handles port selection, application creation, and starting the Uvicorn server process.

    In the library usage context, this is typically managed by `src.core.lifecycle.ChartServer`,
    which runs this logic in a background thread. However, this function can be used to run
    the server in the main thread (blocking) or for testing purposes.

    Args:
        host (str): The hostname or IP address to bind the server to. Defaults to "127.0.0.1".
        port (Optional[int]): The specific port to use. If `None`, a free port will be found automatically
            unless `auto_port` is False.
        auto_port (bool): If True (default), automatically finds an alternative free port if the specified
            (or default) port is unavailable.
        reload (bool): If True, enables Uvicorn's auto-reload feature. Useful for development.
            Defaults to False.

    Returns:
        None: This function blocks until the server stops.

    Example:
        ```python
        # Run server on localhost, finding a free port automatically
        run_server()

        # Run on a specific port
        run_server(port=8080)
        ```
    """
    # Determine port
    if port is None:
        port = find_free_port()
        logger.info(f"Auto-selected port: {port}")
    elif auto_port:
        try:
            # Test if port is available
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
        except OSError:
            logger.warning(f"Port {port} is in use, finding alternative...")
            port = find_free_port(port + 1)
            logger.info(f"Using alternative port: {port}")
    
    app = create_app()
    
    logger.info(f"Starting PyCharting server at http://{host}:{port}")
    logger.info(f"API documentation available at http://{host}:{port}/api/docs")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        reload=reload,
    )


# Create app instance for direct import
app = create_app()


if __name__ == "__main__":
    run_server(reload=True)
