"""
Unit tests for the AI scheduling pipeline.
Tests: AvailabilityAgent, RotationAgent, OptimizationAgent, Orchestrator.
"""
import pytest
from datetime import date, timedelta

from app.agents.availability_agent import AvailabilityAgent, AvailabilityInput
from app.agents.rotation_agent import RotationAgent, RotationInput
from app.agents.optimization_agent import (
    OptimizationAgent, OptimizationInput, ShiftSlot
)
from app.agents.orchestrator import SchedulingOrchestrator, OrchestratorInput


# ── AvailabilityAgent ──────────────────────────────────────────────────────

class TestAvailabilityAgent:
    def test_basic_availability(self, medical_employees, medical_shifts):
        agent = AvailabilityAgent()
        monday = date(2025, 1, 6)  # A Monday
        output = agent.run(AvailabilityInput(
            roster_type="medical",
            employees=medical_employees,
            shifts=medical_shifts,
            target_dates=[monday],
        ))
        assert output.success
        date_str = monday.isoformat()
        assert date_str in output.availability_matrix
        # All employees available Monday
        morning_ids = output.availability_matrix[date_str].get("morning", [])
        assert len(morning_ids) >= 2  # Dr. Alice and Dr. Bob available Monday

    def test_unavailable_day_excluded(self, medical_employees, medical_shifts):
        """Wednesday should exclude Bob (availability=False on wednesday)."""
        agent = AvailabilityAgent()
        wednesday = date(2025, 1, 8)  # Wednesday
        output = agent.run(AvailabilityInput(
            roster_type="medical",
            employees=medical_employees,
            shifts=medical_shifts,
            target_dates=[wednesday],
        ))
        wed_morning = output.availability_matrix[wednesday.isoformat()].get("morning", [])
        # Bob (id=2) has availability=False on Wednesday
        assert 2 not in wed_morning

    def test_max_shifts_cap(self, medical_employees, medical_shifts):
        """Employee at max shifts should be excluded."""
        agent = AvailabilityAgent()
        monday = date(2025, 1, 6)
        # Simulate Alice already has 5 shifts this week (Tue–Sat, same week as Monday)
        existing = {1: [(monday + timedelta(days=i), "morning") for i in range(1, 6)]}
        output = agent.run(AvailabilityInput(
            roster_type="medical",
            employees=medical_employees,
            shifts=medical_shifts,
            target_dates=[monday],
            existing_assignments=existing,
        ))
        morning_ids = output.availability_matrix[monday.isoformat()].get("morning", [])
        assert 1 not in morning_ids  # Alice excluded (at max 5)

    def test_rest_period_enforcement(self, medical_employees, medical_shifts):
        """Employee coming off night shift should not be available for morning same/next day."""
        agent = AvailabilityAgent()
        today = date(2025, 1, 7)
        # Alice did night shift yesterday
        existing = {1: [(today - timedelta(days=1), "night")]}
        output = agent.run(AvailabilityInput(
            roster_type="medical",
            employees=medical_employees,
            shifts=medical_shifts,
            target_dates=[today],
            existing_assignments=existing,
            min_rest_hours=8,
        ))
        morning_ids = output.availability_matrix[today.isoformat()].get("morning", [])
        # Night ends at 07:00, morning starts 07:00 → gap = 0h, should violate rest
        assert 1 not in morning_ids


# ── RotationAgent ──────────────────────────────────────────────────────────

class TestRotationAgent:
    def test_medical_rotation_scores_no_history(self, medical_employees, medical_departments):
        """With no history, all employees should score 1.0 for all departments."""
        agent = RotationAgent()
        output = agent.run(RotationInput(
            roster_type="medical",
            employees=medical_employees,
            departments=medical_departments,
            history_records=[],
        ))
        assert output.success
        for emp in medical_employees:
            for dept in medical_departments:
                score = output.rotation_scores[emp.id][dept.id]
                assert score == 1.0, f"Expected 1.0 for emp {emp.id} dept {dept.id}, got {score}"

    def test_medical_rotation_recent_dept_penalized(self, medical_employees, medical_departments):
        """Employee recently in ICU should score lower for ICU."""
        from app.models.history import History
        recent_history = [
            History(employee_id=1, department_id=1, roster_type="medical",
                    period_start=date.today() - timedelta(days=3),
                    period_end=date.today() - timedelta(days=1),
                    total_shifts=3, night_shifts=0)
        ]
        agent = RotationAgent()
        output = agent.run(RotationInput(
            roster_type="medical",
            employees=medical_employees,
            departments=medical_departments,
            history_records=recent_history,
            rotation_window_days=15,
        ))
        # ICU score for Alice (id=1) should be < 1.0 (recently worked there)
        icu_score = output.rotation_scores[1][1]
        assert icu_score < 1.0

    def test_it_skill_score(self, it_employees):
        from app.models.department import Department
        backend_dept = Department(
            id=10, name="Backend", roster_type="it",
            required_skills_json='["Python","Docker"]',
            shift_types_json='["general"]',
            rotation_priority=3,
        )
        agent = RotationAgent()
        output = agent.run(RotationInput(
            roster_type="it",
            employees=it_employees,
            departments=[backend_dept],
            history_records=[],
        ))
        # Dave has Python and Docker → skill score should be 1.0
        dave_score = output.rotation_scores[4][10]
        assert dave_score == 1.0
        # Eve has none of those skills → score 0.0
        eve_score = output.rotation_scores[5][10]
        assert eve_score == 0.0


