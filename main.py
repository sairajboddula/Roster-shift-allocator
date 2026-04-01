"""
Roster System - Entry Point
Run with: python main.py
"""
import uvicorn
from app.db.database import init_db
from app.db.seed import seed_all
from app.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Initialize database, seed data if empty, start server."""
    logger.info("Initializing Roster System...")
    init_db()
    seed_all()
    logger.info("Starting server at http://localhost:8000")
    uvicorn.run(
        "app:create_app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        factory=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
