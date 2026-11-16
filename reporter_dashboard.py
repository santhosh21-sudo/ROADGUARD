"""
ROADGUARD - Reporter Dashboard & Incident Management Studio
Dedicated portal for ROLE 1: REPORTER
- Can submit road hazard reports with 6 standardized problem categories.
- Can upload road problem photos with Supabase Storage integration.
- Can pinpoint location (HTML5 GPS or manual address) and add detailed description.
- Can track submitted reports through municipal resolution lifecycle.
"""

import streamlit as st
from typing import Dict, Any
from config import THEME_COLORS, ROAD_PROBLEM_TYPES
from database import get_user_submitted_reports, get_hazards
from auth import get_current_user, can_submit_reports, switch_demo_user
from reporting import render_hazard_reporting_form
from my_reports import render_single_report_dossier

def render_reporter_dashboard():
    """Renders the comprehensive Reporter Operations Dashboard."""
    user = get_current_user()

    # Role-Based Access Control Check
    if not can_submit_reports():
        st.markdown(
            f"""
            <div class="rg-card" style="border-left: 5px solid #F59E0B;">
                <h3 style="margin:0; color:#92400E;">🔒 Reporter Role Required</h3>
                <p style="margin:6px 0 12px 0; color:#475569; font-size:14px;">
                    Your account is currently in <b>Viewer Role ({user.get('full_name', 'User')})</b>.<br>
                    Viewers have access to search approved reports and inspect pre-travel route safety.
                    To submit road hazard reports, upload problem photos, and track fixes, please switch to a <b>Reporter</b> profile.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("📢 Switch to Reporter Profile (Alice)", type="primary"):
            switch_demo_user("alice")
            st.rerun()
        return

    # Header Banner
    st.markdown(
        f"""
        <div class="rg-card" style="border-left: 5px solid {THEME_COLORS['primary_blue']};">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                <div>
                    <h2 style="margin:0; color:#1E3A8A;">📢 Reporter Dashboard & Hazard Studio</h2>
                    <p style="margin:4px 0 0 0; color:#475569;">
                        Submit live roadway obstructions, upload problem photos, pinpoint GPS coordinates, and track resolution progress.
                    </p>
                </div>
                <div>
                    <span class="rg-badge" style="background:#EFF6FF; color:#1D4ED8; border:1px solid #BFDBFE; font-size:13px; padding:6px 14px;">
                        📢 ROLE: REPORTER ({user.get('full_name', 'User')})
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Reporter KPI Row (Strictly from Real Database Reports)
    my_reports = get_user_submitted_reports(user.get("username", ""))
    verified_count = len([r for r in my_reports if r["status"] in ["Community Verified", "Work Order Dispatched", "In Progress"]])
    resolved_count = len([r for r in my_reports if r["status"] == "Resolved"])
    total_upvotes = sum(r.get("upvotes", 0) for r in my_reports)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("My Filed Reports", len(my_reports), delta=f"+{len(my_reports) * 25} Karma pts")
    with col2:
        st.metric("Community Verified", verified_count, delta="Confirmed on Radar")
    with col3:
        st.metric("Resolved by Public Works", resolved_count, delta="Roads Cleared")
    with col4:
        st.metric("Trust Upvotes Earned", total_upvotes, delta=f"⭐ {user.get('karma_points', 25)} Karma")

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # Tabs: Submit Report / Recent Submissions / Reporting Guidelines
    tab_submit, tab_my_reports, tab_guidelines = st.tabs([
        "📝 Submit Road Hazard Report",
        f"📋 My Submitted Reports ({len(my_reports)})",
        "💡 Reporter Guidelines & Best Practices"
    ])

    with tab_submit:
        render_hazard_reporting_form(user)

    with tab_my_reports:
        if not my_reports:
            st.info("You haven't filed any road hazard reports yet. Use the 'Submit Road Hazard Report' tab to report your first roadway issue!")
        else:
            st.markdown(f"**Showing all {len(my_reports)} hazard report(s) submitted by you:**")
            for r in my_reports:
                render_single_report_dossier(r)

    with tab_guidelines:
        st.markdown(
            f"""
            <div class="rg-card">
                <h4 style="margin:0 0 10px 0; color:#1E3A8A;">💡 How to Submit High-Impact Road Reports</h4>
                <div style="font-size:13px; color:#334155; line-height:1.6;">
                    <ul>
                        <li><b>Safety First:</b> Never use the application while driving. Pull over safely before filing a report or taking photos.</li>
                        <li><b>Accurate GPS Location:</b> Use the <i>Detect My Current Location</i> button or select the nearest recognizable cross-street or mile marker.</li>
                        <li><b>Clear Photo Evidence:</b> Take a landscape-oriented snapshot showing the road hazard in relation to traffic lanes and lane markings.</li>
                        <li><b>Correct Problem Category:</b> Select the closest category (e.g. <i>Pothole</i> for road craters, <i>Waterlogging</i> for standing flood pools, <i>Accident</i> for collisions).</li>
                        <li><b>Urgency / Severity:</b> Mark <i>Critical</i> only if the road is completely impassable or presents imminent physical danger to life.</li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
