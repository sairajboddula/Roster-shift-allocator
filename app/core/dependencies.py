"""FastAPI dependency providers."""
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.config import get_settings, Settings


# Type aliases for injection
DBSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]
