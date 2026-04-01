"""Schedule generation, retrieval, override, and export endpoints."""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field
import io

from app.core.dependencies import DBSession
from app.core.auth_deps import CurrentUser
from app.services.scheduling_service import SchedulingService
from app.services.export_service import ExportService
from app.models.schedule import Schedule
from app.models.feedback import Feedback

router = APIRouter()


# ── Request / Response schemas ─────────────────────────────────────────────

class GenerateRequest(BaseModel):
    roster_type: str
    start_date: date
    end_date: date
    department_ids: Optional[list[int]] = None
    employee_ids: Optional[list[int]] = None


class OverrideRequest(BaseModel):
    employee_id: int
    department_id: int
    shift_key: str
    schedule_date: date
    roster_type: str
    reason: str = "Manual override by manager"


class FeedbackRequest(BaseModel):
    schedule_id: int
    employee_id: int
    roster_type: str
    rating: int = Field(..., ge=1, le=5)
    comment: str = ""
    is_conflict_report: bool = False


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/generate")
def generate_schedule(payload: GenerateRequest, db: DBSession, current_user: CurrentUser):
    """Run the AI scheduling engine and persist results."""
    svc = SchedulingService(db, current_user.id)
    return svc.generate_schedule(
        roster_type=payload.roster_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        department_ids=payload.department_ids,
        employee_ids=payload.employee_ids,
    )


@router.get("/")
def list_schedules(
    db: DBSession,
    current_user: CurrentUser,
    roster_type: str = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    department_id: Optional[int] = Query(None),
    employee_id: Optional[int] = Query(None),
    batch_id: Optional[str] = Query(None),
):
    """Fetch schedules for the current user with optional filters."""
    from sqlalchemy import and_
    from app.models.employee import Employee
    from app.models.department import Department
    from app.models.shift import Shift

    q = (
        db.query(Schedule, Employee, Department, Shift)
        .join(Employee, Schedule.employee_id == Employee.id)
        .join(Department, Schedule.department_id == Department.id)
        .join(Shift, Schedule.shift_id == Shift.id)
        .filter(and_(
            Schedule.roster_type == roster_type,
            Schedule.schedule_date >= start_date,
            Schedule.schedule_date <= end_date,
            Employee.user_id == current_user.id,
        ))
    )
    if department_id:
        q = q.filter(Schedule.department_id == department_id)
    if employee_id:
        q = q.filter(Schedule.employee_id == employee_id)
    if batch_id:
        q = q.filter(Schedule.generation_batch == batch_id)

    q = q.order_by(Schedule.schedule_date, Department.name, Employee.name)
    results = []
    for sched, emp, dept, shift in q.all():
        results.append({
            "id": sched.id,
            "date": sched.schedule_date.isoformat(),
            "employee_id": emp.id,
            "employee_name": emp.name,
            "role": emp.role,
            "department_id": dept.id,
            "department_name": dept.name,
            "shift_key": shift.shift_key,
            "shift_name": shift.name,
            "shift_start": shift.start_time,
            "shift_end": shift.end_time,
            "color": shift.color_hex,
            "ai_score": sched.ai_score,
            "reason": sched.reason,
            "is_manual_override": sched.is_manual_override,
            "is_confirmed": sched.is_confirmed,
            "batch_id": sched.generation_batch,
        })
    return results


@router.post("/override", status_code=201)
def manual_override(payload: OverrideRequest, db: DBSession, current_user: CurrentUser):
    """Manually assign an employee to a shift (manager override)."""
    from app.models.shift import Shift as ShiftModel
    from app.models.employee import Employee
    from app.core.exceptions import NotFoundException, ValidationException

    # Verify the employee belongs to the current user
    emp = db.query(Employee).filter(
        Employee.id == payload.employee_id,
        Employee.user_id == current_user.id,
    ).first()
    if not emp:
        raise ValidationException("Employee not found or does not belong to your account.")

    shift = db.query(ShiftModel).filter_by(
        shift_key=payload.shift_key, roster_type=payload.roster_type
    ).first()
    if not shift:
        raise NotFoundException("Shift", payload.shift_key)

    sched = Schedule(
        employee_id=payload.employee_id,
        department_id=payload.department_id,
        shift_id=shift.id,
        schedule_date=payload.schedule_date,
        roster_type=payload.roster_type,
        ai_score=1.0,
        reason=payload.reason,
        is_manual_override=True,
        is_confirmed=True,
    )
    db.add(sched)
    db.commit()
    db.refresh(sched)
    return {"id": sched.id, "message": "Manual override saved."}


@router.patch("/{schedule_id}/confirm")
def confirm_schedule(schedule_id: int, db: DBSession, current_user: CurrentUser):
    """Mark a schedule entry as confirmed."""
    from app.models.employee import Employee
    from app.core.exceptions import NotFoundException

    sched = (
        db.query(Schedule)
        .join(Employee, Schedule.employee_id == Employee.id)
        .filter(Schedule.id == schedule_id, Employee.user_id == current_user.id)
        .first()
    )
    if not sched:
        raise NotFoundException("Schedule", schedule_id)
    sched.is_confirmed = True
    db.commit()
    return {"message": "Confirmed."}


@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: int, db: DBSession, current_user: CurrentUser):
    """Delete a schedule entry."""
    from app.models.employee import Employee
    from app.core.exceptions import NotFoundException

    sched = (
        db.query(Schedule)
        .join(Employee, Schedule.employee_id == Employee.id)
        .filter(Schedule.id == schedule_id, Employee.user_id == current_user.id)
        .first()
    )
    if not sched:
        raise NotFoundException("Schedule", schedule_id)
    db.delete(sched)
    db.commit()


@router.post("/feedback", status_code=201)
def submit_feedback(payload: FeedbackRequest, db: DBSession, current_user: CurrentUser):
    """Submit feedback for a schedule assignment."""
    fb = Feedback(
        schedule_id=payload.schedule_id,
        employee_id=payload.employee_id,
        roster_type=payload.roster_type,
        rating=payload.rating,
        comment=payload.comment,
        is_conflict_report=payload.is_conflict_report,
    )
    db.add(fb)
    db.commit()
    return {"message": "Feedback submitted.", "id": fb.id}


@router.get("/export/csv")
def export_csv(
    db: DBSession,
    current_user: CurrentUser,
    roster_type: str = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    batch_id: Optional[str] = Query(None),
):
    """Download schedule as CSV."""
    svc = ExportService(db, current_user.id)
    csv_data = svc.export_csv(roster_type, start_date, end_date, batch_id)
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=roster_{roster_type}_{start_date}.csv"},
    )


@router.get("/export/excel")
def export_excel(
    db: DBSession,
    current_user: CurrentUser,
    roster_type: str = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    batch_id: Optional[str] = Query(None),
):
    """Download schedule as Excel workbook."""
    svc = ExportService(db, current_user.id)
    excel_bytes = svc.export_excel(roster_type, start_date, end_date, batch_id)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=roster_{roster_type}_{start_date}.xlsx"},
    )
