# =============================================================
# auth/service.py
# TalentMatch AI - Registration & Login Orchestration
# =============================================================
import sqlite3
from typing import Optional, Tuple

from auth.security import hash_password, verify_password
from auth.validators import validate_signup_form, validate_login_form
from database.user_repository import (
    create_user,
    email_exists,
    get_user_by_email,
    update_last_login,
)
from models.user import User


def register_user(
    full_name: str,
    email: str,
    password: str,
    confirm_password: str,
    role: str,
) -> Tuple[bool, str]:
    """
    Validates and persists a new user account.

    Returns:
        Tuple[bool, str]: (success, message). On failure, message contains all
        validation errors joined by newlines, or a duplicate-email notice.
    """
    errors = validate_signup_form(full_name, email, password, confirm_password, role)
    if errors:
        return False, "\n".join(errors)

    if email_exists(email):
        return False, "An account with this email already exists. Please log in instead."

    try:
        create_user(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role=role,
        )
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists. Please log in instead."

    return True, "Account created successfully. Please log in to continue."


def authenticate_user(email: str, password: str) -> Tuple[bool, Optional[User], str]:
    """
    Validates credentials against the users table.

    Returns:
        Tuple[bool, Optional[User], str]: (success, user_or_none, message).
        Failure messages are intentionally generic to avoid revealing whether
        an email is registered.
    """
    errors = validate_login_form(email, password)
    if errors:
        return False, None, "\n".join(errors)

    row = get_user_by_email(email)
    if row is None or not verify_password(password, row["password_hash"]):
        return False, None, "Invalid email or password."

    update_last_login(row["id"])
    user = User.from_row(row)
    return True, user, "Login successful."
