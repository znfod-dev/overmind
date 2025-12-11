"""Translation Sub-Application

This module creates a FastAPI sub-application for translation services.
It provides both REST API endpoints and a web UI for translation.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.translation.routers import api, web

# Create Translation Sub-App
translation_app = FastAPI(
    title="Overmind Translation Service",
    description="AI-powered translation service supporting 5 languages",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include routers
translation_app.include_router(web.router, tags=["translation-ui"])
translation_app.include_router(api.router, tags=["translation-api"])


@translation_app.get(
    "/health",
    tags=["health"],
    summary="Health check",
    description="Check if translation service is running",
)
async def health_check():
    """
    Translation service health check

    Returns:
        Status of translation service
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "translation",
            "features": ["web_ui", "rest_api"],
            "languages": ["ko", "vi", "en", "zh", "ru"],
            "providers": ["claude", "google_ai", "openai"],
        }
    )
