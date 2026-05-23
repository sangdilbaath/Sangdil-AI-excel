"""
Home.py — Nexus Excel AI · Landing Page
Entry point: email & password capture → redirect to Trial or App.
"""

import streamlit as st
import sys, os, time, re, hmac
sys.path.insert(0, os.path.dirname(__file__))

# ── Updated Imports (Fixed for Supabase / Expiry Dates & Stub Cleaned) ───────
from database import verify_or_create_user, activate_plan, is_account_expired
from styles import GLOBAL_CSS

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus Excel AI — Home",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
/* Landing-specific */
.hero-landing {
    text-align: center;
    padding: 5rem 1rem 3rem 1rem;
    animation: fadeUp 0.4s ease both;
}
.hero-badge {
    display: inline-block;
    background: var(--accent-dim);
    border: 1px solid var(--accent-dim);
    border-radius: 20px;
    padding: 0.3rem 1rem;
    font-size: 0.75rem;
    color: var(--accent);
    font-family: var(--font-mono);
    letter-spacing: 2px;
    margin-bottom: 1.5rem;
    text-transform: uppercase;
}
.hero-h1 {
    font-family: var(--font-mono);
    font-size: clamp(2.5rem, 6vw, 4.5rem);
    color: var(--text-primary);
    line-height: 1.1;
    margin: 0 0 1rem 0;
}
.hero-h1 span { color: var(--accent); }
.hero-p {
    color: var(--text-muted);
    font-size: 1.15rem;
    max-width: 560px;
    margin: 0 auto 2.5rem auto;
    line-height: 1.7;
}
.email-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.4);
}
.email-card-title {
    font-family: var(--font-mono);
    font-size: 1rem;
    color: var(--text-primary);
    margin-bottom: 0.35rem;
}
.email-card-sub {
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-bottom: 1.25rem;
}

/* Feature strip */
.feature-strip {
    display: flex;
    justify-content: center;
    gap: 2.5rem;
    flex-wrap: wrap;
    margin: 4rem auto 2rem auto;
    max-width: 900px;
    padding: 0 1rem;
}
.feature-item {
    text-align: center;
    flex: 1;
    min-width: 160px;
    max-width: 220px;
    animation: fadeUp 0.4s ease 0.15s both;
}
.feature-icon { font-size: 2.2rem; margin-bottom: 0.75rem; }
.feature-title { font-family: var(--font-mono); font-size: 0.85rem; color: var(--text-primary); margin-bottom: 0.35rem; }
.feature-desc  { font-size: 0.8rem; color: var(--text-muted); line-height: 1.5; }

/* Trusted bar */
.trust-bar {
    text-align: center;
    margin-top: 3rem;
    padding: 1.5rem;
    border-top: 1px solid var(--border);
}
.trust-bar p { font-size: 0.78rem; color: var(--text-muted); letter-spacing: 1px; text-transform: uppercase; }
.trust-pills { display: flex; justify-content: center; gap: 1.5rem; flex-wrap: wrap; margin-top: 0.75rem; }
.trust-pill {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.35rem 1rem;
    font-size: 0.72rem;
    font-family: var(--font-mono);
    color: var(--text-muted);
}
</style>
""", unsafe_allow_html=True)

# ── Session State Initialisation ──────────────────────────────
if "login_attempts" not in st.session_state:
    st.session_state["login_attempts"] = 0

# ── If already logged in + paid + active → go straight to app ─
if st.session_state.get("user") and st.session_state["user"].get("has_payment_on_file"):
    if not is_account_expired(st.session_state["user"]):
        st.switch_page("pages/3_App.py")

# ── Hero Section (Gemini text removed) ────────────────────────
st.markdown("""
<div class="hero-landing">
    <div class="hero-badge">◈ Powered By Nexus</div>
    <h1 class="hero-h1">Your Spreadsheets,<br><span>Supercharged by AI.</span></h1>
    <p class="hero-p">
        Upload any CSV or Excel file and ask questions in plain English —
        or by voice. Nexus writes, runs, and explains Python analysis
        instantly.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Login / Master Key Section ────────────────────────────────
