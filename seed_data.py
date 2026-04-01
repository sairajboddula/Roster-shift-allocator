"""
Standalone seed script.
Usage: python seed_data.py
Initialises the database and seeds both Medical and IT data.
"""
import sys
from pathlib import Path

# Ensure project root is on path when run directly
sys.path.insert(0, str(Path(__file__).parent))

from app.db.database import init_db
from app.db.seed import seed_all
from app.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    logger.info("Initialising database…")
    init_db()
    logger.info("Seeding data…")
    seed_all()
    logger.info("Done. Run 'python main.py' to start the server.")


if __name__ == "__main__":
    main()
