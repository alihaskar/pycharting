"""FastAPI server for PyCharting."""

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
    Find a free port in the specified range.
    
    Args:
        start_port: Starting port number to search from
        end_port: Ending port number to search to
        
    Returns:
        Free port number
        
    Raises:
        RuntimeError: If no free port is found in range
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
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
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
    from src.api.routes import router as api_router
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
    Run the PyCharting server.
    
    Args:
        host: Host to bind to
        port: Port to use. If None and auto_port is True, finds a free port
        auto_port: If True, automatically find a free port if specified port is unavailable
        reload: Enable auto-reload for development
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
