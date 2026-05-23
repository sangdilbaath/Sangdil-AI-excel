"""
pages/4_Admin_Portal.py — Nexus Excel AI · Admin Portal
Admin dashboard for statistics, plan provisioning, and user control.
"""

import streamlit as st
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import get_admin_stats, admin_create_user, block_user_trial, PLAN_LABELS, supabase
from styles import GLOBAL_CSS

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus Excel AI — Admin Portal",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
.admin-badge {
    display: inline-block;
    background: #f8514922;
    border: 1px solid #f8514960;
    border-radius: 20px;
    padding: 0.3rem 1rem;
    font-size: 0.75rem;
    color: #f85149;
    font-family: var(--font-mono);
    letter-spacing: 2px;
    margin-bottom: 1.5rem;
    text-transform: uppercase;
    font-weight: bold;
}
.admin-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 30px rgba(0,0,0,0.3);
}
.admin-card-title {
    font-family: var(--font-mono);
    font-size: 1.15rem;
    color: var(--accent);
    margin-bottom: 0.75rem;
}
.admin-stat-row {
    display: flex;
    gap: 1.5rem;
    margin: 1rem 0;
    flex-wrap: wrap;
}
.admin-stat-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    flex: 1;
    min-width: 140px;
    text-align: center;
}
.admin-stat-val {
    font-family: var(--font-mono);
    font-size: 1.8rem;
    color: var(--text-primary);
    font-weight: 700;
}
.admin-stat-lbl {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 0.2rem;
}
</style>
""", unsafe_allow_html=True)

# ── Guards ────────────────────────────────────────────────────
if not st.session_state.get("is_admin", False):
    st.switch_page("Home.py")

st.markdown("""
<div style="text-align:center; padding: 2rem 0 1rem 0;">
    <div class="admin-badge">👑 Master Administrator Mode</div>
    <h2 style="font-family:'Space Mono',monospace; color:var(--text-primary); margin:0;">
        Nexus Control Panel
    </h2>
    <p style="color:var(--text-muted); font-size:0.875rem;">
        Monitor cloud accounts, provision licenses, and override service limits.
    </p>
</div>
""", unsafe_allow_html=True)

# Check database configuration
if not supabase:
    st.warning(
        "⚠️ Supabase integration is inactive. The admin controls will run in sandbox mode. "
        "Define SUPABASE_URL and SUPABASE_KEY in your secrets to hook into live accounts.",
        icon="⚠️"
    )

# ── Metrics Row ───────────────────────────────────────────────
st.markdown('<div class="section-label">Realtime Statistics</div>', unsafe_allow_html=True)
stats = get_admin_stats()
total_users = stats.get("total_users", 0)
plans = stats.get("plans", {})

st.markdown('<div class="admin-stat-row">', unsafe_allow_html=True)
cols_stats = st.columns(4)
with cols_stats[0]:
    st.markdown(f"""
    <div class="admin-stat-card">
        <div class="admin-stat-val">{total_users}</div>
        <div class="admin-stat-lbl">Registered Accounts</div>
    </div>
    """, unsafe_allow_html=True)
with cols_stats[1]:
    st.markdown(f"""
    <div class="admin-stat-card">
        <div class="admin-stat-val">{plans.get("trial", 0) + plans.get("free_trial", 0)}</div>
        <div class="admin-stat-lbl">Active Trials</div>
    </div>
    """, unsafe_allow_html=True)
with cols_stats[2]:
    st.markdown(f"""
    <div class="admin-stat-card">
        <div class="admin-stat-val">{plans.get("pro", 0)}</div>
        <div class="admin-stat-lbl">Pro Tiers</div>
    </div>
    """, unsafe_allow_html=True)
with cols_stats[3]:
    st.markdown(f"""
    <div class="admin-stat-card">
        <div class="admin-stat-val">{plans.get("none", 0)}</div>
        <div class="admin-stat-lbl">Free Tiers</div>
    </div>
    """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# ── Admin Forms ───────────────────────────────────────────────
col_prov, col_rev = st.columns(2)

with col_prov:
    st.markdown("""
    <div class="admin-card">
        <div class="admin-card-title">🚀 Provision User License</div>
        <p style="color:var(--text-muted); font-size:0.8rem; line-height:1.5; margin-bottom:1rem;">
            Register a new client or update an existing account plan and duration.
            Passwords are hashed automatically before write.
        </p>
    """, unsafe_allow_html=True)
    
    with st.form("provision_form", clear_on_submit=True):
        p_email = st.text_input("User Email", placeholder="client@company.com")
        p_pass = st.text_input("Temporary Password", placeholder="secure1234", type="password")
        p_plan = st.selectbox("Plan Tier", ["trial", "free_trial", "basic", "premium", "pro"])
        p_dur = st.number_input("License Duration (Days)", min_value=1, max_value=3650, value=30)
        
        prov_btn = st.form_submit_button("Grant Access license ➔", use_container_width=True)
        
        if prov_btn:
            if not p_email.strip() or not p_pass.strip():
                st.error("❌ Email and password are required to register an account.")
            elif not supabase:
                st.error("❌ Supabase inactive. Unable to provision in sandbox.")
            else:
                with st.spinner("Writing hashed credentials to database..."):
                    success = admin_create_user(
                        p_email.strip().lower(),
                        p_pass.strip(),
                        p_plan,
                        int(p_dur)
                    )
                if success:
                    st.success(f"✅ Success! Plan '{PLAN_LABELS[p_plan]}' assigned to {p_email}.")
                    time.sleep(1.0)
                    st.rerun()
                else:
                    st.error("❌ Database rejected entry. Double check table structure.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_rev:
    st.markdown("""
    <div class="admin-card">
        <div class="admin-card-title">🚫 Revoke Access / Block Trial</div>
        <p style="color:var(--text-muted); font-size:0.8rem; line-height:1.5; margin-bottom:1rem;">
            Instantly force an account trial to expire, immediately blocking access to the AI Workspace.
        </p>
    """, unsafe_allow_html=True)
    
    with st.form("revoke_form", clear_on_submit=True):
        r_email = st.text_input("Target User Email", placeholder="violator@company.com")
        revoke_btn = st.form_submit_button("Revoke Plan Access ➔", use_container_width=True)
        
        if revoke_btn:
            if not r_email.strip():
                st.error("❌ Please provide a target email address.")
            elif not supabase:
                st.error("❌ Supabase inactive. Unable to revoke in sandbox.")
            else:
                with st.spinner("Locking cloud trial record..."):
                    success = block_user_trial(r_email.strip().lower())
                if success:
                    st.success(f"✅ Account {r_email} has been successfully locked out.")
                    time.sleep(1.0)
                    st.rerun()
                else:
                    st.error("❌ Failed to revoke license. User may not exist.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
col_nav_left, col_nav_right = st.columns([8, 2])
with col_nav_right:
    if st.button("← Go to AI Dashboard", use_container_width=True):
        st.switch_page("pages/3_App.py")
