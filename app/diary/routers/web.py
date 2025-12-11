"""Diary web pages"""

from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["diary-web"])


@router.get("/", response_class=HTMLResponse, summary="Diary main page")
async def diary_main_page(request: Request):
    """일기장 메인 페이지 (달력 + 일기 보기)"""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/write", response_class=HTMLResponse, summary="Write diary page")
async def write_diary_page(request: Request):
    """일기 작성 페이지 (채팅 형식)"""
    return templates.TemplateResponse("write.html", {"request": request})
