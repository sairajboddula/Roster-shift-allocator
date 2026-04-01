"""CRUD service for Department records."""
from sqlalchemy.orm import Session
from app.models.department import Department
from app.core.exceptions import NotFoundException, ValidationException
from app.utils.validators import validate_roster_type
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DepartmentService:

    def __init__(self, db: Session):
        self.db = db

    def list_departments(
        self,
        roster_type: str | None = None,
        active_only: bool = True,
    ) -> list[Department]:
        q = self.db.query(Department)
        if roster_type:
            q = q.filter_by(roster_type=validate_roster_type(roster_type))
        if active_only:
            q = q.filter_by(is_active=True)
        return q.order_by(Department.name).all()

    def get_department(self, dept_id: int) -> Department:
        dept = self.db.query(Department).filter_by(id=dept_id).first()
        if not dept:
            raise NotFoundException("Department", dept_id)
        return dept

    def create_department(self, data: dict) -> Department:
        roster_type = validate_roster_type(data.get("roster_type", ""))
        dept = Department(
            name=data["name"],
            roster_type=roster_type,
            description=data.get("description", ""),
            required_staff_morning=data.get("required_staff_morning", 2),
            required_staff_evening=data.get("required_staff_evening", 2),
            required_staff_night=data.get("required_staff_night", 1),
            rotation_priority=data.get("rotation_priority", 3),
            is_active=data.get("is_active", True),
        )
        dept.shift_types = data.get("shift_types", ["morning", "evening", "night"])
        dept.required_skills = data.get("required_skills", [])
        dept.tech_stack = data.get("tech_stack", [])
        self.db.add(dept)
        self.db.commit()
        self.db.refresh(dept)
        logger.info("Created department: %s (id=%d)", dept.name, dept.id)
        return dept

    def update_department(self, dept_id: int, data: dict) -> Department:
        dept = self.get_department(dept_id)
        allowed = {
            "name", "description", "required_staff_morning",
            "required_staff_evening", "required_staff_night",
            "rotation_priority", "is_active",
        }
        for k, v in data.items():
            if k in allowed:
                setattr(dept, k, v)
        if "shift_types" in data:
            dept.shift_types = data["shift_types"]
        if "required_skills" in data:
            dept.required_skills = data["required_skills"]
        if "tech_stack" in data:
            dept.tech_stack = data["tech_stack"]
        self.db.commit()
        self.db.refresh(dept)
        return dept

    def delete_department(self, dept_id: int) -> None:
        dept = self.get_department(dept_id)
        dept.is_active = False
        self.db.commit()
        logger.info("Soft-deleted department id=%d", dept_id)
