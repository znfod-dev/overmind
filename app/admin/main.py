"""Admin Sub-Application"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.admin.routers import api, web

admin_app = FastAPI(
    title="Overmind Admin",
    description="Admin dashboard for user management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include routers
admin_app.include_router(web.router)
admin_app.include_router(api.router)


@admin_app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "admin"
        }
    )
