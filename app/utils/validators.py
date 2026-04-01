"""Input validation utilities."""
from datetime import date
from typing import Literal


VALID_ROSTER_TYPES = {"medical", "it"}
VALID_SHIFT_TYPES_MEDICAL = {"morning", "evening", "night", "emergency"}
VALID_SHIFT_TYPES_IT = {"general", "night_support", "on_call"}
VALID_ROLES_MEDICAL = {"doctor", "nurse", "intern"}
VALID_ROLES_IT = {"developer", "qa", "devops", "support"}


def validate_roster_type(roster_type: str) -> str:
    """Validate and normalize roster type."""
    rt = roster_type.lower().strip()
    if rt not in VALID_ROSTER_TYPES:
        raise ValueError(f"roster_type must be one of {VALID_ROSTER_TYPES}, got '{rt}'")
    return rt


def validate_date_range(start_date: date, end_date: date) -> None:
    """Ensure start_date is before end_date and range is reasonable."""
    if start_date > end_date:
        raise ValueError("start_date must be before or equal to end_date")
    delta = (end_date - start_date).days
    if delta > 365:
        raise ValueError("Date range cannot exceed 365 days")


def validate_role_for_domain(role: str, roster_type: str) -> str:
    """Ensure role is valid for the given roster_type."""
    role = role.lower().strip()
    if roster_type == "medical" and role not in VALID_ROLES_MEDICAL:
        raise ValueError(f"Role '{role}' is not valid for medical roster. Valid: {VALID_ROLES_MEDICAL}")
    if roster_type == "it" and role not in VALID_ROLES_IT:
        raise ValueError(f"Role '{role}' is not valid for IT roster. Valid: {VALID_ROLES_IT}")
    return role
