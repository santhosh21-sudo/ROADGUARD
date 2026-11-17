"""
ROADGUARD - My Submitted Reports Page
Dedicated tracking page for reporters to inspect all hazard reports they have submitted,
track lifecycle status progression, review community verifications, and view municipal resolution notes.
"""

import streamlit as st
from typing import Dict, Any, List
from config import THEME_COLORS, SEVERITY_LEVELS, STATUS_METADATA, ROAD_PROBLEM_TYPES
from database import get_user_submitted_reports
from auth import get_current_user, is_authenticated, switch_demo_user
from utils import time_ago, export_hazards_csv

def render_my_reports_page():
    """Renders the comprehensive My Submitted Reports Page."""
    if not is_authenticated():
        st.warning("Please sign in to view your submitted road hazard reports.")
        return

    user = get_current_user()
    reports = get_user_submitted_reports(user.get("username", ""))

    # Header Banner
    st.markdown(
        f"""<div class="rg-card" style="border-left: 5px solid {THEME_COLORS['primary_blue']};">
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
<div>
<h2 style="margin:0; color:#1E3A8A;">📋 My Submitted Road Reports</h2>
<p style="margin:4px 0 0 0; color:#475569;">
Track verification progress, municipal work order dispatches, community upvotes, and resolution statuses for all your reports.
</p>
</div>
<div>
<span class="rg-badge" style="background:#EFF6FF; color:#1D4ED8; border:1px solid #BFDBFE; font-size:13px; padding:6px 14px;">
👤 {user.get('full_name', 'Reporter')} ({user.get('role', 'reporter').upper()})
</span>
</div>
</div>
</div>""",
        unsafe_allow_html=True
    )
    # If user is in Viewer role and has 0 reports, provide helpful role context
    if user.get("role") == "viewer" and not reports:
        st.info(
            "👀 **You are currently in Viewer Role.**\n\n"
            "Viewers primarily search approved reports and inspect route conditions. "
            "To submit road problem reports and track their lifecycle here, switch to the **Reporter** profile."
        )
        if st.button("📢 Switch to Reporter Profile (Alice)", type="primary"):
            switch_demo_user("alice")
            st.rerun()

    # KPI Metrics Row
    verified_count = len([r for r in reports if r["status"] in ["Community Verified", "Work Order Dispatched", "In Progress"]])
    dispatched_count = len([r for r in reports if r["status"] in ["Work Order Dispatched", "In Progress"]])
    resolved_count = len([r for r in reports if r["status"] == "Resolved"])
    total_upvotes = sum(r.get("upvotes", 0) for r in reports)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Filed Reports", len(reports), delta=f"+{len(reports) * 25} Karma pts")
    with col2:
        st.metric("Community Verified", verified_count, delta="Confirmed Active")
    with col3:
        st.metric("Crews Dispatched", dispatched_count, delta="Work Orders Active")
    with col4:
        st.metric("Resolved Corridors", resolved_count, delta=f"👍 {total_upvotes} Upvotes Earned")

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # Filter & Search Controls
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        status_filter = st.selectbox(
            "Filter by Lifecycle Status",
            ["All Reports", "Active / Pending", "Community Verified", "Work Order Dispatched", "In Progress", "Resolved"]
        )
    with col_f2:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        if reports:
            csv_data = export_hazards_csv(reports)
            st.download_button(
                "📥 Export My Reports (CSV)",
                data=csv_data,
                file_name=f"roadguard_my_reports_{user.get('username', 'user')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    # Apply filters
    filtered_reports = reports
    if status_filter == "Active / Pending":
        filtered_reports = [r for r in filtered_reports if r["status"] != "Resolved"]
    elif status_filter != "All Reports":
        filtered_reports = [r for r in filtered_reports if r["status"] == status_filter]

    st.markdown(f"**Displaying {len(filtered_reports)} of {len(reports)} submitted report(s):**")

    if not filtered_reports:
        st.markdown(
            """<div class="rg-card" style="text-align:center; padding:36px; color:#64748B;">
<div style="font-size:36px; margin-bottom:8px;">📝</div>
<h4 style="margin:0 0 6px 0; color:#334155;">No reports match the selected filter</h4>
<p style="font-size:13px; margin:0;">File a new road hazard report to begin earning Safety Karma and tracking roadway repairs.</p>
</div>""",
            unsafe_allow_html=True
        )

    # Render Report Dossiers with Visual Lifecycle Progression
    for r in filtered_reports:
        render_single_report_dossier(r)

def render_single_report_dossier(r: Dict[str, Any]):
    """Renders a single submitted report card with lifecycle step pipeline and photo."""
    status = r.get("status", "Reported")
    sev = r.get("severity", "Medium")
    sev_color = SEVERITY_LEVELS.get(sev, {}).get("color", "#2563EB")
    status_meta = STATUS_METADATA.get(status, {"icon": "📝", "color": "#2563EB"})
    cat_meta = ROAD_PROBLEM_TYPES.get(r.get("category"), {"icon": "⚠️"})

    # Lifecycle Step Pipeline
    steps = ["Reported", "Community Verified", "Work Order Dispatched", "In Progress", "Resolved"]
    current_idx = steps.index(status) if status in steps else 0

    pipeline_html = "<div style='display:flex; align-items:center; gap:6px; flex-wrap:wrap; margin:10px 0 14px 0;'>"
    for idx, step_name in enumerate(steps):
        is_done = idx <= current_idx
        is_current = idx == current_idx
        bg_col = "#059669" if is_done else "#E2E8F0"
        txt_col = "#FFFFFF" if is_done else "#64748B"
        border_col = "#047857" if is_current else "transparent"
        icon_step = "✓" if (is_done and not is_current) else (str(idx + 1))
        if is_current:
            icon_step = "▶"

        pipeline_html += f"<div style='display:inline-flex; align-items:center; gap:4px; background:{bg_col}; color:{txt_col}; padding:3px 10px; border-radius:14px; font-size:11px; font-weight:700; border:2px solid {border_col};'><span>{icon_step}</span><span>{step_name}</span></div>"
        if idx < len(steps) - 1:
            arrow_color = "#059669" if idx < current_idx else "#CBD5E1"
            pipeline_html += f"<span style='color:{arrow_color}; font-weight:800; font-size:12px;'>➔</span>"
    pipeline_html += "</div>"

    col_info, col_photo = st.columns([1.6, 0.9])

    with col_info:
        st.markdown(
            f"""<div class="rg-card" style="border-left: 5px solid {sev_color}; margin-bottom:14px;">
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
<div>
<span class="rg-badge badge-{sev.lower()}">{cat_meta['icon']} {sev.upper()} SEVERITY</span>
<span class="rg-badge" style="background:#EFF6FF; color:#1D4ED8; border:1px solid #BFDBFE;">
{status_meta['icon']} {status}
</span>
</div>
<span style="font-size:11px; color:#64748B;">{time_ago(r.get('created_at', ''))}</span>
</div>
<h3 style="margin:10px 0 4px 0; color:#0F172A; font-size:17px;">
#{r['id']} {r['title']}
</h3>
<div style="font-size:12px; color:#475569; margin-bottom:6px;">
📍 <b>{r.get('address', 'Location not specified')}</b> ({r.get('city', '')})<br>
🌐 Coordinates: <code>{r['latitude']:.4f}, {r['longitude']:.4f}</code>
</div>
{pipeline_html}
<div style="background:#F8FAFC; border-radius:6px; padding:10px; font-size:13px; color:#334155; margin-bottom:8px;">
{r.get('description', 'No additional details provided.')}
</div>
<div style="background:#ECFDF5; border:1px solid #A7F3D0; padding:6px 10px; border-radius:6px; font-size:12px; color:#065F46; margin-bottom:6px;">
<b>💡 Recommended Driver Action:</b> {r.get('suggested_action', 'Proceed with caution.')}
</div>
{f"<div style='background:#EFF6FF; border:1px solid #BFDBFE; padding:6px 10px; border-radius:6px; font-size:12px; color:#1E40AF; margin-bottom:6px;'><b>🚜 Work Order Dispatch:</b> Code <code>{r['work_order_id']}</code> — {r.get('resolution_notes', '')}</div>" if r.get('work_order_id') else ""}
<div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; color:#64748B; margin-top:8px;">
<span>Safety Reward: <b>+25 Karma Points</b></span>
<span>👍 <b>{r.get('upvotes', 0)} Community Confirmations</b></span>
</div>
</div>""",
            unsafe_allow_html=True
        )

    with col_photo:
        photo_url = r.get("photo_url")
        if photo_url and photo_url.startswith("http"):
            st.image(photo_url, caption=f"Evidence Photo: #{r['id']} {r['title'][:25]}", use_container_width=True)
        else:
            st.markdown(
                """<div style="background:#F1F5F9; border:1px dashed #CBD5E1; border-radius:8px; height:180px; display:flex; align-items:center; justify-content:center; text-align:center; color:#64748B; font-size:12px; padding:14px;">
📷 Photo evidence on file.
</div>""",
                unsafe_allow_html=True
            )
