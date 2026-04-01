"""
ConflictAgent - detects and resolves scheduling conflicts.

Medical: strict rest enforcement (min 8h), no 3+ consecutive nights.
IT:      flexible - no more than 2 consecutive nights, fair weekends.

Conflict types detected:
  1. Double booking (same employee, same day, same shift)
  2. Rest period violation (back-to-back shifts with < min_rest_hours gap)
  3. Consecutive night shifts exceeding max
  4. Over weekly limit
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from collections import defaultdict

from app.agents.base_agent import BaseAgent, AgentInput, AgentOutput
from app.agents.optimization_agent import Assignment
from app.models.shift import Shift


@dataclass
class ConflictInput(AgentInput):
    assignments: list[Assignment] = field(default_factory=list)
    shifts_by_key: dict[str, Shift] = field(default_factory=dict)
    min_rest_hours: int = 8
    max_consecutive_nights: int = 3
    max_shifts_per_week: int = 6


@dataclass
class ConflictRecord:
    assignment_index: int
    conflict_type: str
    description: str
    auto_resolved: bool = False
    resolution_note: str = ""


@dataclass
class ConflictOutput(AgentOutput):
    clean_assignments: list[Assignment] = field(default_factory=list)
    conflicts: list[ConflictRecord] = field(default_factory=list)
    removed_count: int = 0


class ConflictAgent(BaseAgent[ConflictInput, ConflictOutput]):
    """Scans and resolves conflicts in a proposed assignment list."""

    def __init__(self):
        super().__init__("ConflictAgent")

    def _validate(self, inp: ConflictInput) -> None:
        if inp.roster_type not in ("medical", "it"):
            raise ValueError(f"ConflictAgent: unknown roster_type '{inp.roster_type}'")

    def _process(self, inp: ConflictInput) -> ConflictOutput:
        conflicts: list[ConflictRecord] = []
        removed_indices: set[int] = set()

        max_consecutive = inp.max_consecutive_nights
        if inp.roster_type == "it":
            max_consecutive = min(max_consecutive, 2)

        # --- Pass 1: detect double bookings ---
        # key = (employee_id, date, shift_key)
        seen: dict[tuple, int] = {}
        for i, a in enumerate(inp.assignments):
            key = (a.employee_id, a.target_date, a.shift_key)
            if key in seen:
                conflicts.append(ConflictRecord(
                    assignment_index=i,
                    conflict_type="DOUBLE_BOOKING",
                    description=f"{a.employee_name} assigned twice to {a.shift_key} on {a.target_date}",
                    auto_resolved=True,
                    resolution_note="Duplicate removed.",
                ))
                removed_indices.add(i)
            else:
                seen[key] = i

        # --- Pass 2: detect rest violations ---
        emp_assignments: dict[int, list[tuple[int, Assignment]]] = defaultdict(list)
        for i, a in enumerate(inp.assignments):
            if i not in removed_indices:
                emp_assignments[a.employee_id].append((i, a))

        for emp_id, emp_assigns in emp_assignments.items():
            emp_assigns_sorted = sorted(emp_assigns, key=lambda x: (x[1].target_date, x[1].shift_key))
            for j in range(1, len(emp_assigns_sorted)):
                idx_prev, prev_a = emp_assigns_sorted[j - 1]
                idx_curr, curr_a = emp_assigns_sorted[j]
                if idx_prev in removed_indices or idx_curr in removed_indices:
                    continue

                prev_shift = inp.shifts_by_key.get(prev_a.shift_key)
                curr_shift = inp.shifts_by_key.get(curr_a.shift_key)
                if prev_shift is None or curr_shift is None:
                    continue

                gap = self._compute_gap_hours(prev_a.target_date, prev_shift, curr_a.target_date, curr_shift)
                if 0 <= gap < inp.min_rest_hours:
                    conflicts.append(ConflictRecord(
                        assignment_index=idx_curr,
                        conflict_type="REST_VIOLATION",
                        description=(
                            f"{curr_a.employee_name}: only {gap:.1f}h rest before "
                            f"{curr_a.shift_key} on {curr_a.target_date} (min={inp.min_rest_hours}h)"
                        ),
                        auto_resolved=True,
                        resolution_note="Later shift removed to enforce rest period.",
                    ))
                    removed_indices.add(idx_curr)

        # --- Pass 3: consecutive night shifts ---
        for emp_id, emp_assigns in emp_assignments.items():
            sorted_by_date = sorted(emp_assigns, key=lambda x: x[1].target_date)
            night_streak = 0
            for idx, a in sorted_by_date:
                if idx in removed_indices:
                    night_streak = 0
                    continue
                shift = inp.shifts_by_key.get(a.shift_key)
                if shift and shift.is_night_shift:
                    night_streak += 1
                    if night_streak > max_consecutive:
                        conflicts.append(ConflictRecord(
                            assignment_index=idx,
                            conflict_type="CONSECUTIVE_NIGHTS",
                            description=(
                                f"{a.employee_name}: {night_streak} consecutive nights "
                                f"(max={max_consecutive})"
                            ),
                            auto_resolved=True,
                            resolution_note="Excess night shift removed.",
                        ))
                        removed_indices.add(idx)
                        night_streak = max_consecutive
                else:
                    night_streak = 0

        # --- Pass 4: weekly limit ---
        weekly_counts: dict[tuple[int, date], int] = defaultdict(int)
        for i, a in enumerate(inp.assignments):
            if i in removed_indices:
                continue
            week_start = a.target_date - timedelta(days=a.target_date.weekday())
            weekly_counts[(a.employee_id, week_start)] += 1

        for i, a in enumerate(inp.assignments):
            if i in removed_indices:
                continue
            week_start = a.target_date - timedelta(days=a.target_date.weekday())
            if weekly_counts.get((a.employee_id, week_start), 0) > inp.max_shifts_per_week:
            # Check if THIS specific assignment pushes over the limit
                emp_week_assigns = [
                    (j, b) for j, b in enumerate(inp.assignments)
                    if j not in removed_indices
                    and b.employee_id == a.employee_id
                    and b.target_date - timedelta(days=b.target_date.weekday()) == week_start
                ]
                if len(emp_week_assigns) > inp.max_shifts_per_week:
                    # Remove the last (lowest-score) ones
                    emp_week_assigns.sort(key=lambda x: x[1].ai_score)
                    excess = len(emp_week_assigns) - inp.max_shifts_per_week
                    for j2, b2 in emp_week_assigns[:excess]:
                        if j2 not in removed_indices:
                            conflicts.append(ConflictRecord(
                                assignment_index=j2,
                                conflict_type="WEEKLY_LIMIT",
                                description=f"{b2.employee_name}: over weekly shift limit ({inp.max_shifts_per_week})",
                                auto_resolved=True,
                                resolution_note="Lowest-scored excess shift removed.",
                            ))
                            removed_indices.add(j2)

        clean = [a for i, a in enumerate(inp.assignments) if i not in removed_indices]

        return ConflictOutput(
            clean_assignments=clean,
            conflicts=conflicts,
            removed_count=len(removed_indices),
            success=True,
        )

    def _compute_gap_hours(
        self,
        prev_date: date, prev_shift: Shift,
        curr_date: date, curr_shift: Shift,
    ) -> float:
        """Compute hours between end of previous shift and start of next."""
        try:
            eh, em = map(int, prev_shift.end_time.split(":"))
            sh, sm = map(int, curr_shift.start_time.split(":"))
        except Exception:
            return 24.0  # unknown shift times, assume safe

        prev_end = datetime(prev_date.year, prev_date.month, prev_date.day, eh, em)
        curr_start = datetime(curr_date.year, curr_date.month, curr_date.day, sh, sm)

        # Night shift end carries to next day
        if prev_shift.is_night_shift and eh < 12:
            prev_end += timedelta(days=1)

        gap = (curr_start - prev_end).total_seconds() / 3600
        return gap
