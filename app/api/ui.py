"""UI routes - serve Jinja2 HTML templates with auth protection."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.core.auth_deps import CurrentUserUI, get_optional_user
from app.core.dependencies import DBSession

ui_router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")


def _ctx(request: Request, user, **extra) -> dict:
    return {"request": request, "user": user, **extra}


# ── Public pages (no auth required) ────────────────────────────────────────

@ui_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@ui_router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html")


# ── Protected pages ──────────────────────────────────────────────────────────

@ui_router.get("/", response_class=HTMLResponse)
async def index(request: Request, user: CurrentUserUI):
    return templates.TemplateResponse(request, "index.html", _ctx(request, user))


@ui_router.get("/employees", response_class=HTMLResponse)
async def employees_page(request: Request, user: CurrentUserUI):
    return templates.TemplateResponse(request, "employees.html", _ctx(request, user))


@ui_router.get("/departments", response_class=HTMLResponse)
async def departments_page(request: Request, user: CurrentUserUI):
    return templates.TemplateResponse(request, "departments.html", _ctx(request, user))


@ui_router.get("/schedule", response_class=HTMLResponse)
async def schedule_page(request: Request, user: CurrentUserUI):
    return templates.TemplateResponse(request, "schedule.html", _ctx(request, user))
