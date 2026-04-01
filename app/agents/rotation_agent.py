"""
RotationAgent - computes a rotation score per (employee, department) pair.

Medical: ACTIVE rotation - strongly prefers employees who have NOT
         recently worked in the target department.
IT:      MINIMAL rotation - just tracks skill overlap instead.
"""
from dataclasses import dataclass, field
from datetime import date

from app.agents.base_agent import BaseAgent, AgentInput, AgentOutput
from app.models.employee import Employee
from app.models.department import Department
from app.models.history import History


@dataclass
class RotationInput(AgentInput):
    employees: list[Employee] = field(default_factory=list)
    departments: list[Department] = field(default_factory=list)
    # history records for the relevant domain
    history_records: list[History] = field(default_factory=list)
    # 15-day rotation window (medical default)
    rotation_window_days: int = 15


@dataclass
class RotationOutput(AgentOutput):
    # {employee_id: {department_id: rotation_score}}  (0.0 = recently worked, 1.0 = never worked)
    rotation_scores: dict[int, dict[int, float]] = field(default_factory=dict)
    # {employee_id: department_id} recommended primary dept to avoid
    last_departments: dict[int, int] = field(default_factory=dict)


class RotationAgent(BaseAgent[RotationInput, RotationOutput]):
    """Calculates how desirable it is to assign an employee to each department."""

    def __init__(self):
        super().__init__("RotationAgent")

    def _validate(self, inp: RotationInput) -> None:
        if inp.roster_type not in ("medical", "it"):
            raise ValueError(f"RotationAgent: unknown roster_type '{inp.roster_type}'")

    def _process(self, inp: RotationInput) -> RotationOutput:
        rotation_scores: dict[int, dict[int, float]] = {}
        last_departments: dict[int, int] = {}

        if inp.roster_type == "medical":
            rotation_scores, last_departments = self._medical_rotation(inp)
        else:
            rotation_scores = self._it_skill_score(inp)

        return RotationOutput(
            rotation_scores=rotation_scores,
            last_departments=last_departments,
        )

    # ------------------------------------------------------------------
    # Medical: penalize same-department repeat assignments
    # ------------------------------------------------------------------
    def _medical_rotation(
        self, inp: RotationInput
    ) -> tuple[dict[int, dict[int, float]], dict[int, int]]:
        """
        Score = 1.0 if employee has never worked in dept.
        Score decays based on recency: score = days_since / rotation_window.
        Capped at [0.0, 1.0].
        """
        today = date.today()
        rotation_scores: dict[int, dict[int, float]] = {}
        last_departments: dict[int, int] = {}

        # Build {employee_id: {dept_id: last_period_end}} from history
        emp_dept_last: dict[int, dict[int, date]] = {}
        for h in inp.history_records:
            emp_dept_last.setdefault(h.employee_id, {})
            existing = emp_dept_last[h.employee_id].get(h.department_id)
            if existing is None or h.period_end > existing:
                emp_dept_last[h.employee_id][h.department_id] = h.period_end

        for emp in inp.employees:
            rotation_scores[emp.id] = {}
            # Find last department (most recently worked)
            dept_history = emp_dept_last.get(emp.id, {})
            if dept_history:
                last_dept_id = max(dept_history, key=lambda d: dept_history[d])
                last_departments[emp.id] = last_dept_id
            for dept in inp.departments:
                last_date = dept_history.get(dept.id)
                if last_date is None:
                    # Never worked here -> maximum rotation score
                    rotation_scores[emp.id][dept.id] = 1.0
                else:
                    days_since = (today - last_date).days
                    score = min(days_since / max(inp.rotation_window_days, 1), 1.0)
                    rotation_scores[emp.id][dept.id] = score

        return rotation_scores, last_departments

    # ------------------------------------------------------------------
    # IT: skill overlap score instead of dept rotation
    # ------------------------------------------------------------------
    def _it_skill_score(self, inp: RotationInput) -> dict[int, dict[int, float]]:
        """
        Score = fraction of department's required skills that the employee has.
        """
        rotation_scores: dict[int, dict[int, float]] = {}

        for emp in inp.employees:
            rotation_scores[emp.id] = {}
            emp_skills = set(s.lower() for s in emp.skills)
            for dept in inp.departments:
                required = [s.lower() for s in dept.required_skills]
                if not required:
                    rotation_scores[emp.id][dept.id] = 0.5  # neutral
                else:
                    matches = sum(1 for s in required if s in emp_skills)
                    rotation_scores[emp.id][dept.id] = matches / len(required)

        return rotation_scores
