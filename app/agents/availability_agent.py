"""
AvailabilityAgent - determines which employees can work on each date/shift.

Works identically for both medical and IT domains.
Checks:
  1. Employee day-of-week availability
  2. Max shifts per week limit
  3. Minimum rest period since last shift
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

from app.agents.base_agent import BaseAgent, AgentInput, AgentOutput
from app.models.employee import Employee
from app.models.shift import Shift


@dataclass
class AvailabilityInput(AgentInput):
    employees: list[Employee] = field(default_factory=list)
    shifts: list[Shift] = field(default_factory=list)
    target_dates: list[date] = field(default_factory=list)
    # existing_schedule: {employee_id: [(schedule_date, shift_key), ...]}
    existing_assignments: dict[int, list[tuple[date, str]]] = field(default_factory=dict)
    min_rest_hours: int = 8


@dataclass
class AvailabilityOutput(AgentOutput):
    # {date_str: {shift_key: [employee_id, ...]}}
    availability_matrix: dict[str, dict[str, list[int]]] = field(default_factory=dict)
    # {employee_id: shifts_this_week}
    weekly_shift_counts: dict[int, int] = field(default_factory=dict)


class AvailabilityAgent(BaseAgent[AvailabilityInput, AvailabilityOutput]):
    """Computes which employees are available for each date and shift."""

    def __init__(self):
        super().__init__("AvailabilityAgent")

    def _validate(self, inp: AvailabilityInput) -> None:
        if not inp.employees:
            raise ValueError("AvailabilityAgent requires at least one employee.")
        if not inp.shifts:
            raise ValueError("AvailabilityAgent requires at least one shift definition.")
        if not inp.target_dates:
            raise ValueError("AvailabilityAgent requires at least one target date.")

    def _process(self, inp: AvailabilityInput) -> AvailabilityOutput:
        availability_matrix: dict[str, dict[str, list[int]]] = {}
        weekly_counts: dict[int, int] = {}

        # Build a week-start boundary (Monday of first date's week)
        if inp.target_dates:
            first_date = min(inp.target_dates)
            week_start = first_date - timedelta(days=first_date.weekday())
            week_end = week_start + timedelta(days=6)
        else:
            week_start = week_end = date.today()

        # Count existing assignments within the week for each employee
        for emp in inp.employees:
            count = 0
            for assign_date, _ in inp.existing_assignments.get(emp.id, []):
                if week_start <= assign_date <= week_end:
                    count += 1
            weekly_counts[emp.id] = count

        # Build shift objects keyed by shift_key
        shifts_by_key: dict[str, Shift] = {s.shift_key: s for s in inp.shifts}

        for target_date in inp.target_dates:
            date_str = target_date.isoformat()
            availability_matrix[date_str] = {}
            day_name = target_date.strftime("%A").lower()

            for shift in inp.shifts:
                available_ids: list[int] = []
                for emp in inp.employees:
                    if not emp.is_active:
                        continue
                    if not emp.is_available_on(day_name):
                        continue
                    # Weekly cap check
                    if weekly_counts.get(emp.id, 0) >= emp.max_shifts_per_week:
                        continue
                    # Rest period check
                    if self._violates_rest(emp.id, target_date, shift, inp.existing_assignments, inp.min_rest_hours, shifts_by_key):
                        continue
                    available_ids.append(emp.id)

                availability_matrix[date_str][shift.shift_key] = available_ids

        return AvailabilityOutput(
            availability_matrix=availability_matrix,
            weekly_shift_counts=weekly_counts,
        )

    def _violates_rest(
        self,
        employee_id: int,
        target_date: date,
        shift: Shift,
        existing_assignments: dict[int, list[tuple[date, str]]],
        min_rest_hours: int,
        shifts_by_key: dict[str, Shift],
    ) -> bool:
        """Return True if assigning this shift would violate minimum rest hours."""
        assignments = existing_assignments.get(employee_id, [])
        if not assignments:
            return False

        # Approximate shift start as a datetime
        try:
            h, m = map(int, shift.start_time.split(":"))
        except Exception:
            h, m = 9, 0
        proposed_start = datetime(target_date.year, target_date.month, target_date.day, h, m)

        for assign_date, assign_shift_key in assignments:
            prev_shift = shifts_by_key.get(assign_shift_key)
            if prev_shift is None:
                continue
            try:
                ph, pm = map(int, prev_shift.end_time.split(":"))
            except Exception:
                ph, pm = 18, 0
            prev_end = datetime(assign_date.year, assign_date.month, assign_date.day, ph, pm)
            # Handle overnight shifts: end < start means it ends next day
            if ph <= int(prev_shift.start_time.split(":")[0]) and prev_shift.is_night_shift:
                prev_end += timedelta(days=1)

            gap_hours = (proposed_start - prev_end).total_seconds() / 3600
            if 0 <= gap_hours < min_rest_hours:
                return True

        return False
