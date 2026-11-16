# =============================================================
# database/db.py
# TalentMatch AI - SQLite Connection & Schema Bootstrap
# =============================================================
import sqlite3
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "talentmatch.db"


def get_connection() -> sqlite3.Connection:
    """
    Opens a fresh SQLite connection scoped to a single operation.

    A new connection is created per call rather than shared across Streamlit
    reruns, since Streamlit may execute a session's script on different
    threads and sqlite3 connections are not safe to share across threads.

    Returns:
        sqlite3.Connection: Connection with row_factory set to sqlite3.Row.
    """
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@st.cache_resource
def init_database() -> None:
    """
    Creates the data directory and the users table if they do not exist yet.

    Cached with st.cache_resource so the schema bootstrap only runs once per
    running process instead of on every Streamlit rerun.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = get_connection()
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('candidate', 'recruiter')),
                created_at TEXT NOT NULL,
                last_login TEXT
            )
            """
        )
        connection.commit()
    finally:
        connection.close()
