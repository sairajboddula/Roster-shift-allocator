"""Employee API endpoints."""
from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.core.dependencies import DBSession
from app.core.auth_deps import CurrentUser
from app.services.employee_service import EmployeeService

router = APIRouter()


class EmployeeCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5)
    role: str
    roster_type: str
    skills: list[str] = []
    availability: dict[str, bool] = {}
    max_shifts_per_week: int = Field(5, ge=1, le=7)
    experience_years: float = Field(1.0, ge=0.0)
    department_id: Optional[int] = None


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    skills: Optional[list[str]] = None
    availability: Optional[dict[str, bool]] = None
    max_shifts_per_week: Optional[int] = None
    experience_years: Optional[float] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None


def _emp_out(emp) -> dict:
    return {
        "id": emp.id,
        "name": emp.name,
        "email": emp.email,
        "role": emp.role,
        "roster_type": emp.roster_type,
        "skills": emp.skills,
        "availability": emp.availability,
        "max_shifts_per_week": emp.max_shifts_per_week,
        "experience_years": emp.experience_years,
        "department_id": emp.department_id,
        "is_active": emp.is_active,
    }


@router.get("/")
def list_employees(
    db: DBSession,
    current_user: CurrentUser,
    roster_type: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    active_only: bool = Query(True),
):
    """List employees, optionally filtered by domain and role."""
    svc = EmployeeService(db, current_user.id)
    employees = svc.list_employees(roster_type=roster_type, role=role, active_only=active_only)
    return [_emp_out(e) for e in employees]


@router.get("/workload")
def get_workload(
    db: DBSession,
    current_user: CurrentUser,
    roster_type: str = Query(...),
    days: int = Query(30, ge=7, le=365),
):
    """Return shift counts per employee in the last N days."""
    svc = EmployeeService(db, current_user.id)
    return svc.get_workload_summary(roster_type=roster_type, days=days)


@router.get("/{employee_id}")
def get_employee(employee_id: int, db: DBSession, current_user: CurrentUser):
    svc = EmployeeService(db, current_user.id)
    return _emp_out(svc.get_employee(employee_id))


@router.post("/", status_code=201)
def create_employee(payload: EmployeeCreate, db: DBSession, current_user: CurrentUser):
    svc = EmployeeService(db, current_user.id)
    emp = svc.create_employee(payload.model_dump())
    return _emp_out(emp)


@router.put("/{employee_id}")
def update_employee(employee_id: int, payload: EmployeeUpdate, db: DBSession, current_user: CurrentUser):
    svc = EmployeeService(db, current_user.id)
    updated = svc.update_employee(employee_id, payload.model_dump(exclude_none=True))
    return _emp_out(updated)


@router.delete("/{employee_id}", status_code=204)
def delete_employee(employee_id: int, db: DBSession, current_user: CurrentUser):
    EmployeeService(db, current_user.id).delete_employee(employee_id)
