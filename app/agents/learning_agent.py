"""
LearningAgent - reads past schedule history and produces adjusted weight
multipliers per employee, per domain.

Learns separately for medical and IT:
  - Employees who received low feedback scores get a slight penalty weight.
  - Employees who worked well in a department get a boost.
  - Decay factor prevents old data from dominating.
"""
from dataclasses import dataclass, field
from datetime import date

from app.agents.base_agent import BaseAgent, AgentInput, AgentOutput
from app.models.history import History
from app.models.feedback import Feedback
from app.config import get_settings


@dataclass
class LearningInput(AgentInput):
    history_records: list[History] = field(default_factory=list)
    feedback_records: list[Feedback] = field(default_factory=list)
    employee_ids: list[int] = field(default_factory=list)
    reference_date: date = field(default_factory=date.today)


@dataclass
class LearningOutput(AgentOutput):
    # {employee_id: weight_multiplier}  1.0 = neutral, <1.0 = penalised, >1.0 = boosted
    employee_weights: dict[int, float] = field(default_factory=dict)
    # {(employee_id, department_id): dept_specific_multiplier}
    dept_weights: dict[tuple[int, int], float] = field(default_factory=dict)
    insight_summary: list[str] = field(default_factory=list)


class LearningAgent(BaseAgent[LearningInput, LearningOutput]):
    """Adjusts scheduling weights based on historical feedback and patterns."""

    def __init__(self):
        super().__init__("LearningAgent")
        self._settings = get_settings()

    def _validate(self, inp: LearningInput) -> None:
        if inp.roster_type not in ("medical", "it"):
            raise ValueError(f"LearningAgent: unknown roster_type '{inp.roster_type}'")

    def _process(self, inp: LearningInput) -> LearningOutput:
        decay = self._settings.LEARNING_DECAY_FACTOR
        min_history = self._settings.LEARNING_MIN_HISTORY

        employee_weights: dict[int, float] = {eid: 1.0 for eid in inp.employee_ids}
        dept_weights: dict[tuple[int, int], float] = {}
        insights: list[str] = []

        # ----------------------------------------------------------------
        # Step 1: Feedback-based adjustment
        # ----------------------------------------------------------------
        feedback_by_emp: dict[int, list[int]] = {}
        for fb in inp.feedback_records:
            feedback_by_emp.setdefault(fb.employee_id, []).append(fb.rating)

        for emp_id, ratings in feedback_by_emp.items():
            if len(ratings) < min_history:
                continue
            avg_rating = sum(ratings) / len(ratings)
            # Normalise: rating 3 = neutral (1.0), 5 = boost (1.15), 1 = penalty (0.85)
            modifier = 0.85 + (avg_rating - 1) * (0.30 / 4)  # maps [1,5] -> [0.85, 1.15]
            modifier = max(0.80, min(1.20, modifier))
            employee_weights[emp_id] = employee_weights.get(emp_id, 1.0) * modifier
            if avg_rating < 2.5:
                insights.append(
                    f"Employee {emp_id}: low avg feedback ({avg_rating:.1f}) → weight penalised."
                )
            elif avg_rating > 4.0:
                insights.append(
                    f"Employee {emp_id}: high avg feedback ({avg_rating:.1f}) → weight boosted."
                )

        # ----------------------------------------------------------------
        # Step 2: History-based department affinity adjustment
        # ----------------------------------------------------------------
        for h in inp.history_records:
            key = (h.employee_id, h.department_id)
            # Recency decay: older records have less influence
            days_old = (inp.reference_date - h.period_end).days
            recency_factor = decay ** (days_old / 30)  # decay per 30 days

            # Boost if high avg score in that dept
            if h.avg_score > 0.75 and h.total_shifts >= min_history:
                boost = 1.0 + (h.avg_score - 0.75) * 0.4 * recency_factor
                dept_weights[key] = dept_weights.get(key, 1.0) * boost
            elif h.avg_score < 0.40 and h.total_shifts >= min_history:
                penalty = 1.0 - (0.40 - h.avg_score) * 0.3 * recency_factor
                dept_weights[key] = dept_weights.get(key, 1.0) * max(penalty, 0.70)

        # ----------------------------------------------------------------
        # Step 3: Domain-specific adjustments
        # ----------------------------------------------------------------
        if inp.roster_type == "medical":
            # Penalise employees with high night-shift counts (burnout prevention)
            emp_nights: dict[int, int] = {}
            for h in inp.history_records:
                emp_nights[h.employee_id] = emp_nights.get(h.employee_id, 0) + h.night_shifts
            for emp_id, nights in emp_nights.items():
                if nights > 15:
                    penalty = max(0.80, 1.0 - (nights - 15) * 0.01)
                    employee_weights[emp_id] = employee_weights.get(emp_id, 1.0) * penalty
                    insights.append(f"Employee {emp_id}: {nights} recent nights → slight penalty.")
        else:
            # IT: boost employees with high on-call counts (reward reliability)
            for h in inp.history_records:
                if h.emergency_shifts > 5:
                    boost = min(1.15, 1.0 + h.emergency_shifts * 0.01)
                    employee_weights[h.employee_id] = (
                        employee_weights.get(h.employee_id, 1.0) * boost
                    )

        return LearningOutput(
            employee_weights=employee_weights,
            dept_weights=dept_weights,
            insight_summary=insights,
        )
