# =============================================================
# auth/validators.py
# TalentMatch AI - Signup / Login Input Validation
# =============================================================
import re
from typing import List

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_VALID_ROLES = {"candidate", "recruiter"}
_MIN_PASSWORD_LENGTH = 8


def is_valid_email(email: str) -> bool:
    """Returns True when the given string is a plausible email address."""
    return bool(_EMAIL_PATTERN.match(email.strip()))


def validate_signup_form(
    full_name: str,
    email: str,
    password: str,
    confirm_password: str,
    role: str,
) -> List[str]:
    """
    Validates all Sign Up fields.

    Returns:
        List[str]: Human-readable error messages. Empty list means valid.
    """
    errors: List[str] = []

    if not full_name.strip():
        errors.append("Full name is required.")
    elif len(full_name.strip()) < 2:
        errors.append("Full name must be at least 2 characters long.")

    if not email.strip():
        errors.append("Email is required.")
    elif not is_valid_email(email):
        errors.append("Please enter a valid email address.")

    if not password:
        errors.append("Password is required.")
    elif len(password) < _MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {_MIN_PASSWORD_LENGTH} characters long.")

    if not confirm_password:
        errors.append("Please confirm your password.")
    elif password != confirm_password:
        errors.append("Passwords do not match.")

    if role not in _VALID_ROLES:
        errors.append("Please select a valid account role.")

    return errors


def validate_login_form(email: str, password: str) -> List[str]:
    """
    Validates Login fields for presence only (credential correctness is
    checked separately against the database).

    Returns:
        List[str]: Human-readable error messages. Empty list means valid.
    """
    errors: List[str] = []

    if not email.strip():
        errors.append("Email is required.")
    elif not is_valid_email(email):
        errors.append("Please enter a valid email address.")

    if not password:
        errors.append("Password is required.")

    return errors
