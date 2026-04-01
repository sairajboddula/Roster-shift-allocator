"""Department SQLAlchemy model."""
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text

from app.db.database import Base


class Department(Base):
    """Represents a department (ward/team) in Medical or IT domain."""

    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    roster_type = Column(String(20), nullable=False, index=True)  # medical | it
    description = Column(Text, default="")

    # Required staff count per shift
    required_staff_morning = Column(Integer, default=2)
    required_staff_evening = Column(Integer, default=2)
    required_staff_night = Column(Integer, default=1)

    # Shift types available in this department (JSON array)
    # Medical: ["morning", "evening", "night", "emergency"]
    # IT: ["general", "night_support", "on_call"]
    shift_types_json = Column(Text, default='["morning", "evening", "night"]')

    # Required skills/roles for this department (JSON array)
    required_skills_json = Column(Text, default="[]")

    # For IT departments: tech stack tags
    tech_stack_json = Column(Text, default="[]")

    is_active = Column(Boolean, default=True)
    rotation_priority = Column(Integer, default=1)  # Higher = more important for rotation
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def shift_types(self) -> list[str]:
        try:
            return json.loads(self.shift_types_json or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @shift_types.setter
    def shift_types(self, value: list[str]) -> None:
        self.shift_types_json = json.dumps(value)

    @property
    def required_skills(self) -> list[str]:
        try:
            return json.loads(self.required_skills_json or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @required_skills.setter
    def required_skills(self, value: list[str]) -> None:
        self.required_skills_json = json.dumps(value)

    @property
    def tech_stack(self) -> list[str]:
        try:
            return json.loads(self.tech_stack_json or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @tech_stack.setter
    def tech_stack(self, value: list[str]) -> None:
        self.tech_stack_json = json.dumps(value)

    def get_required_staff(self, shift_type: str) -> int:
        """Get required staff count for a shift type."""
        mapping = {
            "morning": self.required_staff_morning,
            "general": self.required_staff_morning,
            "evening": self.required_staff_evening,
            "night": self.required_staff_night,
            "night_support": self.required_staff_night,
            "emergency": self.required_staff_morning,
            "on_call": 1,
        }
        return mapping.get(shift_type, 1)

    def __repr__(self) -> str:
        return f"<Department id={self.id} name={self.name!r} type={self.roster_type!r}>"
