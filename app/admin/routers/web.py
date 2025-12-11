"""Admin web pages"""

from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["admin-web"])


@router.get("/", response_class=HTMLResponse, summary="Admin dashboard")
async def admin_dashboard(request: Request):
    """Admin dashboard - authentication handled by JavaScript"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request
    })


@router.get("/users", response_class=HTMLResponse, summary="User list page")
async def user_list_page(request: Request):
    """User list page - authentication handled by JavaScript"""
    return templates.TemplateResponse("user_list.html", {
        "request": request
    })


@router.get("/users/{user_id}", response_class=HTMLResponse, summary="User detail page")
async def user_detail_page(request: Request, user_id: int):
    """User detail page - authentication handled by JavaScript"""
    return templates.TemplateResponse("user_detail.html", {
        "request": request,
        "user_id": user_id
    })
