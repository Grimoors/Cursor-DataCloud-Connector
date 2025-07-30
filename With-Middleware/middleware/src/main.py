"""
Main application entry point for the Salesforce Data Cloud Middleware.

This module initializes the FastAPI application, configures middleware,
sets up logging, and starts the server. It supports both REST API
and MCP server modes.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.config.settings import get_settings
from src.api.routes import api_router
from src.mcp.server import create_mcp_server
from src.utils.logging import setup_logging

# Configure structured logging
setup_logging()
logger = structlog.get_logger(__name__)

# Global settings instance
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application.
    Initializes and cleans up resources as needed.
    """
    # Startup
    logger.info("Starting Salesforce Data Cloud Middleware", 
                version="1.0.0", 
                environment=settings.environment)
    
    # Initialize MCP server if enabled
    if settings.enable_mcp:
        try:
            mcp_server = create_mcp_server()
            app.state.mcp_server = mcp_server
            logger.info("MCP server initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize MCP server", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("Shutting down Salesforce Data Cloud Middleware")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title="Salesforce Data Cloud Middleware",
        description="Middleware service for Salesforce Data Cloud integration with IDE extensions",
        version="1.0.0",
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url="/redoc" if settings.enable_docs else None,
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log incoming requests and their processing time."""
        start_time = asyncio.get_event_loop().time()
        
        # Log request
        logger.info("Incoming request",
                   method=request.method,
                   url=str(request.url),
                   client_ip=request.client.host if request.client else None)
        
        response = await call_next(request)
        
        # Log response
        process_time = asyncio.get_event_loop().time() - start_time
        logger.info("Request completed",
                   method=request.method,
                   url=str(request.url),
                   status_code=response.status_code,
                   process_time=f"{process_time:.3f}s")
        
        return response
    
    # Add exception handler
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        """Handle Pydantic validation errors."""
        logger.warning("Validation error", 
                      errors=exc.errors(),
                      path=request.url.path)
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "details": exc.errors(),
                "message": "Invalid request data"
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error("Unhandled exception",
                    error=str(exc),
                    error_type=type(exc).__name__,
                    path=request.url.path,
                    exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred"
            }
        )
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint for monitoring."""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "environment": settings.environment
        }
    
    return app


def main():
    """Main application entry point."""
    try:
        # Create the application
        app = create_app()
        
        # Configure uvicorn settings
        uvicorn_config = {
            "app": app,
            "host": settings.host,
            "port": settings.port,
            "log_level": settings.log_level.lower(),
            "access_log": True,
            "reload": settings.environment == "development",
        }
        
        logger.info("Starting server",
                   host=settings.host,
                   port=settings.port,
                   environment=settings.environment)
        
        # Start the server
        uvicorn.run(**uvicorn_config)
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error("Failed to start server", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main() 