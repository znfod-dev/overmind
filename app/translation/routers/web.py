"""Translation web UI endpoints"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

# Get templates directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["translation-ui"])


@router.get(
    "/",
    response_class=HTMLResponse,
    summary="Translation web interface",
    description="Simple web UI for translation (like Google Translate)",
)
async def translation_ui(request: Request):
    """
    Translation web interface

    Provides a simple Google Translate-style interface for translation.
    """
    return templates.TemplateResponse(
        "translate.html", {"request": request, "title": "Overmind Translation Service"}
    )
