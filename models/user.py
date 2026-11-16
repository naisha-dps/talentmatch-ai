# =============================================================
# models/user.py
# TalentMatch AI - User Domain Model
# =============================================================
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class User:
    """Represents an authenticated TalentMatch AI account."""

    id: int
    full_name: str
    email: str
    role: str
    created_at: str
    last_login: Optional[str]

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "User":
        """Builds a User instance from a sqlite3.Row returned by the users table."""
        return cls(
            id=row["id"],
            full_name=row["full_name"],
            email=row["email"],
            role=row["role"],
            created_at=row["created_at"],
            last_login=row["last_login"],
        )

    @property
    def is_candidate(self) -> bool:
        """True when the account role is Candidate."""
        return self.role == "candidate"

    @property
    def is_recruiter(self) -> bool:
        """True when the account role is Recruiter."""
        return self.role == "recruiter"
