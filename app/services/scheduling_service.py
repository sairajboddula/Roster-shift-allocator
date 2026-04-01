"""
SchedulingService - bridges the API layer with the orchestrator.

Responsibilities:
  1. Load required data from DB.
  2. Invoke the SchedulingOrchestrator.
  3. Persist results to the Schedule table.
  4. Update History table.
  5. Return serialisable output.
"""
import uuid
from datetime import date
from dataclasses import asdict

from sqlalchemy.orm import Session

from app.agents.orchestrator import SchedulingOrchestrator, OrchestratorInput, OrchestratorResult
from app.models.employee import Employee
from app.models.department import Department
from app.models.shift import Shift
from app.models.schedule import Schedule
from app.models.history import History
from app.models.feedback import Feedback
from app.core.exceptions import ValidationException
from app.utils.validators import validate_roster_type, validate_date_range
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SchedulingService:
    """Orchestrates the full scheduling pipeline for one roster_type and date range."""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.orchestrator = SchedulingOrchestrator()

    def generate_schedule(
        self,
        roster_type: str,
        start_date: date,
        end_date: date,
        department_ids: list[int] | None = None,
        employee_ids: list[int] | None = None,
    ) -> dict:
        """
        Generate and persist a new schedule.
        Returns a summary dict with assignments and stats.
        """
        roster_type = validate_roster_type(roster_type)
        validate_date_range(start_date, end_date)

        # Load data
        employees = self._load_employees(roster_type, employee_ids)
        departments = self._load_departments(roster_type, department_ids)
        shifts = self._load_shifts(roster_type)

        if not employees:
            raise ValidationException(f"No active employees found for roster_type='{roster_type}'.")
        if not departments:
            raise ValidationException(f"No active departments found for roster_type='{roster_type}'.")

        history_records = self._load_history(roster_type)
        feedback_records = self._load_feedback(roster_type)
        existing_assignments = self._load_existing_assignments(roster_type, start_date, end_date)

        # Run orchestrator
        result: OrchestratorResult = self.orchestrator.run(OrchestratorInput(
            roster_type=roster_type,
            start_date=start_date,
            end_date=end_date,
            employees=employees,
            departments=departments,
            shifts=shifts,
            history_records=history_records,
            feedback_records=feedback_records,
            existing_assignments=existing_assignments,
        ))

        # Persist to DB
        batch_id = str(uuid.uuid4())[:8]
        shift_map = {s.shift_key: s for s in shifts}
        saved_schedules = self._persist_schedules(result, batch_id, roster_type, shift_map)
        self._update_history(result, roster_type, start_date, end_date)

        return {
            "batch_id": batch_id,
            "roster_type": roster_type,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "stats": result.stats,
            "assignments": [self._assignment_to_dict(a, shift_map) for a in result.assignments],
            "conflicts": [
                {
                    "type": c.conflict_type,
                    "description": c.description,
                    "resolved": c.auto_resolved,
                    "note": c.resolution_note,
                }
                for c in result.conflicts
            ],
            "unfilled_slots": len(result.unfilled_slots),
            "learning_insights": result.learning_insights,
        }

    def simulate_schedule(
        self,
        roster_type: str,
        start_date: date,
        end_date: date,
        department_ids: list[int] | None = None,
    ) -> dict:
        """Run scheduling pipeline but do NOT persist results. Returns preview."""
        roster_type = validate_roster_type(roster_type)
        validate_date_range(start_date, end_date)

        employees = self._load_employees(roster_type, None)
        departments = self._load_departments(roster_type, department_ids)
        shifts = self._load_shifts(roster_type)

        if not employees or not departments:
            raise ValidationException("Insufficient data for simulation.")

        result: OrchestratorResult = self.orchestrator.run(OrchestratorInput(
            roster_type=roster_type,
            start_date=start_date,
            end_date=end_date,
            employees=employees,
            departments=departments,
            shifts=shifts,
            history_records=self._load_history(roster_type),
            feedback_records=self._load_feedback(roster_type),
        ))

        shift_map = {s.shift_key: s for s in shifts}
        return {
            "is_simulation": True,
            "roster_type": roster_type,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "stats": result.stats,
            "assignments": [self._assignment_to_dict(a, shift_map) for a in result.assignments],
            "conflicts": [
                {"type": c.conflict_type, "description": c.description}
                for c in result.conflicts
            ],
            "learning_insights": result.learning_insights,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_employees(self, roster_type: str, ids: list[int] | None) -> list[Employee]:
        q = self.db.query(Employee).filter(
            Employee.roster_type == roster_type,
            Employee.is_active == True,
            Employee.user_id == self.user_id,
        )
        if ids:
            q = q.filter(Employee.id.in_(ids))
        return q.all()

    def _load_departments(self, roster_type: str, ids: list[int] | None) -> list[Department]:
        q = self.db.query(Department).filter_by(roster_type=roster_type, is_active=True)
        if ids:
            q = q.filter(Department.id.in_(ids))
        return q.all()

    def _load_shifts(self, roster_type: str) -> list[Shift]:
        return self.db.query(Shift).filter_by(roster_type=roster_type).all()

    def _load_history(self, roster_type: str) -> list[History]:
        return (
            self.db.query(History)
            .join(Employee, History.employee_id == Employee.id)
            .filter(History.roster_type == roster_type, Employee.user_id == self.user_id)
            .all()
        )

    def _load_feedback(self, roster_type: str) -> list[Feedback]:
        return (
            self.db.query(Feedback)
            .join(Employee, Feedback.employee_id == Employee.id)
            .filter(Feedback.roster_type == roster_type, Employee.user_id == self.user_id)
            .all()
        )

    def _load_existing_assignments(
        self, roster_type: str, start_date: date, end_date: date
    ) -> dict[int, list[tuple[date, str]]]:
        """Load existing schedule entries in the period for rest-period checks."""
        from app.models.schedule import Schedule as ScheduleModel
        from sqlalchemy import and_

        rows = (
            self.db.query(ScheduleModel)
            .join(Employee, ScheduleModel.employee_id == Employee.id)
            .join(Shift, ScheduleModel.shift_id == Shift.id)
            .filter(
                and_(
                    ScheduleModel.roster_type == roster_type,
                    ScheduleModel.schedule_date >= start_date,
                    ScheduleModel.schedule_date <= end_date,
                    Employee.user_id == self.user_id,
                )
            )
            .all()
        )
        result: dict[int, list[tuple[date, str]]] = {}
        for row in rows:
            shift = self.db.query(Shift).get(row.shift_id)
            if shift:
                result.setdefault(row.employee_id, []).append((row.schedule_date, shift.shift_key))
        return result

    def _persist_schedules(
        self,
        result: OrchestratorResult,
        batch_id: str,
        roster_type: str,
        shift_map: dict,
    ) -> list[Schedule]:
        saved = []
        for a in result.assignments:
            shift = shift_map.get(a.shift_key)
            if shift is None:
                continue
            sched = Schedule(
                employee_id=a.employee_id,
                department_id=a.department_id,
                shift_id=shift.id,
                schedule_date=a.target_date,
                roster_type=roster_type,
                ai_score=a.ai_score,
                reason=a.reason,
                rotation_score=a.rotation_score,
                skill_score=a.skill_score,
                workload_score=a.workload_score,
                generation_batch=batch_id,
                is_manual_override=False,
                is_confirmed=False,
            )
            self.db.add(sched)
            saved.append(sched)
        self.db.commit()
        logger.info("Persisted %d schedule rows (batch=%s).", len(saved), batch_id)
        return saved

    def _update_history(
        self,
        result: OrchestratorResult,
        roster_type: str,
        start_date: date,
        end_date: date,
    ) -> None:
        """Aggregate assignments into History rows."""
        from collections import defaultdict

        # {(emp_id, dept_id): {"total": int, "night": int}}
        agg: dict[tuple[int, int], dict] = defaultdict(lambda: {"total": 0, "night": 0, "scores": []})
        shift_night_keys = {"night", "night_support"}

        for a in result.assignments:
            key = (a.employee_id, a.department_id)
            agg[key]["total"] += 1
            if a.shift_key in shift_night_keys:
                agg[key]["night"] += 1
            agg[key]["scores"].append(a.ai_score)

        for (emp_id, dept_id), data in agg.items():
            avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0.0
            hist = History(
                employee_id=emp_id,
                department_id=dept_id,
                roster_type=roster_type,
                period_start=start_date,
                period_end=end_date,
                total_shifts=data["total"],
                night_shifts=data["night"],
                avg_score=avg_score,
            )
            self.db.add(hist)
        self.db.commit()

    @staticmethod
    def _assignment_to_dict(a, shift_map: dict) -> dict:
        shift = shift_map.get(a.shift_key)
        return {
            "date": a.target_date.isoformat(),
            "employee_id": a.employee_id,
            "employee_name": a.employee_name,
            "department_id": a.department_id,
            "department_name": a.department_name,
            "shift_key": a.shift_key,
            "shift_name": shift.name if shift else a.shift_key,
            "shift_start": shift.start_time if shift else "",
            "shift_end": shift.end_time if shift else "",
            "ai_score": round(a.ai_score, 3),
            "reason": a.reason,
        }
