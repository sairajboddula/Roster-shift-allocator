"""Shift type SQLAlchemy model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime

from app.db.database import Base


class Shift(Base):
    """Defines a shift type: morning, evening, night, etc."""

    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)          # e.g. "Morning", "Night Support"
    shift_key = Column(String(30), nullable=False, index=True)  # e.g. "morning", "night_support"
    roster_type = Column(String(20), nullable=False, index=True)
    start_time = Column(String(5), nullable=False)     # "HH:MM" format
    end_time = Column(String(5), nullable=False)       # "HH:MM" format
    duration_hours = Column(Float, nullable=False)
    is_night_shift = Column(Boolean, default=False)
    is_emergency = Column(Boolean, default=False)
    on_call = Column(Boolean, default=False)
    color_hex = Column(String(7), default="#3B82F6")  # For UI calendar rendering
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Shift id={self.id} key={self.shift_key!r} type={self.roster_type!r}>"
