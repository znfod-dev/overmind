"""Auth web pages"""

from pathlib import Path
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.auth.services.auth import AuthService

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["auth-web"])


@router.get("/login", response_class=HTMLResponse, summary="Login page")
@router.get("/login/", response_class=HTMLResponse, summary="Login page with slash")
async def login_page(request: Request):
    """로그인 페이지"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/signup", response_class=HTMLResponse, summary="Signup page")
async def signup_page(request: Request):
    """회원가입 페이지"""
    return templates.TemplateResponse("signup.html", {"request": request})


@router.get("/me", response_class=HTMLResponse, summary="My page")
async def my_page(request: Request):
    """마이페이지 (프로필 수정, 비밀번호 변경) - authentication handled by JavaScript"""
    return templates.TemplateResponse("mypage.html", {
        "request": request
    })
