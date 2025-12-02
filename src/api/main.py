"""Main FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from src.api import routes
from src.api import exceptions as api_exceptions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting Financial Charting API...")
    logger.info(f"API version: {app.version}")
    yield
    # Shutdown
    logger.info("Shutting down Financial Charting API...")


def get_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Financial Charting API",
        description="API for serving financial chart data with technical indicators",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify exact origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Root endpoint
    @app.get("/", tags=["info"])
    async def root():
        """
        Get API information.
        
        Returns:
            API name and version
        """
        return {
            "name": app.title,
            "version": app.version,
            "description": app.description
        }
    
    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """
        Health check endpoint.
        
        Returns:
            Health status
        """
        return {"status": "healthy"}
    
    # Include routers
    app.include_router(routes.router)
    
    # Register exception handlers
    @app.exception_handler(api_exceptions.APIException)
    async def api_exception_handler(request: Request, exc: api_exceptions.APIException):
        """Handle custom API exceptions."""
        logger.error(f"API error: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message}
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle FastAPI validation errors."""
        logger.error(f"Validation error: {exc}")
        return JSONResponse(
            status_code=422,
            content={"detail": "Validation error", "errors": exc.errors()}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    return app


# Create application instance
app = get_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

