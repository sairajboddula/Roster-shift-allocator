"""What-if simulation endpoint - runs scheduling engine without persisting."""
from datetime import date
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.dependencies import DBSession
from app.services.scheduling_service import SchedulingService

router = APIRouter()


class SimulationRequest(BaseModel):
    roster_type: str
    start_date: date
    end_date: date
    department_ids: Optional[list[int]] = None


@router.post("/")
def run_simulation(payload: SimulationRequest, db: DBSession):
    """
    Run the full AI scheduling pipeline in simulation mode.
    Results are NOT saved to the database.
    """
    svc = SchedulingService(db)
    return svc.simulate_schedule(
        roster_type=payload.roster_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        department_ids=payload.department_ids,
    )
