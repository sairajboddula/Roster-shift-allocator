"""Employee SQLAlchemy model."""
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.database import Base


class Employee(Base):
    """Represents a staff member owned by a specific user (medical or IT domain)."""

    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("user_id", "email", name="uq_employee_user_email"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(150), nullable=False)
    role = Column(String(50), nullable=False)
    roster_type = Column(String(20), nullable=False, index=True)  # medical | it

    # Skills stored as JSON array: ["Python", "DevOps"] or ["ICU", "Surgery"]
    skills_json = Column(Text, default="[]")

    # Availability stored as JSON: {"monday": true, "tuesday": true, ...}
    availability_json = Column(Text, default="{}")

    max_shifts_per_week = Column(Integer, default=5)
    department_id = Column(Integer, nullable=True)  # current default department
    experience_years = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    schedules = relationship("Schedule", back_populates="employee", cascade="all, delete-orphan")
    history = relationship("History", back_populates="employee", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="employee")

    @property
    def skills(self) -> list[str]:
        """Return skills as Python list."""
        try:
            return json.loads(self.skills_json or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @skills.setter
    def skills(self, value: list[str]) -> None:
        self.skills_json = json.dumps(value)

    @property
    def availability(self) -> dict[str, bool]:
        """Return availability as Python dict."""
        try:
            return json.loads(self.availability_json or "{}")
        except (json.JSONDecodeError, TypeError):
            return {}

    @availability.setter
    def availability(self, value: dict[str, bool]) -> None:
        self.availability_json = json.dumps(value)

    def is_available_on(self, day_name: str) -> bool:
        """Check if employee is available on a given weekday name."""
        return self.availability.get(day_name.lower(), True)

    def __repr__(self) -> str:
        return f"<Employee id={self.id} name={self.name!r} role={self.role!r} type={self.roster_type!r}>"
