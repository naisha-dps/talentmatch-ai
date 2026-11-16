# =============================================================
# database/user_repository.py
# TalentMatch AI - Users Table Data Access Layer
# =============================================================
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from database.db import get_connection


def email_exists(email: str) -> bool:
    """Checks whether an account with the given (lowercased) email already exists."""
    connection = get_connection()
    try:
        cursor = connection.execute(
            "SELECT 1 FROM users WHERE email = ? LIMIT 1", (email.lower(),)
        )
        return cursor.fetchone() is not None
    finally:
        connection.close()


def create_user(full_name: str, email: str, password_hash: str, role: str) -> int:
    """
    Inserts a new user record.

    Args:
        full_name: Display name collected at signup.
        email: Account email, stored lowercased.
        password_hash: Salted/hashed password, never plaintext.
        role: Either "candidate" or "recruiter".

    Returns:
        int: The newly created user's id.

    Raises:
        sqlite3.IntegrityError: If the email is already registered.
    """
    created_at = datetime.now(timezone.utc).isoformat()

    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            INSERT INTO users (full_name, email, password_hash, role, created_at, last_login)
            VALUES (?, ?, ?, ?, ?, NULL)
            """,
            (full_name.strip(), email.lower().strip(), password_hash, role, created_at),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    """Fetches the raw row for a user by email, or None if not found."""
    connection = get_connection()
    try:
        cursor = connection.execute(
            "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
        )
        return cursor.fetchone()
    finally:
        connection.close()


def update_last_login(user_id: int) -> None:
    """Stamps the current UTC time as the user's last successful login."""
    last_login = datetime.now(timezone.utc).isoformat()

    connection = get_connection()
    try:
        connection.execute(
            "UPDATE users SET last_login = ? WHERE id = ?", (last_login, user_id)
        )
        connection.commit()
    finally:
        connection.close()
