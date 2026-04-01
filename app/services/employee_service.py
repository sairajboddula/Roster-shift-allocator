"""CRUD service for Employee records — scoped per authenticated user."""
from sqlalchemy.orm import Session
from app.models.employee import Employee
from app.core.exceptions import NotFoundException, ValidationException
from app.utils.validators import validate_roster_type, validate_role_for_domain
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmployeeService:

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def _q(self):
        """Base query scoped to this user's employees."""
        return self.db.query(Employee).filter(Employee.user_id == self.user_id)

    def list_employees(
        self,
        roster_type: str | None = None,
        role: str | None = None,
        active_only: bool = True,
    ) -> list[Employee]:
        q = self._q()
        if roster_type:
            q = q.filter(Employee.roster_type == validate_roster_type(roster_type))
        if role:
            q = q.filter(Employee.role == role.lower())
        if active_only:
            q = q.filter(Employee.is_active == True)
        return q.order_by(Employee.name).all()

    def get_employee(self, employee_id: int) -> Employee:
        emp = self._q().filter(Employee.id == employee_id).first()
        if not emp:
            raise NotFoundException("Employee", employee_id)
        return emp

    def create_employee(self, data: dict) -> Employee:
        roster_type = validate_roster_type(data.get("roster_type", ""))
        role = validate_role_for_domain(data.get("role", ""), roster_type)

        existing = self._q().filter(Employee.email == data.get("email", "")).first()
        if existing:
            raise ValidationException(f"You already have an employee with email '{data['email']}'.")

        emp = Employee(
            user_id=self.user_id,
            name=data["name"],
            email=data["email"],
            role=role,
            roster_type=roster_type,
            max_shifts_per_week=data.get("max_shifts_per_week", 5),
            experience_years=data.get("experience_years", 1.0),
            department_id=data.get("department_id"),
            is_active=data.get("is_active", True),
        )
        emp.skills = data.get("skills", [])
        emp.availability = data.get("availability", {
            "monday": True, "tuesday": True, "wednesday": True,
            "thursday": True, "friday": True, "saturday": False, "sunday": False,
        })
        self.db.add(emp)
        self.db.commit()
        self.db.refresh(emp)
        logger.info("Created employee: %s (id=%d) for user_id=%d", emp.name, emp.id, self.user_id)
        return emp

    def update_employee(self, employee_id: int, data: dict) -> Employee:
        emp = self.get_employee(employee_id)
        allowed = {
            "name", "email", "role", "max_shifts_per_week",
            "experience_years", "department_id", "is_active",
        }
        for field_name, value in data.items():
            if field_name in allowed:
                setattr(emp, field_name, value)
        if "skills" in data:
            emp.skills = data["skills"]
        if "availability" in data:
            emp.availability = data["availability"]
        self.db.commit()
        self.db.refresh(emp)
        return emp

    def delete_employee(self, employee_id: int) -> None:
        emp = self.get_employee(employee_id)
        emp.is_active = False
        self.db.commit()
        logger.info("Soft-deleted employee id=%d (user_id=%d)", employee_id, self.user_id)

    def get_workload_summary(self, roster_type: str, days: int = 30) -> list[dict]:
        """Return shift count per employee in the last N days."""
        from datetime import date, timedelta
        from app.models.schedule import Schedule

        since = date.today() - timedelta(days=days)
        employees = self.list_employees(roster_type=roster_type)
        result = []
        for emp in employees:
            count = (
                self.db.query(Schedule)
                .filter(
                    Schedule.employee_id == emp.id,
                    Schedule.schedule_date >= since,
                )
                .count()
            )
            result.append({
                "employee_id": emp.id,
                "name": emp.name,
                "role": emp.role,
                "shift_count": count,
            })
        result.sort(key=lambda x: x["shift_count"], reverse=True)
        return result
