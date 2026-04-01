"""History model - summarises past schedule periods for learning."""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class History(Base):
    """Stores aggregate data about past shift periods per employee-department pair."""

    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    roster_type = Column(String(20), nullable=False, index=True)

    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    total_shifts = Column(Integer, default=0)
    night_shifts = Column(Integer, default=0)
    emergency_shifts = Column(Integer, default=0)
    avg_score = Column(Float, default=0.0)

    # Learning weights adjusted over time
    rotation_weight = Column(Float, default=1.0)
    skill_weight = Column(Float, default=1.0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    employee = relationship("Employee", back_populates="history")
    department = relationship("Department")

    def __repr__(self) -> str:
        return (
            f"<History id={self.id} emp={self.employee_id} "
            f"dept={self.department_id} shifts={self.total_shifts}>"
        )
