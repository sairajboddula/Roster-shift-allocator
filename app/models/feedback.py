"""Feedback model - employee/manager feedback on schedule quality."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.db.database import Base


class Feedback(Base):
    """Stores feedback ratings on individual schedule assignments."""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    roster_type = Column(String(20), nullable=False)

    rating = Column(Integer, nullable=False)         # 1-5
    comment = Column(Text, default="")
    is_conflict_report = Column(Boolean, default=False)
    suggested_swap_with = Column(Integer, nullable=True)  # employee_id suggestion

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    schedule = relationship("Schedule", back_populates="feedback")
    employee = relationship("Employee", back_populates="feedback")

    def __repr__(self) -> str:
        return f"<Feedback id={self.id} schedule={self.schedule_id} rating={self.rating}>"
