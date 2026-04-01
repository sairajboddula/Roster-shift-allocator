"""Pytest fixtures shared across all test modules."""
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.employee import Employee
from app.models.department import Department
from app.models.shift import Shift


@pytest.fixture(scope="function")
def db_session():
    """In-memory SQLite session for each test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def medical_employees(db_session) -> list[Employee]:
    employees = [
        Employee(id=1, name="Dr. Alice", email="alice@h.com", role="doctor",
                 roster_type="medical", max_shifts_per_week=5, experience_years=5.0,
                 skills_json='["ICU","Emergency"]',
                 availability_json='{"monday":true,"tuesday":true,"wednesday":true,"thursday":true,"friday":true,"saturday":false,"sunday":false}'),
        Employee(id=2, name="Dr. Bob", email="bob@h.com", role="doctor",
                 roster_type="medical", max_shifts_per_week=5, experience_years=3.0,
                 skills_json='["Surgery","General Medicine"]',
                 availability_json='{"monday":true,"tuesday":true,"wednesday":false,"thursday":true,"friday":true,"saturday":true,"sunday":false}'),
        Employee(id=3, name="Nurse Carol", email="carol@h.com", role="nurse",
                 roster_type="medical", max_shifts_per_week=6, experience_years=4.0,
                 skills_json='["General Medicine","Pediatrics"]',
                 availability_json='{"monday":true,"tuesday":true,"wednesday":true,"thursday":true,"friday":true,"saturday":false,"sunday":false}'),
    ]
    for e in employees:
        db_session.add(e)
    db_session.commit()
    return employees


@pytest.fixture
def it_employees(db_session) -> list[Employee]:
    employees = [
        Employee(id=4, name="Dev Dave", email="dave@t.com", role="developer",
                 roster_type="it", max_shifts_per_week=5, experience_years=4.0,
                 skills_json='["Python","Docker","AWS"]',
                 availability_json='{"monday":true,"tuesday":true,"wednesday":true,"thursday":true,"friday":true,"saturday":false,"sunday":false}'),
        Employee(id=5, name="QA Eve", email="eve@t.com", role="qa",
                 roster_type="it", max_shifts_per_week=5, experience_years=2.0,
                 skills_json='["Selenium","Pytest","JIRA"]',
                 availability_json='{"monday":true,"tuesday":true,"wednesday":true,"thursday":true,"friday":true,"saturday":false,"sunday":false}'),
        Employee(id=6, name="Ops Frank", email="frank@t.com", role="devops",
                 roster_type="it", max_shifts_per_week=5, experience_years=6.0,
                 skills_json='["Docker","Kubernetes","AWS"]',
                 availability_json='{"monday":true,"tuesday":true,"wednesday":true,"thursday":true,"friday":true,"saturday":true,"sunday":false}'),
    ]
    for e in employees:
        db_session.add(e)
    db_session.commit()
    return employees


@pytest.fixture
def medical_departments(db_session) -> list[Department]:
    depts = [
        Department(id=1, name="ICU", roster_type="medical",
                   shift_types_json='["morning","evening","night"]',
                   required_staff_morning=2, required_staff_evening=2, required_staff_night=1,
                   required_skills_json='["ICU"]', rotation_priority=5),
        Department(id=2, name="General Medicine", roster_type="medical",
                   shift_types_json='["morning","evening"]',
                   required_staff_morning=2, required_staff_evening=1, required_staff_night=0,
                   required_skills_json='[]', rotation_priority=3),
    ]
    for d in depts:
        db_session.add(d)
    db_session.commit()
    return depts


@pytest.fixture
def medical_shifts(db_session) -> list[Shift]:
    shifts = [
        Shift(id=1, name="Morning", shift_key="morning", roster_type="medical",
              start_time="07:00", end_time="15:00", duration_hours=8.0, is_night_shift=False, color_hex="#F59E0B"),
        Shift(id=2, name="Evening", shift_key="evening", roster_type="medical",
              start_time="15:00", end_time="23:00", duration_hours=8.0, is_night_shift=False, color_hex="#8B5CF6"),
        Shift(id=3, name="Night", shift_key="night", roster_type="medical",
              start_time="23:00", end_time="07:00", duration_hours=8.0, is_night_shift=True, color_hex="#1E3A5F"),
    ]
    for s in shifts:
        db_session.add(s)
    db_session.commit()
    return shifts


@pytest.fixture
def it_shifts(db_session) -> list[Shift]:
    shifts = [
        Shift(id=4, name="General", shift_key="general", roster_type="it",
              start_time="09:00", end_time="18:00", duration_hours=9.0, is_night_shift=False, color_hex="#10B981"),
        Shift(id=5, name="Night Support", shift_key="night_support", roster_type="it",
              start_time="21:00", end_time="06:00", duration_hours=9.0, is_night_shift=True, color_hex="#1E3A5F"),
    ]
    for s in shifts:
        db_session.add(s)
    db_session.commit()
    return shifts
