import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.api.v1.api import api_router
from app.core.settings import settings
from app.db.session import create_tables, db_manager
from app.services.cache import rate_limiter
from app.core.logging_config import configure_logging # Import the new logging config

# Configure logging early
configure_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware (in-memory only for Fly.io optimization)."""
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        
        # Check rate limit
        rate_limit_key = f"rate_limit:{client_ip}"
        if not rate_limiter.is_allowed(rate_limit_key, settings.RATE_LIMIT_PER_MINUTE, 60):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        return await call_next(request)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Performance monitoring middleware."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Add request ID for tracing
        request_id = f"{int(start_time * 1000)}-{hash(str(request.url))}"
        
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add performance headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        # Log slow requests
        if process_time > 1.0:  # Log requests taking more than 1 second
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {process_time:.2f}s (Request ID: {request_id})"
            )
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting up Recipe Scraper API...")
    
    # Create database tables
    try:
        await create_tables()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
    
    # Check database connectivity
    if await db_manager.health_check():
        logger.info("Database connection verified")
    else:
        logger.error("Database connection failed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Recipe Scraper API...")
    await db_manager.close_all_connections()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="A comprehensive API for scraping recipes with video support, meal planning, and recommendations",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add middleware (order matters!)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(PerformanceMiddleware)
app.add_middleware(RateLimitMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time", "X-Request-ID"]
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check database
    db_healthy = await db_manager.health_check()
    
    # Overall health
    healthy = db_healthy
    
    status_code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if healthy else "unhealthy",
            "timestamp": time.time(),
            "version": settings.APP_VERSION,
            "database": {
                "status": "healthy" if db_healthy else "unhealthy",
                "connection_info": await db_manager.get_connection_info() if db_healthy else None
            },
            "dependencies": {
                "gemini_api": "configured" if settings.GEMINI_API_KEY else "not configured",
                "youtube_api": "configured" if settings.YOUTUBE_API_KEY else "not configured",
            }
        }
    )


# Metrics endpoint (simplified for Fly.io optimization)
@app.get("/metrics")
async def get_metrics():
    """Get application metrics."""
    return {
        "database": await db_manager.get_connection_info(),
        "application": {
            "version": settings.APP_VERSION,
            "debug_mode": settings.DEBUG
        }
    }


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail} for {request.method} {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "method": request.method,
            "timestamp": time.time()
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    request_id = request.headers.get("X-Request-ID", "unknown")
    logger.exception(f"Unhandled exception for Request ID: {request_id}") # Logs traceback
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "request_id": request_id,
            "timestamp": time.time()
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to Recipe Scraper API",
        "version": settings.APP_VERSION,
        "docs_url": "/docs" if settings.DEBUG else "Documentation not available in production",
        "health_check": "/health",
        "api_prefix": "/api/v1"
    }


# Startup event logging
@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info(f"Recipe Scraper API v{settings.APP_VERSION} started successfully")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'Not configured'}")
    logger.info("Cache backend: In-memory (Redis removed for optimization)")