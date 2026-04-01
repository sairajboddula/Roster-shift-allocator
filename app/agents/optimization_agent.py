"""
OptimizationAgent - scores and ranks candidate employees for each shift slot.

Uses domain-specific scoring weights:
  Medical: rotation(40%) + availability(30%) + rest(20%) + fairness(10%)
  IT:      skill_match(40%) + workload(30%) + availability(20%) + weekend(10%)

Implements greedy selection with optional backtracking on failure.
"""
from dataclasses import dataclass, field
from datetime import date

from app.agents.base_agent import BaseAgent, AgentInput, AgentOutput
from app.models.employee import Employee
from app.models.department import Department
from app.models.shift import Shift


@dataclass
class ScoredCandidate:
    """A scored employee-department-shift tuple."""
    employee_id: int
    employee_name: str
    total_score: float
    rotation_score: float
    skill_score: float
    workload_score: float
    availability_score: float
    reason: str


@dataclass
class ShiftSlot:
    """Represents one (date, department, shift_key) slot to fill."""
    target_date: date
    department_id: int
    department_name: str
    shift_key: str
    required_count: int


@dataclass
class OptimizationInput(AgentInput):
    employees: list[Employee] = field(default_factory=list)
    departments: list[Department] = field(default_factory=list)
    shifts: list[Shift] = field(default_factory=list)
    slots: list[ShiftSlot] = field(default_factory=list)

    # From AvailabilityAgent: {date_str: {shift_key: [employee_id, ...]}}
    availability_matrix: dict[str, dict[str, list[int]]] = field(default_factory=dict)

    # From RotationAgent: {employee_id: {department_id: score}}
    rotation_scores: dict[int, dict[int, float]] = field(default_factory=dict)

    # Current workload: {employee_id: shift_count_so_far}
    current_workload: dict[int, int] = field(default_factory=dict)

    # Learning weights modifier: {employee_id: float multiplier}
    learning_weights: dict[int, float] = field(default_factory=dict)

    # Domain weight overrides (optional)
    weight_rotation: float = 0.40
    weight_skill: float = 0.40
    weight_workload: float = 0.30
    weight_availability: float = 0.25
    weight_fairness: float = 0.10


@dataclass
class Assignment:
    """A single confirmed assignment produced by the optimizer."""
    target_date: date
    department_id: int
    department_name: str
    shift_key: str
    employee_id: int
    employee_name: str
    ai_score: float
    rotation_score: float
    skill_score: float
    workload_score: float
    reason: str


@dataclass
class OptimizationOutput(AgentOutput):
    assignments: list[Assignment] = field(default_factory=list)
    unfilled_slots: list[ShiftSlot] = field(default_factory=list)
    workload_snapshot: dict[int, int] = field(default_factory=dict)


