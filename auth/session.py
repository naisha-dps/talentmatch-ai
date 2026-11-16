# =============================================================
# auth/session.py
# TalentMatch AI - Streamlit Session State Management
# =============================================================
from typing import Optional

import streamlit as st

from models.user import User

_AUTH_FLAG_KEY = "authenticated"
_AUTH_USER_KEY = "auth_user"
_AUTH_VIEW_KEY = "auth_view"
_SIGNUP_SUCCESS_KEY = "signup_success_message"

# Defaults for every workspace (Candidate/Recruiter portal) state key. Centralized
# here so both the initial page load and logout() reset to the exact same shape.
WORKSPACE_STATE_DEFAULTS: dict = {
    "candidate_raw_text": "",
    "saved_analysis_report": "",
    "saved_interview_questions": "",
    "saved_mock_evaluation": "",
    "saved_career_guidance": "",
    "saved_tailored_resume": "",
    "cached_recruiter_run_data": [],
    "recruiter_logs": [],
    "recruiter_run_executed": False,
    "agent_audio_response": None,
    "interview_active": False,
    "interview_complete": False,
    "current_question_idx": 0,
    "interview_history": [],
    "current_question_text": "",
    "current_question_audio": None,
}


def init_session_state() -> None:
    """Ensures all auth-related and workspace session_state keys exist with safe defaults."""
    if _AUTH_FLAG_KEY not in st.session_state:
        st.session_state[_AUTH_FLAG_KEY] = False
    if _AUTH_USER_KEY not in st.session_state:
        st.session_state[_AUTH_USER_KEY] = None
    if _AUTH_VIEW_KEY not in st.session_state:
        st.session_state[_AUTH_VIEW_KEY] = "signup"
    if _SIGNUP_SUCCESS_KEY not in st.session_state:
        st.session_state[_SIGNUP_SUCCESS_KEY] = ""

    init_workspace_state()


def init_workspace_state() -> None:
    """Ensures every Candidate/Recruiter portal state key exists with its default value."""
    for key, default in WORKSPACE_STATE_DEFAULTS.items():
        if key not in st.session_state or st.session_state[key] is None:
            # Lists/False/0/None defaults are all falsy-safe here except "" which
            # is intentionally treated as "unset" for string fields too.
            st.session_state[key] = default.copy() if isinstance(default, list) else default


def reset_workspace_state() -> None:
    """Forcibly resets every Candidate/Recruiter portal state key back to its default."""
    for key, default in WORKSPACE_STATE_DEFAULTS.items():
        st.session_state[key] = default.copy() if isinstance(default, list) else default


def login(user: User) -> None:
    """Marks the current Streamlit session as authenticated for the given user."""
    st.session_state[_AUTH_FLAG_KEY] = True
    st.session_state[_AUTH_USER_KEY] = user


def logout() -> None:
    """Clears authentication state and wipes any cached workspace data for this session."""
    st.session_state[_AUTH_FLAG_KEY] = False
    st.session_state[_AUTH_USER_KEY] = None
    st.session_state[_AUTH_VIEW_KEY] = "signup"
    st.session_state[_SIGNUP_SUCCESS_KEY] = ""
    reset_workspace_state()


def is_authenticated() -> bool:
    """Returns True if the current Streamlit session belongs to a logged-in user."""
    return bool(st.session_state.get(_AUTH_FLAG_KEY, False))


def get_current_user() -> Optional[User]:
    """Returns the logged-in User for this session, or None if not authenticated."""
    return st.session_state.get(_AUTH_USER_KEY)


def get_auth_view() -> str:
    """Returns which auth form is currently active: 'signup' or 'login'."""
    return st.session_state.get(_AUTH_VIEW_KEY, "signup")


def set_auth_view(view: str) -> None:
    """Switches the active auth form between 'signup' and 'login'."""
    st.session_state[_AUTH_VIEW_KEY] = view


def pop_signup_success_message() -> str:
    """Reads and clears the one-shot post-registration success message, if any."""
    message = st.session_state.get(_SIGNUP_SUCCESS_KEY, "")
    st.session_state[_SIGNUP_SUCCESS_KEY] = ""
    return message


def set_signup_success_message(message: str) -> None:
    """Stashes a one-shot success message to display after redirecting to Login."""
    st.session_state[_SIGNUP_SUCCESS_KEY] = message
