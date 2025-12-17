"""Overmind AI Gateway - Main FastAPI Application"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles

from app.admin.main import admin_app
from app.ai.main import ai_app
from app.auth.main import auth_app
from app.core.http_client import close_http_client, get_http_client
from app.core.logging_config import logger
from app.database import init_db, close_db
from app.diary.main import diary_app
from app.middleware import RateLimiter, RequestLogger
from app.translation.main import translation_app

# Templates
TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리"""
    # Startup
    logger.info("Starting Overmind AI Gateway...")
    get_http_client()
    logger.info("HTTP client initialized")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down Overmind AI Gateway...")
    await close_http_client()
    logger.info("HTTP client closed")
    await close_db()
    logger.info("Database closed")


app = FastAPI(
    title="Overmind AI Gateway",
    description="통합 AI API 게이트웨이 - AI Chat & Translation Service",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware 등록 (순서 중요: 아래에서 위로 실행)
# 1. Rate Limiting (분당 10번)
app.add_middleware(RateLimiter, requests_per_minute=10)

# 2. Request Logging
app.add_middleware(RequestLogger)

# 3. CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Sub-Applications
app.mount("/ai", ai_app)
app.mount("/translate", translation_app)
app.mount("/auth", auth_app)
app.mount("/diary", diary_app)
app.mount("/admin", admin_app)

# Serve static files from the storage directory
app.mount("/storage", StaticFiles(directory="storage"), name="storage")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """메인 페이지 - 로그인 여부에 따라 리다이렉트"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "overmind-ai-gateway",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