_, col_card, _ = st.columns([1, 1.6, 1])
with col_card:
    tab_user, tab_admin = st.tabs(["🚀 User Login", "👑 Master Key"])
    
    with tab_user:
        st.markdown("""
        <div class="email-card">
            <div class="email-card-title">Get started or Log in</div>
            <div class="email-card-sub">Enter your email and password to access your account.</div>
            <br>
        """, unsafe_allow_html=True)

        email_input = st.text_input(
            "Email",
            placeholder="you@company.com",
            key="user_email"
        )
        password_input = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="user_password"
        )

        st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
        go_btn = st.button("Continue  →", use_container_width=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

        if go_btn:
            raw_email = email_input.strip().lower()
            raw_pass = password_input.strip()
            
            # Rate limiting check before calling DB
            if st.session_state.get("login_attempts", 0) >= 5:
                st.error("⛔ Too many failed attempts. Please refresh the page.")
                st.stop()
            
            # 1. Validation using strict standard email pattern
            email_pattern = r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+$"
            
            if not re.match(email_pattern, raw_email):
                st.error("⚠️ Please enter a valid email address.")
            elif not raw_pass:
                st.error("⚠️ Please enter a password.")
            else:
                domain = raw_email.split('@')[-1]
                blocked_domains = ["test.com", "example.com", "fake.com", "mailinator.com", "tempmail.com"]
                
                if domain in blocked_domains:
                    st.error("⚠️ Please use a real personal or work email address.")
                else:
                    # 2. Check Database via Supabase
                    with st.spinner("Authenticating securely..."):
                        user = verify_or_create_user(raw_email, raw_pass)
                        time.sleep(0.5)

                    if user is False:
                        st.session_state["login_attempts"] = st.session_state.get("login_attempts", 0) + 1
                        st.error(f"❌ Incorrect password for this email. (Attempt {st.session_state['login_attempts']}/5)")
                    else:
                        # Reset brute force rate limit counter on successful login
                        st.session_state["login_attempts"] = 0
                        
                        # 3. Successful Login / Account Creation
                        st.session_state["email"] = raw_email
                        st.session_state["user"]  = user

                        # If they are a returning active user, send to App
                        if user.get("has_payment_on_file"):
                            if not is_account_expired(user):
                                st.switch_page("pages/3_App.py")

                        # If they are brand new (or expired), send them to start a trial
                        st.switch_page("pages/1_Start_Trial.py")

    with tab_admin:
        st.markdown("""
        <div class="email-card">
            <div class="email-card-title">Admin Access</div>
            <div class="email-card-sub">Strictly restricted to authorized administrator. Bypasses all limits.</div>
            <br>
        """, unsafe_allow_html=True)
        
        admin_email = st.text_input("Admin Email", placeholder="admin@domain.com", key="admin_email")
        admin_pass = st.text_input("Password", type="password", key="admin_pass")

        st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
        admin_btn = st.button("Unlock Dashboard  →", use_container_width=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

        if admin_btn:
            clean_email = admin_email.strip().lower()
            
            # Fetch admin credentials from secrets ONLY - No source-code fallbacks.
            expected_admin_email = st.secrets.get("ADMIN_EMAIL")
            expected_admin_pass  = st.secrets.get("ADMIN_PASS")
            
            if not expected_admin_email or not expected_admin_pass:
                st.error("❌ Critical Security Block: Admin credentials are not configured in Streamlit Secrets.")
            else:
                # Timing-safe comparison using hmac.compare_digest
                email_ok = hmac.compare_digest(clean_email, expected_admin_email.lower())
                pass_ok  = hmac.compare_digest(admin_pass, expected_admin_pass)
                
                if email_ok and pass_ok:
                    # Master User Dictionary
                    master_user = {
                        "email": clean_email,
                        "plan_type": "pro",
                        "has_payment_on_file": True,
                        "expiry_date": None
                    }
                    
                    st.session_state["email"] = clean_email
                    st.session_state["user"] = master_user
                    st.session_state["is_admin"] = True
                    
                    st.success("✅ Master Key Accepted! Booting Admin Portal...")
                    time.sleep(1.2)
                    st.switch_page("pages/4_Admin_Portal.py")
                else:
                    st.error("❌ Access Denied: Unrecognized email or incorrect password.")

# ── Feature Strip (Gemini text removed) ───────────────────────
st.markdown("""
<div class="feature-strip">
    <div class="feature-item">
        <div class="feature-icon">🧠</div>
        <div class="feature-title">AI Data Analyst</div>
        <div class="feature-desc">Ask anything. Nexus writes and runs the Python for you.</div>
    </div>
    <div class="feature-item">
        <div class="feature-icon">🎙️</div>
        <div class="feature-title">Voice Commands</div>
        <div class="feature-desc">Speak your analysis — microphone input with instant transcription.</div>
    </div>
    <div class="feature-item">
        <div class="feature-icon">📈</div>
        <div class="feature-title">Instant Charts</div>
        <div class="feature-desc">Ask for a bar, line, or scatter chart — rendered in seconds.</div>
    </div>
    <div class="feature-item">
        <div class="feature-icon">⚡</div>
        <div class="feature-title">Zero Setup</div>
        <div class="feature-desc">Upload CSV or Excel, type your question. That's it.</div>
    </div>
</div>

<div class="trust-bar">
    <p>Trusted features</p>
    <div class="trust-pills">
        <span class="trust-pill">Cloud DB Auth</span>
        <span class="trust-pill">Feature Gating</span>
        <span class="trust-pill">Trial Management</span>
        <span class="trust-pill">Secure Exec Engine</span>
        <span class="trust-pill">Export CSV / Excel</span>
    </div>
</div>
""", unsafe_allow_html=True)
