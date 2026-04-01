"""Roster System Application Factory."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.api.router import api_router
from app.core.exceptions import register_exception_handlers
from app.utils.logger import get_logger

logger = get_logger(__name__)

BASE_DIR = Path(__file__).parent


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="AI Roster System",
        description="AI-powered Shift Planning & Roster System for Medical and IT domains",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

    # Register routers
    app.include_router(api_router, prefix="/api")

    # Register exception handlers
    register_exception_handlers(app)

    # Register UI routes
    from app.api.ui import ui_router
    app.include_router(ui_router)

    # Ensure DB tables exist and seed on startup (covers gunicorn/Render where main.py is not run)
    @app.on_event("startup")
    def _startup():
        from app.db.database import init_db
        from app.db.seed import seed_all
        init_db()
        seed_all()

    logger.info("Application created successfully.")
    return app
