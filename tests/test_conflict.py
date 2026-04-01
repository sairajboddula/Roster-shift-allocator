"""
Unit tests for the ConflictAgent.
Tests: double-booking, rest violations, consecutive nights, weekly limits.
"""
import pytest
from datetime import date, timedelta

from app.agents.conflict_agent import ConflictAgent, ConflictInput
from app.agents.optimization_agent import Assignment


def _make_assignment(emp_id, emp_name, dept_id, dept_name, shift_key, target_date, score=0.8):
    return Assignment(
        target_date=target_date,
        department_id=dept_id,
        department_name=dept_name,
        shift_key=shift_key,
        employee_id=emp_id,
        employee_name=emp_name,
        ai_score=score,
        rotation_score=0.8,
        skill_score=0.8,
        workload_score=0.8,
        reason=f"Test assignment for {emp_name}",
    )


class TestConflictAgent:

    def test_no_conflicts_clean_schedule(self, medical_shifts):
        """A clean schedule with no conflicts should pass through unchanged."""
        shifts_by_key = {s.shift_key: s for s in medical_shifts}
        today = date(2025, 1, 6)
        assignments = [
            _make_assignment(1, "Dr. Alice", 1, "ICU", "morning", today),
            _make_assignment(2, "Dr. Bob", 2, "General", "evening", today),
            _make_assignment(3, "Nurse Carol", 1, "ICU", "night", today),
        ]
        agent = ConflictAgent()
        output = agent.run(ConflictInput(
            roster_type="medical",
            assignments=assignments,
            shifts_by_key=shifts_by_key,
            min_rest_hours=8,
            max_consecutive_nights=3,
            max_shifts_per_week=6,
        ))
        assert output.success
        assert output.removed_count == 0
        assert len(output.clean_assignments) == 3
        assert len(output.conflicts) == 0

    def test_double_booking_detected(self, medical_shifts):
        """Same employee, same day, same shift → second entry removed."""
        shifts_by_key = {s.shift_key: s for s in medical_shifts}
        today = date(2025, 1, 6)
        assignments = [
            _make_assignment(1, "Dr. Alice", 1, "ICU", "morning", today),
            _make_assignment(1, "Dr. Alice", 2, "General", "morning", today),  # duplicate!
        ]
        agent = ConflictAgent()
        output = agent.run(ConflictInput(
            roster_type="medical",
            assignments=assignments,
            shifts_by_key=shifts_by_key,
        ))
        assert output.removed_count == 1
        assert len(output.clean_assignments) == 1
        assert any(c.conflict_type == "DOUBLE_BOOKING" for c in output.conflicts)

    def test_rest_violation_detected(self, medical_shifts):
        """Night shift followed immediately by morning = rest violation."""
        shifts_by_key = {s.shift_key: s for s in medical_shifts}
        today = date(2025, 1, 6)
        tomorrow = today + timedelta(days=1)
        assignments = [
            _make_assignment(1, "Dr. Alice", 1, "ICU", "night", today),     # ends 07:00 next day
            _make_assignment(1, "Dr. Alice", 1, "ICU", "morning", tomorrow), # starts 07:00 same time → 0h gap
        ]
        agent = ConflictAgent()
        output = agent.run(ConflictInput(
            roster_type="medical",
            assignments=assignments,
            shifts_by_key=shifts_by_key,
            min_rest_hours=8,
        ))
        assert output.removed_count >= 1
        assert any(c.conflict_type == "REST_VIOLATION" for c in output.conflicts)

    def test_consecutive_nights_medical(self, medical_shifts):
        """Medical: max 3 consecutive nights; 4th should be removed."""
        shifts_by_key = {s.shift_key: s for s in medical_shifts}
        base = date(2025, 1, 6)
        assignments = [
            _make_assignment(1, "Dr. Alice", 1, "ICU", "night", base + timedelta(days=i))
            for i in range(4)  # 4 consecutive nights
        ]
        agent = ConflictAgent()
        output = agent.run(ConflictInput(
            roster_type="medical",
            assignments=assignments,
            shifts_by_key=shifts_by_key,
            min_rest_hours=8,
            max_consecutive_nights=3,
        ))
        night_conflicts = [c for c in output.conflicts if c.conflict_type == "CONSECUTIVE_NIGHTS"]
        assert len(night_conflicts) >= 1

    def test_consecutive_nights_it_stricter(self, it_shifts):
        """IT: max 2 consecutive nights; 3rd should be removed."""
        shifts_by_key = {s.shift_key: s for s in it_shifts}
        base = date(2025, 1, 6)
        assignments = [
            _make_assignment(4, "Dev Dave", 10, "Backend", "night_support", base + timedelta(days=i))
            for i in range(3)  # 3 consecutive nights
        ]
        agent = ConflictAgent()
        output = agent.run(ConflictInput(
            roster_type="it",
            assignments=assignments,
            shifts_by_key=shifts_by_key,
            min_rest_hours=8,
            max_consecutive_nights=2,
        ))
        night_conflicts = [c for c in output.conflicts if c.conflict_type == "CONSECUTIVE_NIGHTS"]
        assert len(night_conflicts) >= 1

    def test_weekly_limit_enforced(self, medical_shifts):
        """Employee with 7 shifts in one week → excess removed."""
        shifts_by_key = {s.shift_key: s for s in medical_shifts}
        monday = date(2025, 1, 6)
        # Create 7 morning shifts in same week for Alice (max=5)
        assignments = [
            _make_assignment(1, "Dr. Alice", 1, "ICU", "morning", monday + timedelta(days=i), score=0.5 + i*0.05)
            for i in range(7)
        ]
        agent = ConflictAgent()
        output = agent.run(ConflictInput(
            roster_type="medical",
            assignments=assignments,
            shifts_by_key=shifts_by_key,
            min_rest_hours=1,  # relax rest for this test
            max_consecutive_nights=3,
            max_shifts_per_week=5,
        ))
        assert len(output.clean_assignments) <= 5

    def test_auto_resolve_note_present(self, medical_shifts):
        """Each detected conflict should have an auto_resolved=True and a resolution note."""
        shifts_by_key = {s.shift_key: s for s in medical_shifts}
        today = date(2025, 1, 6)
        assignments = [
            _make_assignment(1, "Dr. Alice", 1, "ICU", "morning", today),
            _make_assignment(1, "Dr. Alice", 2, "General", "morning", today),  # double booking
        ]
        agent = ConflictAgent()
        output = agent.run(ConflictInput(
            roster_type="medical",
            assignments=assignments,
            shifts_by_key=shifts_by_key,
        ))
        for conflict in output.conflicts:
            assert conflict.auto_resolved is True
            assert conflict.resolution_note != ""
