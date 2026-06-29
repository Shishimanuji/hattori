"""FastAPI application entry point"""
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from app.core.config import settings
from app.core.database import init_db, create_all_tables, get_db
from app.routes import (
    auth, users, projects, dashboard, asset_types, resources,
    templates, assets, resource_types
)
from app.utils.jwt_utils import verify_token
from app.utils.exceptions import InvalidTokenException, TokenExpiredException, MissingTokenException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.app_version,
    debug=settings.debug,
)

# Add CORS middleware FIRST to ensure CORS headers are added to all responses including errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Execute on application startup"""
    logger.info("Starting up Project Resource Management System API")
    
    # Initialize database connection
    if not init_db():
        logger.error("Failed to connect to database. Application startup aborted.")
        raise RuntimeError("Database connection failed")
    
    # Create tables if they don't exist
    try:
        create_all_tables()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Execute on application shutdown"""
    logger.info("Shutting down Project Resource Management System API")


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify API is running"""
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "version": settings.app_version
    }


# API V1 routes
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(resources.router)
app.include_router(dashboard.router)
app.include_router(asset_types.router)

# New routes for redesigned schema
app.include_router(templates.router)
app.include_router(assets.router)
app.include_router(resource_types.router)

@app.get(f"{settings.api_v1_prefix}/", tags=["Root"])
async def root():
    """Root API endpoint"""
    return {
        "message": f"Welcome to {settings.api_title}",
        "version": settings.app_version,
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc",
        }
    }


# Database dependency
async def get_database():
    """Get database session"""
    return next(get_db())


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug,
        log_level="info",
    )
