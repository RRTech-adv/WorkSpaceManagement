from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    # Don't handle HTTPException - FastAPI handles it automatically
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        # Let FastAPI's default handler process HTTPException
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail}
        )
    
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred"
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

