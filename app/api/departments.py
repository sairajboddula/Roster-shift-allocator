"""Department API endpoints."""
from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.core.dependencies import DBSession
from app.services.department_service import DepartmentService

router = APIRouter()


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2)
    roster_type: str
    description: str = ""
    required_staff_morning: int = Field(2, ge=0)
    required_staff_evening: int = Field(2, ge=0)
    required_staff_night: int = Field(1, ge=0)
    shift_types: list[str] = ["morning", "evening", "night"]
    required_skills: list[str] = []
    tech_stack: list[str] = []
    rotation_priority: int = Field(3, ge=1, le=5)


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    required_staff_morning: Optional[int] = None
    required_staff_evening: Optional[int] = None
    required_staff_night: Optional[int] = None
    shift_types: Optional[list[str]] = None
    required_skills: Optional[list[str]] = None
    tech_stack: Optional[list[str]] = None
    rotation_priority: Optional[int] = None
    is_active: Optional[bool] = None


def _dept_out(dept) -> dict:
    return {
        "id": dept.id,
        "name": dept.name,
        "roster_type": dept.roster_type,
        "description": dept.description,
        "required_staff_morning": dept.required_staff_morning,
        "required_staff_evening": dept.required_staff_evening,
        "required_staff_night": dept.required_staff_night,
        "shift_types": dept.shift_types,
        "required_skills": dept.required_skills,
        "tech_stack": dept.tech_stack,
        "rotation_priority": dept.rotation_priority,
        "is_active": dept.is_active,
    }


@router.get("/")
def list_departments(
    db: DBSession,
    roster_type: Optional[str] = Query(None),
    active_only: bool = Query(True),
):
    svc = DepartmentService(db)
    return [_dept_out(d) for d in svc.list_departments(roster_type=roster_type, active_only=active_only)]


@router.get("/{dept_id}")
def get_department(dept_id: int, db: DBSession):
    return _dept_out(DepartmentService(db).get_department(dept_id))


@router.post("/", status_code=201)
def create_department(payload: DepartmentCreate, db: DBSession):
    dept = DepartmentService(db).create_department(payload.model_dump())
    return _dept_out(dept)


@router.put("/{dept_id}")
def update_department(dept_id: int, payload: DepartmentUpdate, db: DBSession):
    updated = DepartmentService(db).update_department(dept_id, payload.model_dump(exclude_none=True))
    return _dept_out(updated)


@router.delete("/{dept_id}", status_code=204)
def delete_department(dept_id: int, db: DBSession):
    DepartmentService(db).delete_department(dept_id)


@router.patch("/{dept_id}/toggle")
def toggle_department(dept_id: int, db: DBSession):
    """Flip the is_active flag on a department. Returns the updated record."""
    svc = DepartmentService(db)
    dept = svc.get_department(dept_id)
    updated = svc.update_department(dept_id, {"is_active": not dept.is_active})
    return _dept_out(updated)


@router.get("/all/list")
def list_all_departments(
    db: DBSession,
    roster_type: Optional[str] = Query(None),
):
    """Return ALL departments including inactive (for the toggle management UI)."""
    svc = DepartmentService(db)
    return [_dept_out(d) for d in svc.list_departments(roster_type=roster_type, active_only=False)]
