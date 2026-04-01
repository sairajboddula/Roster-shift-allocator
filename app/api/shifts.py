"""Shift definition endpoints."""
from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.core.dependencies import DBSession
from app.models.shift import Shift

router = APIRouter()


class ShiftCreate(BaseModel):
    name: str
    shift_key: str
    roster_type: str
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    duration_hours: float = Field(..., gt=0)
    is_night_shift: bool = False
    is_emergency: bool = False
    on_call: bool = False
    color_hex: str = "#3B82F6"


def _shift_out(s: Shift) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "shift_key": s.shift_key,
        "roster_type": s.roster_type,
        "start_time": s.start_time,
        "end_time": s.end_time,
        "duration_hours": s.duration_hours,
        "is_night_shift": s.is_night_shift,
        "is_emergency": s.is_emergency,
        "on_call": s.on_call,
        "color_hex": s.color_hex,
    }


@router.get("/")
def list_shifts(
    db: DBSession,
    roster_type: Optional[str] = Query(None),
):
    q = db.query(Shift)
    if roster_type:
        q = q.filter_by(roster_type=roster_type)
    return [_shift_out(s) for s in q.all()]


@router.get("/{shift_id}")
def get_shift(shift_id: int, db: DBSession):
    shift = db.query(Shift).filter_by(id=shift_id).first()
    if not shift:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Shift", shift_id)
    return _shift_out(shift)


@router.post("/", status_code=201)
def create_shift(payload: ShiftCreate, db: DBSession):
    shift = Shift(**payload.model_dump())
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return _shift_out(shift)
