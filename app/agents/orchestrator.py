"""
SchedulingOrchestrator - chains all agents in the correct order.

Pipeline:
  LearningAgent → AvailabilityAgent → RotationAgent
      → OptimizationAgent → ConflictAgent

Returns a final list of Assignment objects and a conflict report.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.agents.availability_agent import AvailabilityAgent, AvailabilityInput
from app.agents.rotation_agent import RotationAgent, RotationInput
from app.agents.optimization_agent import (
    OptimizationAgent, OptimizationInput, OptimizationOutput, ShiftSlot, Assignment
)
from app.agents.conflict_agent import ConflictAgent, ConflictInput, ConflictRecord
from app.agents.learning_agent import LearningAgent, LearningInput

from app.models.employee import Employee
from app.models.department import Department
from app.models.shift import Shift
from app.models.history import History
from app.models.feedback import Feedback
from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class OrchestratorInput:
    roster_type: str
    start_date: date
    end_date: date
    employees: list[Employee]
    departments: list[Department]
    shifts: list[Shift]
    history_records: list[History]
    feedback_records: list[Feedback]
    # Optional: pre-existing assignments in the period (for rest checking)
    existing_assignments: dict[int, list[tuple[date, str]]] = field(default_factory=dict)


@dataclass
class OrchestratorResult:
    assignments: list[Assignment]
    conflicts: list[ConflictRecord]
    removed_count: int
    unfilled_slots: list[ShiftSlot]
    learning_insights: list[str]
    stats: dict


class SchedulingOrchestrator:
    """Chains all AI agents and returns a complete schedule."""

    def __init__(self):
        self.availability_agent = AvailabilityAgent()
        self.rotation_agent = RotationAgent()
        self.optimization_agent = OptimizationAgent()
        self.conflict_agent = ConflictAgent()
        self.learning_agent = LearningAgent()

    def run(self, inp: OrchestratorInput) -> OrchestratorResult:
        logger.info(
            "Orchestrator start: type=%s, %s → %s, employees=%d, depts=%d",
            inp.roster_type, inp.start_date, inp.end_date, len(inp.employees), len(inp.departments),
        )
        date_range = self._date_range(inp.start_date, inp.end_date)

        # ----------------------------------------------------------------
        # Step 1: Learning Agent
        # ----------------------------------------------------------------
        learning_out = self.learning_agent.run(LearningInput(
            roster_type=inp.roster_type,
            history_records=inp.history_records,
            feedback_records=inp.feedback_records,
            employee_ids=[e.id for e in inp.employees],
            reference_date=inp.end_date,
        ))
        logger.debug("Learning: %d insights", len(learning_out.insight_summary))

        # ----------------------------------------------------------------
        # Step 2: Availability Agent
        # ----------------------------------------------------------------
        min_rest = (
            settings.DEFAULT_REST_HOURS_MEDICAL
            if inp.roster_type == "medical"
            else settings.DEFAULT_REST_HOURS_IT
        )
        availability_out = self.availability_agent.run(AvailabilityInput(
            roster_type=inp.roster_type,
            employees=inp.employees,
            shifts=inp.shifts,
            target_dates=date_range,
            existing_assignments=inp.existing_assignments,
            min_rest_hours=min_rest,
        ))
        logger.debug("Availability: matrix built for %d dates", len(date_range))

        # ----------------------------------------------------------------
        # Step 3: Rotation Agent
        # ----------------------------------------------------------------
        rotation_out = self.rotation_agent.run(RotationInput(
            roster_type=inp.roster_type,
            employees=inp.employees,
            departments=inp.departments,
            history_records=inp.history_records,
        ))
        logger.debug("Rotation scores computed.")

        # ----------------------------------------------------------------
        # Step 4: Build slots
        # ----------------------------------------------------------------
        slots = self._build_slots(inp.departments, inp.shifts, date_range, inp.roster_type)
        logger.debug("Slots to fill: %d", len(slots))

        # ----------------------------------------------------------------
        # Step 5: Optimization Agent
        # ----------------------------------------------------------------
        w_rotation = (
            settings.MEDICAL_ROTATION_WEIGHT if inp.roster_type == "medical"
            else settings.IT_SKILL_WEIGHT
        )
        w_workload = (
            settings.MEDICAL_FAIRNESS_WEIGHT if inp.roster_type == "medical"
            else settings.IT_WORKLOAD_WEIGHT
        )
        w_avail = (
            settings.MEDICAL_AVAILABILITY_WEIGHT if inp.roster_type == "medical"
            else settings.IT_AVAILABILITY_WEIGHT
        )
        w_fairness = (
            settings.MEDICAL_FAIRNESS_WEIGHT if inp.roster_type == "medical"
            else settings.IT_WEEKEND_WEIGHT
        )

        optim_out: OptimizationOutput = self.optimization_agent.run(OptimizationInput(
            roster_type=inp.roster_type,
            employees=inp.employees,
            departments=inp.departments,
            shifts=inp.shifts,
            slots=slots,
            availability_matrix=availability_out.availability_matrix,
            rotation_scores=rotation_out.rotation_scores,
            current_workload={e.id: 0 for e in inp.employees},
            learning_weights=learning_out.employee_weights,
            weight_rotation=w_rotation,
            weight_skill=w_rotation,
            weight_workload=w_workload,
            weight_availability=w_avail,
            weight_fairness=w_fairness,
        ))
        logger.info("Optimization: %d assignments, %d unfilled", len(optim_out.assignments), len(optim_out.unfilled_slots))

        # ----------------------------------------------------------------
        # Step 6: Conflict Agent
        # ----------------------------------------------------------------
        max_consec = (
            settings.MAX_CONSECUTIVE_NIGHTS_MEDICAL if inp.roster_type == "medical"
            else settings.MAX_CONSECUTIVE_NIGHTS_IT
        )
        max_weekly = (
            settings.MAX_SHIFTS_PER_WEEK_MEDICAL if inp.roster_type == "medical"
            else settings.MAX_SHIFTS_PER_WEEK_IT
        )
        conflict_out = self.conflict_agent.run(ConflictInput(
            roster_type=inp.roster_type,
            assignments=optim_out.assignments,
            shifts_by_key={s.shift_key: s for s in inp.shifts},
            min_rest_hours=min_rest,
            max_consecutive_nights=max_consec,
            max_shifts_per_week=max_weekly,
        ))
        logger.info(
            "Conflicts: %d detected, %d removed",
            len(conflict_out.conflicts), conflict_out.removed_count,
        )

        stats = {
            "total_assignments": len(conflict_out.clean_assignments),
            "total_conflicts": len(conflict_out.conflicts),
            "removed_count": conflict_out.removed_count,
            "unfilled_slots": len(optim_out.unfilled_slots),
            "date_range_days": len(date_range),
            "employees_scheduled": len({a.employee_id for a in conflict_out.clean_assignments}),
        }

        return OrchestratorResult(
            assignments=conflict_out.clean_assignments,
            conflicts=conflict_out.conflicts,
            removed_count=conflict_out.removed_count,
            unfilled_slots=optim_out.unfilled_slots,
            learning_insights=learning_out.insight_summary,
            stats=stats,
        )

    @staticmethod
    def _date_range(start: date, end: date) -> list[date]:
        days = (end - start).days + 1
        return [start + timedelta(days=i) for i in range(days)]

    @staticmethod
    def _build_slots(
        departments: list[Department],
        shifts: list[Shift],
        date_range: list[date],
        roster_type: str,
    ) -> list[ShiftSlot]:
        """Build one slot per (date, department, shift_type) combination."""
        shifts_by_key = {s.shift_key: s for s in shifts}
        slots: list[ShiftSlot] = []
        for d in date_range:
            for dept in departments:
                for shift_key in dept.shift_types:
                    shift = shifts_by_key.get(shift_key)
                    if shift is None:
                        continue
                    required = dept.get_required_staff(shift_key)
                    if required <= 0:
                        continue
                    slots.append(ShiftSlot(
                        target_date=d,
                        department_id=dept.id,
                        department_name=dept.name,
                        shift_key=shift_key,
                        required_count=required,
                    ))
        return slots
