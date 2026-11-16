# =============================================================
# ui/sidebar.py
# TalentMatch AI - Authenticated Sidebar
# =============================================================
import streamlit as st

from auth.session import get_current_user, logout
from models.user import User


def render_authenticated_sidebar() -> None:
    """Renders the sidebar shown to logged-in users: identity, role, and logout."""
    user: User = get_current_user()

    with st.sidebar:
        st.title("TalentMatch AI")
        st.caption("GENERATIVE AI RECRUITMENT PLATFORM")
        st.markdown("---")

        st.markdown(
            f"""
            <div class="sidebar-identity">
                <div class="name">{user.full_name}</div>
                <div class="email">{user.email}</div>
                <span class="role-badge">{user.role}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Logout", key="sidebar_logout_button", use_container_width=True):
            logout()
            st.rerun()

        st.markdown("---")

        with st.expander("System Core Architecture Manual"):
            st.write(
                """
                This platform coordinates specialized asynchronous LangGraph structures to execute high-fidelity
                semantic parsing evaluations across variable input unstructured text data matrices.
                """
            )

        with st.expander("Infrastructure Technology Catalog"):
            st.markdown(
                """
                - **Pipeline Engine:** LangGraph Processing Core
                - **Model Framework:** Llama-3.3 Execution Stack
                - **Data Handling:** PyPDF Stream Text Translators
                - **Interface Wrapper:** Streamlit Matrix Components
                """
            )

        st.markdown("<br>" * 2, unsafe_allow_html=True)
        st.markdown(
            '<div class="success-badge" style="width:100%; text-align:center;">Edge Security Verified</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("Core System Version: Engine Build v1.5.0")
