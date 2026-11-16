# =============================================================
# ui/styles.py
# TalentMatch AI - Global CSS Design System
# =============================================================
import streamlit as st

# NOTE: hero-banner, section-header, result-card, info-badge, and success-badge
# are relied on verbatim by ui/candidate_portal.py and ui/recruiter_portal.py.
# Do not rename or remove these classes without updating those modules.
_GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, .stText, .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, span {
    font-family: 'Inter', sans-serif !important;
}

.stApp {
    background: radial-gradient(circle at 15% 10%, #1b1440 0%, #0a0c16 45%, #05060a 100%);
    color: #e2e8f0;
}

/* ---------------------------------------------------------------
   EXISTING WORKSPACE COMPONENTS (retained for portal compatibility)
--------------------------------------------------------------- */
.hero-banner {
    background: linear-gradient(135deg, #181336 0%, #111625 100%);
    border: 1px solid #261f52;
    border-radius: 12px;
    padding: 40px;
    text-align: center;
    margin-bottom: 30px;
}

.section-header {
    font-size: 1.6rem;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 15px;
    border-bottom: 1px solid #222638;
    padding-bottom: 12px;
    letter-spacing: -0.02em;
}

.result-card {
    background: #141724;
    border: 1px solid #222638;
    border-radius: 8px;
    padding: 24px;
    margin: 16px 0;
}

.info-badge {
    background: #191e2e;
    border: 1px solid #2b354f;
    border-radius: 6px;
    padding: 14px 18px;
    font-size: 0.9rem;
    color: #94a3b8;
    line-height: 1.6;
    margin-bottom: 20px;
}

.success-badge {
    background: #064e3b;
    border: 1px solid #059669;
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 0.85rem;
    color: #a7f3d0;
    font-weight: 500;
    display: inline-block;
}

[data-testid="stSidebar"] {
    background: #0b0d14;
    border-right: 1px solid #1c1f2e;
}

.stButton > button {
    background: #4f46e5;
    color: #ffffff;
    border: 1px solid #6366f1;
    border-radius: 6px;
    font-weight: 500;
    font-size: 0.95rem;
    padding: 12px 24px;
    transition: all 0.2s ease;
    width: 100%;
}

.stButton > button:hover {
    background: #4338ca;
    border-color: #4f46e5;
    color: #ffffff;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.25);
}

.stTextArea textarea, .stTextInput input {
    background-color: #141724 !important;
    border: 1px solid #222638 !important;
    color: #e2e8f0 !important;
    border-radius: 6px !important;
}

/* ---------------------------------------------------------------
   LANDING PAGE & AUTHENTICATION CARD
--------------------------------------------------------------- */
@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}

@keyframes pulseGlow {
    0%, 100% { opacity: 0.55; transform: scale(1); }
    50%      { opacity: 0.9;  transform: scale(1.05); }
}

.landing-wrapper {
    animation: fadeSlideIn 0.6s ease-out;
    padding-top: 1.5rem;
}

.brand-eyebrow {
    display: inline-block;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #a5b4fc;
    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.35);
    border-radius: 999px;
    padding: 6px 16px;
    margin-bottom: 22px;
}

.brand-title {
    font-size: 3.2rem;
    font-weight: 800;
    line-height: 1.08;
    letter-spacing: -0.03em;
    margin: 0 0 14px 0;
    background: linear-gradient(120deg, #ffffff 0%, #c7d2fe 45%, #818cf8 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

.brand-tagline {
    font-size: 1.2rem;
    font-weight: 500;
    color: #cbd5e1;
    margin-bottom: 18px;
}

.brand-description {
    font-size: 1rem;
    line-height: 1.75;
    color: #94a3b8;
    max-width: 520px;
    margin-bottom: 34px;
}

.feature-pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 40px;
}

.feature-pill {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 0.85rem;
    color: #cbd5e1;
}

/* CSS-only abstract AI network visual */
.ai-visual {
    position: relative;
    width: 100%;
    max-width: 420px;
    height: 260px;
    margin-top: 10px;
}

.ai-node {
    position: absolute;
    border-radius: 50%;
    background: radial-gradient(circle at 35% 30%, #a5b4fc, #6366f1 60%, transparent 100%);
    box-shadow: 0 0 30px rgba(99, 102, 241, 0.45);
    animation: pulseGlow 3.4s ease-in-out infinite;
}

.ai-node.n1 { width: 90px;  height: 90px;  top: 10px;  left: 30px;  animation-delay: 0s; }
.ai-node.n2 { width: 56px;  height: 56px;  top: 130px; left: 0px;   animation-delay: 0.6s; background: radial-gradient(circle at 35% 30%, #f0abfc, #a855f7 60%, transparent 100%); box-shadow: 0 0 24px rgba(168, 85, 247, 0.4); }
.ai-node.n3 { width: 70px;  height: 70px;  top: 60px;  left: 220px; animation-delay: 1.1s; }
.ai-node.n4 { width: 44px;  height: 44px;  top: 190px; left: 260px; animation-delay: 1.7s; background: radial-gradient(circle at 35% 30%, #f0abfc, #a855f7 60%, transparent 100%); box-shadow: 0 0 24px rgba(168, 85, 247, 0.4); }
.ai-node.n5 { width: 34px;  height: 34px;  top: 20px;  left: 340px; animation-delay: 2.3s; }

.ai-link {
    position: absolute;
    background: linear-gradient(90deg, rgba(165, 180, 252, 0.55), rgba(168, 85, 247, 0.15));
    height: 2px;
    transform-origin: left center;
}

.ai-link.l1 { top: 75px;  left: 95px;  width: 150px; transform: rotate(18deg); }
.ai-link.l2 { top: 155px; left: 55px;  width: 210px; transform: rotate(-12deg); }
.ai-link.l3 { top: 95px;  left: 280px; width: 100px; transform: rotate(35deg); }

.auth-panel {
    background: rgba(20, 22, 36, 0.72);
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 20px;
    padding: 38px 36px 30px 36px;
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.45);
    animation: fadeSlideIn 0.7s ease-out;
}

.auth-panel h2 {
    font-size: 1.5rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 4px;
}

.auth-panel .auth-subtitle {
    font-size: 0.9rem;
    color: #94a3b8;
    margin-bottom: 26px;
}

.auth-tab-row {
    display: flex;
    gap: 8px;
    margin-bottom: 24px;
}

div[data-testid="stButton"] button.auth-tab-active {
    background: #4f46e5 !important;
}

.stRadio > div {
    gap: 6px;
}

.auth-footnote {
    font-size: 0.78rem;
    color: #64748b;
    margin-top: 22px;
    text-align: center;
}

/* Sidebar identity card */
.sidebar-identity {
    background: rgba(99, 102, 241, 0.08);
    border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 18px;
}

.sidebar-identity .name {
    font-size: 1rem;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 2px;
}

.sidebar-identity .email {
    font-size: 0.82rem;
    color: #94a3b8;
    margin-bottom: 10px;
    word-break: break-all;
}

.sidebar-identity .role-badge {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #c4b5fd;
    background: rgba(139, 92, 246, 0.15);
    border: 1px solid rgba(139, 92, 246, 0.35);
    border-radius: 999px;
    padding: 4px 12px;
}

@media (max-width: 900px) {
    .brand-title { font-size: 2.3rem; }
    .ai-visual { height: 200px; }
}
</style>
"""


def inject_global_styles() -> None:
    """Injects the shared TalentMatch AI CSS design system into the page."""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)