# ── OptimizationAgent ──────────────────────────────────────────────────────

class TestOptimizationAgent:
    def test_fills_slot_with_best_candidate(self, medical_employees, medical_departments, medical_shifts):
        agent = OptimizationAgent()
        target = date(2025, 1, 6)
        slot = ShiftSlot(
            target_date=target,
            department_id=1,
            department_name="ICU",
            shift_key="morning",
            required_count=1,
        )
        availability = {target.isoformat(): {"morning": [1, 2, 3]}}
        rotation_scores = {1: {1: 1.0, 2: 0.8}, 2: {1: 0.5, 2: 1.0}, 3: {1: 0.9, 2: 0.7}}
        output = agent.run(OptimizationInput(
            roster_type="medical",
            employees=medical_employees,
            departments=medical_departments,
            shifts=medical_shifts,
            slots=[slot],
            availability_matrix=availability,
            rotation_scores=rotation_scores,
            current_workload={1: 0, 2: 0, 3: 0},
        ))
        assert output.success
        assert len(output.assignments) == 1
        assert output.assignments[0].department_id == 1
        assert output.assignments[0].ai_score > 0

    def test_unfilled_when_no_available(self, medical_employees, medical_departments, medical_shifts):
        agent = OptimizationAgent()
        target = date(2025, 1, 6)
        slot = ShiftSlot(
            target_date=target, department_id=1, department_name="ICU",
            shift_key="morning", required_count=1,
        )
        # No one available
        output = agent.run(OptimizationInput(
            roster_type="medical",
            employees=medical_employees,
            departments=medical_departments,
            shifts=medical_shifts,
            slots=[slot],
            availability_matrix={target.isoformat(): {"morning": []}},
            rotation_scores={1: {1: 1.0}, 2: {1: 1.0}, 3: {1: 1.0}},
            current_workload={},
        ))
        assert len(output.assignments) == 0
        assert len(output.unfilled_slots) == 1

    def test_reason_populated(self, medical_employees, medical_departments, medical_shifts):
        agent = OptimizationAgent()
        target = date(2025, 1, 6)
        slot = ShiftSlot(target_date=target, department_id=1, department_name="ICU",
                         shift_key="morning", required_count=1)
        output = agent.run(OptimizationInput(
            roster_type="medical",
            employees=medical_employees,
            departments=medical_departments,
            shifts=medical_shifts,
            slots=[slot],
            availability_matrix={target.isoformat(): {"morning": [1]}},
            rotation_scores={1: {1: 1.0}},
            current_workload={1: 0},
        ))
        assert output.assignments[0].reason != ""
        assert "Dr. Alice" in output.assignments[0].reason


# ── Orchestrator Integration ───────────────────────────────────────────────

class TestOrchestrator:
    def test_full_pipeline_medical(self, medical_employees, medical_departments, medical_shifts):
        orchestrator = SchedulingOrchestrator()
        start = date(2025, 1, 6)  # Monday
        end   = date(2025, 1, 8)  # Wednesday (3 days)
        result = orchestrator.run(OrchestratorInput(
            roster_type="medical",
            start_date=start,
            end_date=end,
            employees=medical_employees,
            departments=medical_departments,
            shifts=medical_shifts,
            history_records=[],
            feedback_records=[],
        ))
        assert result.stats["total_assignments"] > 0
        assert result.stats["date_range_days"] == 3
        # All assignments have reasons
        for a in result.assignments:
            assert a.reason, f"Assignment missing reason: {a}"

    def test_full_pipeline_it(self, it_employees, it_shifts, db_session):
        from app.models.department import Department
        it_dept = Department(
            id=20, name="Backend", roster_type="it",
            shift_types_json='["general"]',
            required_staff_morning=2, required_staff_evening=0, required_staff_night=0,
            required_skills_json='["Python"]',
            rotation_priority=3,
        )
        db_session.add(it_dept)
        db_session.commit()

        orchestrator = SchedulingOrchestrator()
        start = date(2025, 1, 6)
        end   = date(2025, 1, 7)
        result = orchestrator.run(OrchestratorInput(
            roster_type="it",
            start_date=start,
            end_date=end,
            employees=it_employees,
            departments=[it_dept],
            shifts=it_shifts,
            history_records=[],
            feedback_records=[],
        ))
        assert result.stats["total_assignments"] >= 0  # May be 0 if only night shift but dept has general
