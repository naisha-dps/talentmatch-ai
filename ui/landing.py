# =============================================================
# ui/landing.py
# TalentMatch AI - Landing Page & Authentication Card
# =============================================================
import streamlit as st

from auth.service import authenticate_user, register_user
from auth.session import (
    get_auth_view,
    login,
    pop_signup_success_message,
    set_auth_view,
    set_signup_success_message,
)

_ROLE_LABELS = {"Candidate": "candidate", "Recruiter": "recruiter"}


def _render_brand_column() -> None:
    """Renders the left-hand branding, tagline, description, and AI visual."""
    st.markdown(
        """
        <div class="brand-eyebrow">Generative AI Recruitment Platform</div>
        <h1 class="brand-title">TalentMatch AI</h1>
        <div class="brand-tagline">Where great candidates meet the right roles, faster.</div>
        <div class="brand-description">
            TalentMatch AI pairs candidates and recruiters with a dedicated Generative AI
            workspace. Candidates get resume analysis, tailored optimization, interview
            preparation, and a live adaptive voice interview coach. Recruiters get
            batch resume ranking, candidate comparison, and job description matching
            across an entire applicant pool &mdash; all in one platform.
        </div>
        <div class="feature-pill-row">
            <div class="feature-pill">Resume Analysis</div>
            <div class="feature-pill">Voice Interview Coaching</div>
            <div class="feature-pill">Career Roadmaps</div>
            <div class="feature-pill">Candidate Ranking</div>
            <div class="feature-pill">Job Description Matching</div>
        </div>
        <div class="ai-visual">
            <div class="ai-link l1"></div>
            <div class="ai-link l2"></div>
            <div class="ai-link l3"></div>
            <div class="ai-node n1"></div>
            <div class="ai-node n2"></div>
            <div class="ai-node n3"></div>
            <div class="ai-node n4"></div>
            <div class="ai-node n5"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_tab_switcher() -> None:
    """Renders the Sign Up / Login pill switcher backed by session state."""
    active_view = get_auth_view()
    col_signup, col_login = st.columns(2)

    with col_signup:
        if st.button(
            "Sign Up",
            key="auth_tab_signup",
            use_container_width=True,
            disabled=(active_view == "signup"),
        ):
            set_auth_view("signup")
            st.rerun()

    with col_login:
        if st.button(
            "Login",
            key="auth_tab_login",
            use_container_width=True,
            disabled=(active_view == "login"),
        ):
            set_auth_view("login")
            st.rerun()


def _render_signup_form() -> None:
    """Renders the Sign Up form and handles registration submission."""
    st.markdown("<h2>Create your account</h2>", unsafe_allow_html=True)
    st.markdown(
        '<div class="auth-subtitle">Choose your role to unlock the right workspace.</div>',
        unsafe_allow_html=True,
    )

    with st.form("signup_form", clear_on_submit=False):
        role_label = st.radio(
            "I am a:",
            options=list(_ROLE_LABELS.keys()),
            horizontal=True,
            key="signup_role",
        )
        full_name = st.text_input("Full Name", key="signup_full_name")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input(
            "Confirm Password", type="password", key="signup_confirm_password"
        )
        submitted = st.form_submit_button("Create Account", use_container_width=True)

    if submitted:
        role = _ROLE_LABELS[role_label]
        success, message = register_user(full_name, email, password, confirm_password, role)
        if success:
            set_auth_view("login")
            set_signup_success_message(message)
            st.rerun()
        else:
            for error_line in message.split("\n"):
                st.error(error_line)

    st.markdown(
        '<div class="auth-footnote">Already have an account? Switch to the Login tab above.</div>',
        unsafe_allow_html=True,
    )


def _render_login_form() -> None:
    """Renders the Login form and handles authentication submission."""
    st.markdown("<h2>Welcome back</h2>", unsafe_allow_html=True)
    st.markdown(
        '<div class="auth-subtitle">Log in to continue to your workspace.</div>',
        unsafe_allow_html=True,
    )

    success_message = pop_signup_success_message()
    if success_message:
        st.success(success_message)

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Log In", use_container_width=True)

    if submitted:
        success, user, message = authenticate_user(email, password)
        if success:
            login(user)
            st.rerun()
        else:
            for error_line in message.split("\n"):
                st.error(error_line)

    st.markdown(
        '<div class="auth-footnote">New to TalentMatch AI? Switch to the Sign Up tab above.</div>',
        unsafe_allow_html=True,
    )


def render_landing_page() -> None:
    """Renders the full pre-authentication landing page: branding + auth card."""
    st.markdown('<div class="landing-wrapper">', unsafe_allow_html=True)
    brand_col, auth_col = st.columns([1.15, 1], gap="large")

    with brand_col:
        _render_brand_column()

    with auth_col:
        st.markdown('<div class="auth-panel">', unsafe_allow_html=True)
        _render_tab_switcher()

        if get_auth_view() == "signup":
            _render_signup_form()
        else:
            _render_login_form()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
