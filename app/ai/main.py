"""AI Chat Sub-Application

This module creates a FastAPI sub-application for AI chat services.
It provides REST API endpoints for chat completion (both streaming and non-streaming).
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.ai.routers import chat

# Create AI Chat Sub-App
ai_app = FastAPI(
    title="Overmind AI Chat Service",
    description="AI-powered chat service supporting multiple providers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include routers
ai_app.include_router(chat.router, tags=["chat"])


@ai_app.get(
    "/health",
    tags=["health"],
    summary="Health check",
    description="Check if AI chat service is running",
)
async def health_check():
    """
    AI Chat service health check

    Returns:
        Status of AI chat service
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "ai_chat",
            "features": ["chat", "streaming"],
            "providers": ["claude", "google_ai", "openai"],
        }
    )
