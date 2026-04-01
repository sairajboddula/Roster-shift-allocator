"""Schedule SQLAlchemy model - one row per assignment."""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Float, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Schedule(Base):
    """Represents a single shift assignment for an employee."""

    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False)
    schedule_date = Column(Date, nullable=False, index=True)
    roster_type = Column(String(20), nullable=False, index=True)

    # AI output fields
    ai_score = Column(Float, default=0.0)       # 0.0 to 1.0
    reason = Column(Text, default="")           # Human-readable explanation
    rotation_score = Column(Float, default=0.0)
    skill_score = Column(Float, default=0.0)
    workload_score = Column(Float, default=0.0)
    fairness_score = Column(Float, default=0.0)

    # Meta
    is_manual_override = Column(Boolean, default=False)
    is_confirmed = Column(Boolean, default=False)
    generation_batch = Column(String(50), default="")  # UUID of the generation run
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    employee = relationship("Employee", back_populates="schedules")
    department = relationship("Department")
    shift = relationship("Shift")
    feedback = relationship("Feedback", back_populates="schedule", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<Schedule id={self.id} emp={self.employee_id} "
            f"dept={self.department_id} date={self.schedule_date}>"
        )
