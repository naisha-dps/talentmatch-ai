# =============================================================
# ui/workspace_helpers.py
# TalentMatch AI - Shared Helpers for Candidate & Recruiter Portals
# =============================================================
import re

import streamlit as st

from utils.llm_config import validate_api_key


def check_api_infrastructure() -> bool:
    """Verifies that external model parsing backends are validated."""
    is_valid, error_msg = validate_api_key()
    if not is_valid:
        st.error(f"**Configuration Warning:** {error_msg}")
        st.info("Ensure your access profiles match the active server matrix guidelines.")
        return False
    return True


def parse_score_metrics(report_text: str) -> int:
    """Isolates numerical optimization scores from the underlying graph response markdown."""
    match = re.search(r'(?:Alignment Score|Score):\s*(\d+)%', report_text, re.IGNORECASE)
    if not match:
        match = re.search(r'(\d+)%', report_text)
    return int(match.group(1)) if match else 75


def render_pipeline_runner(steps: list, current_index: int) -> None:
    """Outputs a horizontal visual tracker to depict real-time state tracking steps."""
    columns = st.columns(len(steps))
    for idx, (col, step_label) in enumerate(zip(columns, steps)):
        with col:
            if idx < current_index:
                st.markdown(f"~~{step_label}~~")
            elif idx == current_index:
                st.markdown(f"**{step_label}**")
            else:
                st.markdown(f"{step_label}")
