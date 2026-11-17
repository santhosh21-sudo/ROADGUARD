"""
ROADGUARD - User Profile & Account Settings Section
Displays user profile credentials, Safety Karma rank progression bar,
role configuration, security statistics, and session logout controls.
"""

import streamlit as st
from config import USER_ROLES, USER_RANKS, THEME_COLORS
from auth import get_current_user, is_authenticated, logout_user, switch_demo_user
from database import get_user_submitted_reports
from supabase_client import is_supabase_configured

def render_profile_page():
    """Renders the comprehensive User Profile, Civic Karma Rank, and Security Section."""
    if not is_authenticated():
        st.warning("Please sign in to view your profile.")
        return

    user = get_current_user()
    role_key = user.get("role", "viewer")
    role_meta = USER_ROLES.get(role_key, USER_ROLES["viewer"])
    user_reports = get_user_submitted_reports(user.get("username", ""))

    # Header Banner
    st.markdown(
        f"""<div class="rg-card" style="border-left: 5px solid {THEME_COLORS['accent_green']};">
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
<div>
<h2 style="margin:0; color:#1E3A8A;">👤 User Profile & Civic Standing</h2>
<p style="margin:4px 0 0 0; color:#475569;">
Manage your ROADGUARD credentials, monitor Safety Karma ranking, and toggle role perspectives.
</p>
</div>
<div>
<span class="rg-badge" style="background:#ECFDF5; color:#065F46; border:1px solid #A7F3D0; font-size:13px; padding:6px 14px;">
{role_meta['icon']} ACTIVE ROLE: {role_meta['label'].upper()}
</span>
</div>
</div>
</div>""",
        unsafe_allow_html=True
    )

    col_profile, col_rank = st.columns([1.2, 1.4])

    # 1. User Identity & Role Card
    with col_profile:
        st.markdown("#### 🪪 Identity & Credentials")
        st.markdown(
            f"""<div class="rg-card">
<div style="display:flex; align-items:center; gap:16px; margin-bottom:14px;">
<div style="font-size:48px; background:#EFF6FF; border:1px solid #BFDBFE; border-radius:50%; width:72px; height:72px; display:flex; align-items:center; justify-content:center;">
{user.get('avatar_icon', '👤')}
</div>
<div>
<h3 style="margin:0; color:#1E3A8A; font-size:20px;">{user.get('full_name', 'Commuter')}</h3>
<div style="color:#64748B; font-size:13px;">@{user.get('username', 'user')}</div>
<div style="color:#2563EB; font-size:13px; font-weight:600; margin-top:2px;">{user.get('email', '')}</div>
</div>
</div>
<div style="border-top:1px solid #E2E8F0; padding-top:12px;">
<div style="font-size:12px; color:#64748B; font-weight:700; text-transform:uppercase;">CURRENT PERMISSIONS</div>
<div style="margin-top:4px; font-size:13px; color:#334155; line-height:1.5;">
{role_meta['description']}
</div>
</div>
<div style="margin-top:14px; background:#F8FAFC; border-radius:8px; padding:10px 14px; font-size:12px; color:#475569;">
<span>Member since: <b>{user.get('created_at', '2026-01-01')[:10]}</b></span> &bull;
<span>Account: <b>Verified Active</b></span>
</div>
</div>""",
            unsafe_allow_html=True
        )

    # 2. Civic Safety Karma & Ranks
    with col_rank:
        st.markdown("#### 🏆 Safety Karma & Civic Rank")

        karma = user.get("karma_points", 25)
        # Calculate rank progression
        current_rank = user.get("badge", "🌱 Novice Scout")
        next_rank_points = 100
        for r in USER_RANKS:
            if karma >= r["min_points"]:
                current_rank = f"{r['badge']} {r['name']}"
            else:
                next_rank_points = r["min_points"]
                break

        progress_pct = min(100, int((karma / float(next_rank_points)) * 100))

        st.markdown(
            f"""<div class="rg-card">
<div style="display:flex; justify-content:space-between; align-items:center;">
<div>
<div style="font-size:12px; font-weight:700; color:#64748B; text-transform:uppercase;">CURRENT CIVIC RANK</div>
<div style="font-size:24px; font-weight:800; color:#059669; margin-top:2px;">{current_rank}</div>
</div>
<div style="text-align:right;">
<div style="font-size:32px; font-weight:800; color:#D97706;">⭐ {karma}</div>
<div style="font-size:11px; color:#64748B;">Karma Points</div>
</div>
</div>
<div style="margin-top:14px;">
<div style="display:flex; justify-content:space-between; font-size:12px; color:#475569; margin-bottom:4px;">
<span>Rank Progression</span>
<span><b>{karma}</b> / {next_rank_points} pts</span>
</div>
<div style="background:#E2E8F0; border-radius:9999px; height:10px; overflow:hidden;">
<div style="background:linear-gradient(90deg, #10B981, #059669); width:{progress_pct}%; height:100%; border-radius:9999px;"></div>
</div>
</div>
<div style="display:flex; justify-content:space-between; margin-top:16px; border-top:1px solid #E2E8F0; padding-top:12px;">
<div style="text-align:center;">
<div style="font-size:18px; font-weight:700; color:#1E40AF;">{len(user_reports)}</div>
<div style="font-size:11px; color:#64748B;">Reports Filed</div>
</div>
<div style="text-align:center;">
<div style="font-size:18px; font-weight:700; color:#059669;">{sum(r.get('upvotes', 0) for r in user_reports)}</div>
<div style="font-size:11px; color:#64748B;">Upvotes Received</div>
</div>
<div style="text-align:center;">
<div style="font-size:18px; font-weight:700; color:#D97706;">+25</div>
<div style="font-size:11px; color:#64748B;">Pts Per Report</div>
</div>
</div>
</div>""",
            unsafe_allow_html=True
        )

    # 3. Role Perspective Switcher (College Demo Enabler)
    st.markdown("#### 🔄 Role Perspective Switcher (Presentation Tool)")
    st.caption("Quickly toggle between different user perspectives for classroom and evaluation demos:")

    c_r1, c_r2, c_r3, c_r4 = st.columns(4)

    with c_r1:
        if st.button("📢 Switch to Reporter (Alice)", use_container_width=True, key="prof_alice"):
            switch_demo_user("alice")
            st.rerun()

    with c_r2:
        if st.button("👀 Switch to Viewer (Bob)", use_container_width=True, key="prof_bob"):
            switch_demo_user("viewer_bob")
            st.rerun()

    with c_r3:
        if st.button("🏛️ Switch to Authority (Officer)", use_container_width=True, key="prof_officer"):
            switch_demo_user("officer_bob")
            st.rerun()

    with c_r4:
        if st.button("🚨 Switch to Emergency (Charlie)", use_container_width=True, key="prof_charlie"):
            switch_demo_user("patrol_charlie")
            st.rerun()

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # 4. Account Security & Session Management Section
    st.markdown("#### 🔐 Account Security & Session Vault")

    col_sec, col_logout = st.columns([1.5, 1.0])

    with col_sec:
        supa_status = "Connected (Cloud PostgreSQL)" if is_supabase_configured() else "Local Persistent SQLite Vault"
        st.markdown(
            f"""<div class="rg-card">
<table style="width:100%; font-size:13px; border-collapse:collapse;">
<tr style="border-bottom:1px solid #E2E8F0;">
<td style="padding:6px 0; font-weight:600; color:#475569;">Authentication Engine</td>
<td style="padding:6px 0; color:#1E40AF; font-weight:700;">Supabase GoTrue Auth</td>
</tr>
<tr style="border-bottom:1px solid #E2E8F0;">
<td style="padding:6px 0; font-weight:600; color:#475569;">Database Connection</td>
<td style="padding:6px 0; color:#059669; font-weight:700;">{supa_status}</td>
</tr>
<tr style="border-bottom:1px solid #E2E8F0;">
<td style="padding:6px 0; font-weight:600; color:#475569;">Session Persistence</td>
<td style="padding:6px 0; color:#10B981; font-weight:700;">Active (Browser Refresh F5 Safe)</td>
</tr>
<tr>
<td style="padding:6px 0; font-weight:600; color:#475569;">Password Protection</td>
<td style="padding:6px 0; color:#334155;">Encrypted SHA-256 / GoTrue Bcrypt</td>
</tr>
</table>
</div>""",
            unsafe_allow_html=True
        )

    with col_logout:
        st.markdown(
            """<div class="rg-card" style="border-left: 4px solid #DC2626; text-align:center;">
<div style="font-weight:700; color:#991B1B; font-size:14px; margin-bottom:4px;">End Session</div>
<p style="font-size:12px; color:#64748B; margin-bottom:12px;">
Safely log out of ROADGUARD, invalidate current authentication tokens, and return to the gateway.
</p>
</div>""",
            unsafe_allow_html=True
        )

        if st.button("🚪 Log Out of ROADGUARD", type="primary", use_container_width=True, key="profile_logout_btn"):
            logout_user()
