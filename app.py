"""
ROADGUARD - Main Application Entrypoint & System Orchestrator
Smart Road Hazard Reporting & Navigation System
Professional Blue, White, and Green Light Theme
Suitable for College Project Presentations & Academic Capstone Demonstrations
"""

import streamlit as st
import pandas as pd
import json

# Set Streamlit Page Configuration as first Streamlit call
st.set_page_config(
    page_title="ROADGUARD | Smart Road Hazard & Navigation",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Internal module imports
from config import (
    APP_NAME, APP_SUBTITLE, APP_VERSION, APP_SLOGAN,
    THEME_COLORS, HAZARD_CATEGORIES, SEVERITY_LEVELS,
    DEFAULT_CITIES, USER_ROLES, STATUS_METADATA
)
from database import (
    init_db, get_hazards, get_analytics_summary,
    get_leaderboard, update_hazard_status, get_hazard_by_id
)
from auth import (
    init_auth, get_current_user, render_auth_sidebar,
    has_role, is_authenticated, render_auth_gateway, logout_user
)
from utils import apply_custom_theme, time_ago
from map_view import render_map_page, HAS_FOLIUM
from reporting import render_reporting_page
from alerts import render_alerts_page
from reporter_dashboard import render_reporter_dashboard
from viewer_dashboard import render_viewer_dashboard
from route_planner import render_route_planning_view
from landing_page import render_landing_page
from my_reports import render_my_reports_page
from profile_page import render_profile_page

# Initialize SQLite database and tables
init_db()

# Initialize session state for authentication
init_auth()

# Inject modern custom stylesheet (Blue, White, Green light theme)
apply_custom_theme()

def render_top_banner():
    """Renders the primary header banner with live system health indicators."""
    user = get_current_user() if is_authenticated() else None

    user_badge_html = ""
    if user:
        role_label = user.get("role", "viewer").upper()
        user_badge_html = f"""
        <div style="display:inline-flex; align-items:center; gap:8px; background:rgba(255,255,255,0.18); padding:6px 14px; border-radius:30px; font-size:12px; font-weight:600; color:#FFFFFF;">
            <span>{user.get('avatar_icon', '👤')}</span>
            <span>{user.get('full_name', 'User')}</span>
            <span style="background:#ECFDF5; color:#065F46; padding:2px 8px; border-radius:9999px; font-size:11px; font-weight:700;">{role_label}</span>
        </div>
        """

    st.markdown(
        f"""
        <div class="rg-header">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                <div>
                    <h1 style="display:flex; align-items:center; gap:10px; margin:0;">
                        <span>🛡️</span> {APP_NAME}
                        <span style="font-size:13px; background:rgba(255,255,255,0.2); padding:3px 10px; border-radius:9999px; font-weight:600;">v{APP_VERSION}</span>
                    </h1>
                    <p style="margin:4px 0 0 0; color:#E0E7FF; font-size:14px;">{APP_SUBTITLE} &bull; {APP_SLOGAN}</p>
                </div>
                <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
                    {user_badge_html}
                    <div style="display:inline-flex; align-items:center; gap:8px; background:rgba(255,255,255,0.15); padding:6px 14px; border-radius:30px;">
                        <span style="height:10px; width:10px; background-color:#10B981; border-radius:50%; display:inline-block; box-shadow:0 0 8px #10B981;"></span>
                        <span style="font-size:13px; font-weight:600; color:#FFFFFF;">Highway Radar Live</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_kpi_cards():
    """Renders real-time platform metrics in a clean 4-column card row based on actual database reports."""
    stats = get_analytics_summary()
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class="rg-stat-box">
                <div class="rg-stat-value" style="color:#1E40AF;">{stats['total_hazards']}</div>
                <div class="rg-stat-label">Total Hazards Logged</div>
                <div style="font-size:12px; color:#2563EB; margin-top:4px; font-weight:600;">Database Verified</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div class="rg-stat-box red">
                <div class="rg-stat-value" style="color:#DC2626;">{stats['critical_hazards']}</div>
                <div class="rg-stat-label">Critical Alerts Active</div>
                <div style="font-size:12px; color:#DC2626; margin-top:4px; font-weight:600;">Immediate Detour Advised</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            f"""
            <div class="rg-stat-box amber">
                <div class="rg-stat-value" style="color:#D97706;">{stats['active_hazards']}</div>
                <div class="rg-stat-label">Active Obstructions</div>
                <div style="font-size:12px; color:#D97706; margin-top:4px; font-weight:600;">Pending or In Repair</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:
        st.markdown(
            f"""
            <div class="rg-stat-box green">
                <div class="rg-stat-value" style="color:#059669;">{stats['resolved_hazards']}</div>
                <div class="rg-stat-label">Restored Corridors</div>
                <div style="font-size:12px; color:#059669; margin-top:4px; font-weight:600;">Road Verified Repaired</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

def render_authority_portal():
    """
    Public Works & Highway Maintenance Operations Portal.
    Allows municipal road managers to inspect reports, dispatch crews, and resolve incidents.
    """
    user = get_current_user()

    st.markdown(
        """
        <div class="rg-card" style="border-left: 5px solid #1E40AF;">
            <h2 style="margin:0; color:#1E3A8A;">🏛️ Municipal Road Authority Operations Portal</h2>
            <p style="margin:4px 0 0 0; color:#475569;">
                Triage citizen road hazard reports, generate municipal work orders, dispatch public works maintenance crews, and log road restorations.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    hazards = get_hazards()

    # Operations KPI Row
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        rep_count = len([h for h in hazards if h["status"] == "Reported"])
        st.metric("Pending Triage", rep_count, delta="Requires review", delta_color="inverse")
    with col_k2:
        wo_count = len([h for h in hazards if h["status"] == "Work Order Dispatched"])
        st.metric("Crews Dispatched", wo_count)
    with col_k3:
        prog_count = len([h for h in hazards if h["status"] == "In Progress"])
        st.metric("Active Repairs", prog_count)
    with col_k4:
        res_count = len([h for h in hazards if h["status"] == "Resolved"])
        st.metric("Restored Corridors", res_count, delta="Completed")

    st.markdown("---")

    # Work Order Dispatch Queue
    st.markdown("#### 🚜 Road Maintenance Dispatch Queue")

    col_filter_status, col_filter_city = st.columns(2)
    with col_filter_status:
        view_status = st.selectbox(
            "Filter by Incident Workflow Status",
            ["All Active (Excl. Resolved)", "Reported", "Community Verified", "Work Order Dispatched", "In Progress", "Resolved"]
        )
    with col_filter_city:
        view_city = st.selectbox("Corridor Filter", ["All Corridors"] + list(DEFAULT_CITIES.keys()))

    filtered_list = hazards
    if view_status == "All Active (Excl. Resolved)":
        filtered_list = [h for h in filtered_list if h["status"] != "Resolved"]
    elif view_status != "All Active (Excl. Resolved)":
        filtered_list = [h for h in filtered_list if h["status"] == view_status]

    if view_city != "All Corridors":
        filtered_list = [h for h in filtered_list if h.get("city") == view_city]

    if not filtered_list:
        st.success("✅ No pending incidents matching criteria! All corridors clear.")
        return

    for h in filtered_list:
        sev_color = SEVERITY_LEVELS.get(h["severity"], {}).get("color", "#2563EB")
        status_color = STATUS_METADATA.get(h["status"], {}).get("color", "#2563EB")

        with st.expander(f"#{h['id']} [{h['severity'].upper()}] {h['title']} — Status: {h['status']}"):
            col_left, col_right = st.columns([1.2, 0.8])

            with col_left:
                st.write(f"**Location:** {h.get('address', 'N/A')} ({h.get('city', '')})")
                st.write(f"**GPS:** `{h['latitude']:.5f}, {h['longitude']:.5f}`")
                st.write(f"**Category:** {h['category']}")
                st.write(f"**Description:** {h.get('description', '')}")
                st.write(f"**Reported by:** {h['reporter_name']} ({time_ago(h.get('created_at', ''))})")
                st.write(f"**Community Trust:** 👍 {h['upvotes']} upvotes")

            with col_right:
                st.markdown("##### Dispatch & Status Management")
                new_status = st.selectbox(
                    "Update Incident Lifecycle Status",
                    ["Reported", "Community Verified", "Work Order Dispatched", "In Progress", "Resolved"],
                    index=["Reported", "Community Verified", "Work Order Dispatched", "In Progress", "Resolved"].index(h["status"]),
                    key=f"status_sel_{h['id']}"
                )
                work_code = st.text_input("Work Order ID (e.g. WO-NYC-8823)", value=h.get("work_order_id") or f"WO-CITY-{h['id']}", key=f"wo_{h['id']}")
                notes = st.text_area("Municipal Resolution / Dispatch Notes", value=h.get("resolution_notes") or "", key=f"notes_{h['id']}")

                if st.button("💾 Save Dispatch Updates", key=f"btn_upd_{h['id']}", type="primary"):
                    ok = update_hazard_status(h["id"], new_status, work_code, notes)
                    if ok:
                        st.success("Incident record updated!")
                        st.rerun()

def render_analytics_dashboard():
    """Renders roadway infrastructure reliability insights and civic leaderboard."""
    st.markdown(
        """
        <div class="rg-card" style="border-left: 5px solid #059669;">
            <h2 style="margin:0; color:#1E3A8A;">📊 Road Safety Intelligence & Hotspots Analytics</h2>
            <p style="margin:4px 0 0 0; color:#475569;">
                Data-driven insights into highway infrastructure reliability, recurring road damage hotspots, and civic leaderboard.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    stats = get_analytics_summary()

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("#### 🕳️ Incidents by Hazard Category")
        if stats["category_breakdown"]:
            df_cat = pd.DataFrame(stats["category_breakdown"])
            df_cat.columns = ["Hazard Category", "Incident Count"]
            st.bar_chart(df_cat.set_index("Hazard Category"), color="#1E40AF")
        else:
            st.info("No categorical data available.")

    with col_chart2:
        st.markdown("#### 🏙️ Incident Density by Hub Corridor")
        if stats["city_breakdown"]:
            df_city = pd.DataFrame(stats["city_breakdown"])
            df_city.columns = ["Corridor", "Count"]
            st.bar_chart(df_city.set_index("Corridor"), color="#059669")
        else:
            st.info("No city data available.")

    st.markdown("---")

    # Community Leaderboard
    st.markdown("#### 🏆 Civic Road Safety Leaderboard")
    st.caption("Citizens and officers honored for reporting hazards and verifying public safety:")

    leaderboard_data = get_leaderboard(limit=10)
    if leaderboard_data:
        cols_lb = st.columns([0.5, 1.5, 1.2, 1.2, 1.0])
        cols_lb[0].markdown("**Rank**")
        cols_lb[1].markdown("**Name & Role**")
        cols_lb[2].markdown("**Badge Rank**")
        cols_lb[3].markdown("**Safety Karma**")
        cols_lb[4].markdown("**Reports Filed**")

        for idx, lb in enumerate(leaderboard_data, 1):
            with st.container():
                medal = "🥇" if idx == 1 else ("🥈" if idx == 2 else ("🥉" if idx == 3 else f"#{idx}"))
                cols_entry = st.columns([0.5, 1.5, 1.2, 1.2, 1.0])
                cols_entry[0].markdown(f"**{medal}**")
                cols_entry[1].markdown(f"{lb.get('avatar_icon', '👤')} **{lb['full_name']}** (`{lb['username']}`)")
                cols_entry[2].markdown(f"{lb.get('badge', '🌱 Novice Scout')}")
                cols_entry[3].markdown(f"⭐ **{lb.get('karma_points', 0)} pts**")
                cols_entry[4].markdown(f"📝 {lb.get('reports_count', 0)}")

def main():
    """Main application orchestrator with Role-Based Access Control & Complete Multi-Page Navigation."""
    # Top branding banner
    render_top_banner()

    # If user is not yet authenticated, present the Landing Page alongside Authentication Portal
    if not is_authenticated():
        tab_welcome, tab_auth = st.tabs([
            "🏠 Welcome & Project Showcase",
            "🔐 Portal Login & Signup"
        ])
        with tab_welcome:
            render_landing_page()
        with tab_auth:
            render_auth_gateway()
        return

    # User is Authenticated
    user = get_current_user()
    user_role = user.get("role", "viewer") if user else "viewer"

    # Real-Time Platform KPI Cards
    render_kpi_cards()

    # Sidebar Navigation & Role Indicator
    st.sidebar.markdown(f"## 🛡️ {APP_NAME}")
    role_meta = USER_ROLES.get(user_role, USER_ROLES["viewer"])
    st.sidebar.markdown(
        f"""
        <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:8px; padding:6px 12px; margin-bottom:12px; font-size:12px; font-weight:700; color:#1E40AF;">
            {role_meta['icon']} ACTIVE ROLE: {role_meta['label'].upper()}
        </div>
        """,
        unsafe_allow_html=True
    )

    # Complete Navigation Menu covering all 9 required capabilities
    nav_options = [
        "🏠 Welcome & Project Overview",
        "📢 Reporter Dashboard",
        "👀 Viewer Dashboard",
        "➕ Report Road Hazard",
        "🗺️ Interactive Live Map",
        "🧭 Route Planner & Safe Navigation",
        "🚨 Road Alerts & Driver Mode HUD",
        "📋 My Submitted Reports",
        "👤 User Profile & Settings"
    ]

    # Additional Authority & Analytics options
    if user_role in ["authority", "emergency"]:
        nav_options.append("🏛️ Municipal Authority Portal")
    nav_options.append("📊 Analytics & Hotspots")

    # Set default navigation selection safely
    default_index = 0
    if "nav_index" in st.session_state and isinstance(st.session_state.nav_index, int):
        if 0 <= st.session_state.nav_index < len(nav_options):
            default_index = st.session_state.nav_index

    nav_selection = st.sidebar.radio("Navigation Menu", nav_options, index=default_index)

    # Render authenticated user info and demo switcher in sidebar
    render_auth_sidebar()

    # Route to selected page
    if nav_selection == "🏠 Welcome & Project Overview":
        render_landing_page()

    elif nav_selection == "📢 Reporter Dashboard":
        render_reporter_dashboard()

    elif nav_selection == "👀 Viewer Dashboard":
        render_viewer_dashboard()

    elif nav_selection == "➕ Report Road Hazard":
        render_reporting_page()

    elif nav_selection == "🗺️ Interactive Live Map":
        render_map_page()

    elif nav_selection == "🧭 Route Planner & Safe Navigation":
        render_route_planning_view()

    elif nav_selection == "🚨 Road Alerts & Driver Mode HUD":
        render_alerts_page()

    elif nav_selection == "📋 My Submitted Reports":
        render_my_reports_page()

    elif nav_selection == "👤 User Profile & Settings":
        render_profile_page()

    elif nav_selection == "🏛️ Municipal Authority Portal":
        render_authority_portal()

    elif nav_selection == "📊 Analytics & Hotspots":
        render_analytics_dashboard()

if __name__ == "__main__":
    main()
