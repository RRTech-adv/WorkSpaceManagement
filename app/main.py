from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging

from app.core.middleware import AuthMiddleware
from app.core.config import settings
from app.db.connection import get_db_pool, close_db_pool
from app.api import (
    auth,
    workspaces,
    members,
    integrations_jira,
    integrations_ado,
    integrations_snow,
    integrations_sp,
    db_init
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("Starting up...")
    try:
        await get_db_pool()
        logger.info("Database pool initialized")
    except ValueError as e:
        logger.warning(f"Database not configured: {e}. Some features will be unavailable.")
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}. Some features will be unavailable.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    try:
        await close_db_pool()
        logger.info("Database pool closed")
    except Exception as e:
        logger.warning(f"Error closing database pool: {e}")


app = FastAPI(
    title="PM Assist API",
    description="Production-grade FastAPI backend for workspace management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth middleware (exclude health check, docs, and auth endpoints)
app.add_middleware(
    AuthMiddleware,
    exclude_paths=["/docs", "/openapi.json", "/redoc", "/health", "/auth/validate", "/db"]
)

# Health check endpoint (before auth middleware)
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Include routers
app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(members.router)
app.include_router(integrations_jira.router)
app.include_router(integrations_ado.router)
app.include_router(integrations_snow.router)
app.include_router(integrations_sp.router)
app.include_router(db_init.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException with consistent error format."""
    # Ensure error detail is in consistent format
    if isinstance(exc.detail, dict):
        # If already in correct format (has error_code and message), use it
        if "error_code" in exc.detail and "message" in exc.detail:
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail
            )
        # If dict but not in our format, wrap it
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.detail.get("error_code", "HTTP_ERROR"),
                "message": exc.detail.get("message", str(exc.detail))
            }
        )
    else:
        # If detail is a string, format it consistently
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": "HTTP_ERROR",
                "message": str(exc.detail)
            }
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with consistent format."""
    errors = exc.errors()
    error_messages = []
    
    for error in errors:
        field = ".".join(str(loc) for loc in error.get("loc", []))
        msg = error.get("msg", "Validation error")
        error_messages.append(f"{field}: {msg}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "; ".join(error_messages),
            "details": errors
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions with better categorization."""
    from fastapi import HTTPException, RequestValidationError
    import requests
    
    # Don't handle HTTPException or ValidationError - they have their own handlers
    if isinstance(exc, (HTTPException, RequestValidationError)):
        raise exc
    
    # Log the full exception for debugging
    exc_type = type(exc).__name__
    logger.error(f"Unhandled exception at {request.method} {request.url.path}: {exc_type}: {exc}", exc_info=True)
    
    # Categorize exceptions and provide more specific error codes
    error_code = "INTERNAL_SERVER_ERROR"
    error_message = "An unexpected error occurred"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    # Value/Type errors (usually programming errors that should be caught)
    if isinstance(exc, ValueError):
        error_code = "INVALID_REQUEST"
        error_message = f"Invalid request: {str(exc)}"
        status_code = status.HTTP_400_BAD_REQUEST
    
    # Type errors
    elif isinstance(exc, TypeError):
        error_code = "INVALID_REQUEST"
        error_message = "Invalid request format. Please check your input."
        status_code = status.HTTP_400_BAD_REQUEST
    
    # Key errors
    elif isinstance(exc, KeyError):
        error_code = "MISSING_REQUIRED_FIELD"
        error_message = f"Required field missing: {str(exc)}"
        status_code = status.HTTP_400_BAD_REQUEST
    
    # Attribute errors
    elif isinstance(exc, AttributeError):
        error_code = "INVALID_REQUEST"
        error_message = f"Invalid request: {str(exc)}"
        status_code = status.HTTP_400_BAD_REQUEST
    
    # Not found errors
    elif isinstance(exc, FileNotFoundError):
        error_code = "RESOURCE_NOT_FOUND"
        error_message = str(exc) if str(exc) else "The requested resource was not found."
        status_code = status.HTTP_404_NOT_FOUND
    
    # Network/connection errors (from requests library)
    elif isinstance(exc, (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout)):
        error_code = "NETWORK_ERROR"
        error_message = "Network connection failed. Please check your connection and try again."
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    elif isinstance(exc, requests.exceptions.Timeout):
        error_code = "REQUEST_TIMEOUT"
        error_message = "The request timed out. Please try again."
        status_code = status.HTTP_504_GATEWAY_TIMEOUT
    
    elif isinstance(exc, requests.exceptions.HTTPError):
        error_code = "EXTERNAL_SERVICE_ERROR"
        error_message = f"External service error: {str(exc)}"
        status_code = status.HTTP_502_BAD_GATEWAY
    
    # Check error message for common patterns (only if not already categorized)
    if error_code == "INTERNAL_SERVER_ERROR":
        exc_message = str(exc).lower()
        exc_type_lower = exc_type.lower()
        
        # Database connection errors
        if "database" in exc_message and ("connection" in exc_message or "connect" in exc_message):
            error_code = "DATABASE_CONNECTION_ERROR"
            error_message = "Unable to connect to the database. Please try again later."
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
        # Database query/operation errors
        elif "database" in exc_message or ("sql" in exc_message and "error" in exc_message) or "aioodbc" in exc_type_lower:
            error_code = "DATABASE_ERROR"
            error_message = "A database error occurred. Please check your input and try again."
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Permission/authorization errors
        elif "permission" in exc_message or "authorized" in exc_message or "forbidden" in exc_message:
            error_code = "PERMISSION_DENIED"
            error_message = "You don't have permission to perform this action."
            status_code = status.HTTP_403_FORBIDDEN
        
        # Not found errors (message-based)
        elif "not found" in exc_message:
            error_code = "RESOURCE_NOT_FOUND"
            error_message = str(exc) if str(exc) else "The requested resource was not found."
            status_code = status.HTTP_404_NOT_FOUND
        
        # Blob storage errors
        elif "blob" in exc_message or ("storage" in exc_message and "error" in exc_message):
            error_code = "STORAGE_ERROR"
            error_message = "A storage error occurred. Please try again."
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # For unknown exceptions, provide helpful message
        else:
            # Extract a more user-friendly message from common patterns
            if exc_message:
                # Try to extract meaningful part of error message
                if len(exc_message) > 100:
                    error_message = "An unexpected error occurred. Please try again or contact support."
                else:
                    error_message = f"An error occurred: {str(exc)[:200]}"
            else:
                error_message = "An unexpected error occurred. Please try again or contact support if the problem persists."
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error_code": error_code,
            "message": error_message
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