class OptimizationAgent(BaseAgent[OptimizationInput, OptimizationOutput]):
    """Greedy scheduler with backtracking for unfilled slots."""

    def __init__(self):
        super().__init__("OptimizationAgent")

    def _validate(self, inp: OptimizationInput) -> None:
        if not inp.slots:
            raise ValueError("OptimizationAgent: no slots to fill.")

    def _process(self, inp: OptimizationInput) -> OptimizationOutput:
        # Index employees and departments
        emp_by_id: dict[int, Employee] = {e.id: e for e in inp.employees}
        dept_by_id: dict[int, Department] = {d.id: d for d in inp.departments}
        shifts_by_key: dict[str, Shift] = {s.shift_key: s for s in inp.shifts}

        workload = dict(inp.current_workload)
        assignments: list[Assignment] = []
        unfilled: list[ShiftSlot] = []

        # Sort slots: critical departments first (by rotation_priority desc)
        sorted_slots = sorted(
            inp.slots,
            key=lambda s: dept_by_id.get(s.department_id, type("D", (), {"rotation_priority": 0})()).rotation_priority,
            reverse=True,
        )

        for slot in sorted_slots:
            date_str = slot.target_date.isoformat()
            avail_ids = inp.availability_matrix.get(date_str, {}).get(slot.shift_key, [])
            if not avail_ids:
                unfilled.append(slot)
                continue

            # Score all available candidates
            candidates = self._score_candidates(
                avail_ids, slot, emp_by_id, dept_by_id, shifts_by_key,
                inp, workload,
            )
            candidates.sort(key=lambda c: c.total_score, reverse=True)

            filled_count = 0
            assigned_ids = set()

            for candidate in candidates:
                if filled_count >= slot.required_count:
                    break
                if candidate.employee_id in assigned_ids:
                    continue
                dept = dept_by_id.get(slot.department_id)
                assignments.append(Assignment(
                    target_date=slot.target_date,
                    department_id=slot.department_id,
                    department_name=slot.department_name,
                    shift_key=slot.shift_key,
                    employee_id=candidate.employee_id,
                    employee_name=candidate.employee_name,
                    ai_score=candidate.total_score,
                    rotation_score=candidate.rotation_score,
                    skill_score=candidate.skill_score,
                    workload_score=candidate.workload_score,
                    reason=candidate.reason,
                ))
                workload[candidate.employee_id] = workload.get(candidate.employee_id, 0) + 1
                assigned_ids.add(candidate.employee_id)
                filled_count += 1

            if filled_count < slot.required_count:
                # Partial fill - record remaining as unfilled
                for _ in range(slot.required_count - filled_count):
                    unfilled.append(slot)

        return OptimizationOutput(
            assignments=assignments,
            unfilled_slots=unfilled,
            workload_snapshot=workload,
        )

    def _score_candidates(
        self,
        avail_ids: list[int],
        slot: ShiftSlot,
        emp_by_id: dict[int, Employee],
        dept_by_id: dict[int, Department],
        shifts_by_key: dict[str, Shift],
        inp: OptimizationInput,
        current_workload: dict[int, int],
    ) -> list[ScoredCandidate]:
        """Compute domain-specific score for each available employee."""
        candidates: list[ScoredCandidate] = []
        max_workload = max(current_workload.values(), default=1) or 1

        for emp_id in avail_ids:
            emp = emp_by_id.get(emp_id)
            if emp is None:
                continue

            # Rotation / skill score (from RotationAgent output)
            rot_score = inp.rotation_scores.get(emp_id, {}).get(slot.department_id, 0.5)

            # Workload balance: lower workload = higher score
            emp_workload = current_workload.get(emp_id, 0)
            workload_score = 1.0 - (emp_workload / (max_workload + 1))

            # Availability score: 1.0 if available (they already passed the filter)
            avail_score = 1.0

            # Weekend fairness: slightly penalise if shift is weekend and employee already has weekend shifts
            is_weekend = slot.target_date.weekday() >= 5
            weekend_score = 0.8 if is_weekend and emp_workload > 2 else 1.0

            # Learning weight modifier
            learning_mod = inp.learning_weights.get(emp_id, 1.0)

            if inp.roster_type == "medical":
                total = (
                    inp.weight_rotation * rot_score
                    + inp.weight_availability * avail_score
                    + inp.weight_workload * workload_score
                    + inp.weight_fairness * (1.0 - emp_workload / (max_workload + 1))
                ) * learning_mod
                reason = self._build_medical_reason(emp, rot_score, workload_score, slot)
                skill_score = rot_score  # rotation IS the primary score for medical
            else:
                total = (
                    inp.weight_skill * rot_score  # skill score from rotation agent
                    + inp.weight_workload * workload_score
                    + inp.weight_availability * avail_score
                    + inp.weight_fairness * weekend_score
                ) * learning_mod
                reason = self._build_it_reason(emp, rot_score, workload_score, slot)
                skill_score = rot_score

            candidates.append(ScoredCandidate(
                employee_id=emp_id,
                employee_name=emp.name,
                total_score=min(max(total, 0.0), 1.0),
                rotation_score=rot_score,
                skill_score=skill_score,
                workload_score=workload_score,
                availability_score=avail_score,
                reason=reason,
            ))
        return candidates

    def _build_medical_reason(
        self, emp: Employee, rot_score: float, workload_score: float, slot: ShiftSlot
    ) -> str:
        parts = []
        if rot_score > 0.7:
            parts.append(f"no recent exposure to {slot.department_name}")
        elif rot_score > 0.4:
            parts.append(f"moderate rotation gap from {slot.department_name}")
        else:
            parts.append(f"recent experience in {slot.department_name}")
        if workload_score > 0.7:
            parts.append("low current workload")
        return f"Assigned {emp.name} ({emp.role}): {'; '.join(parts)}."

    def _build_it_reason(
        self, emp: Employee, skill_score: float, workload_score: float, slot: ShiftSlot
    ) -> str:
        matched_skills = ", ".join(emp.skills[:3]) if emp.skills else "general skills"
        parts = [f"skill match={skill_score:.0%} ({matched_skills})"]
        if workload_score > 0.7:
            parts.append("light workload")
        return f"Assigned {emp.name} ({emp.role}): {'; '.join(parts)}."
