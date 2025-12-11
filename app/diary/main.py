"""Diary Sub-Application

This module creates a FastAPI sub-application for AI-powered diary conversations and generation.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.diary.routers import conversation, diary, web

# Create Diary Sub-App
diary_app = FastAPI(
    title="Overmind Diary Service",
    description="AI-powered conversational diary service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include routers
diary_app.include_router(web.router, tags=["diary-web"])  # Web pages (no prefix)
diary_app.include_router(conversation.router, tags=["conversations"])
diary_app.include_router(diary.router, tags=["diaries"])


@diary_app.get(
    "/health",
    tags=["health"],
    summary="Health check",
    description="Check if diary service is running",
)
async def health_check():
    """Diary service health check"""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "diary",
            "features": ["conversations", "diary_generation", "ai_personalization"],
        }
    )
