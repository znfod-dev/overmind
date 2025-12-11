"""Auth Sub-Application

This module creates a FastAPI sub-application for user authentication and profile management.
"""

from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse

from app.auth.routers import auth, profile, web
from app.dependencies.auth import get_current_user
from app.models import User
from app.auth.schemas.responses import UserResponse

# Create Auth Sub-App
auth_app = FastAPI(
    title="Overmind Auth Service",
    description="User authentication and profile management service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include routers
auth_app.include_router(web.router, tags=["auth-web"])  # Web pages (no prefix)
auth_app.include_router(auth.router, tags=["auth"])
auth_app.include_router(profile.router, tags=["profile"])


# Convenience endpoint without /api prefix for better UX
@auth_app.get(
    "/me",
    response_model=UserResponse,
    tags=["auth"],
    summary="Get current user (convenience endpoint)"
)
async def get_me_shortcut(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current user - same as /api/me but without /api prefix"""
    return UserResponse.model_validate(current_user)


@auth_app.get(
    "/health",
    tags=["health"],
    summary="Health check",
    description="Check if auth service is running",
)
async def health_check():
    """Auth service health check"""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "auth",
            "features": ["signup", "login", "jwt_auth", "profile"],
        }
    )
