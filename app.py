# =============================================================
# app.py
# TalentMatch AI - Application Entry Point
#
# Boots the SQLite-backed auth layer, renders the landing page for
# unauthenticated visitors, and routes logged-in users to the workspace
# that matches their account role (Candidate or Recruiter).
# =============================================================
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from auth.session import get_current_user, init_session_state, is_authenticated
from database.db import init_database
from ui.candidate_portal import render_candidate_portal
from ui.landing import render_landing_page
from ui.recruiter_portal import render_recruiter_portal
from ui.sidebar import render_authenticated_sidebar
from ui.styles import inject_global_styles

init_session_state()

st.set_page_config(
    page_title="TalentMatch AI - Systems Interface",
    layout="wide",
    initial_sidebar_state="expanded" if is_authenticated() else "collapsed",
)

inject_global_styles()
init_database()

if not is_authenticated():
    render_landing_page()
    st.stop()

render_authenticated_sidebar()

current_user = get_current_user()
if current_user.is_candidate:
    render_candidate_portal()
else:
    render_recruiter_portal()
