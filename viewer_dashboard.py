"""
ROADGUARD - Viewer Dashboard
Dedicated portal for ROLE 2: VIEWER
- Can view all approved road reports.
- Can search for a location.
- Can view road hazard information.
- Can check reported road conditions before travelling.
"""

import streamlit as st
import json
from typing import Dict, Any, List
from config import (
    DEFAULT_CITIES, HAZARD_CATEGORIES, SEVERITY_LEVELS,
    THEME_COLORS, STATUS_METADATA
)
from database import get_approved_hazards, get_hazard_by_id
from auth import get_current_user
from utils import time_ago, export_hazards_csv
from route_planner import render_route_planning_view

# Preset commuter journeys for pre-travel checks
COMMUTER_JOURNEYS = {
    "New York: Brooklyn to Midtown Manhattan": {
        "start_name": "Cadman Plaza, Brooklyn",
        "start_coords": (40.6958, -73.9912),
        "end_name": "Times Square, Midtown",
        "end_coords": (40.7580, -73.9855),
        "city": "New York Metro, NY"
    },
    "New York: Queens (Flushing) to Lower Manhattan": {
        "start_name": "Flushing Meadows, Queens",
        "start_coords": (40.7498, -73.8407),
        "end_name": "Financial District, Manhattan",
        "end_coords": (40.7075, -74.0090),
        "city": "New York Metro, NY"
    },
    "San Francisco: Oakland to Downtown Financial District": {
        "start_name": "Downtown Oakland",
        "start_coords": (37.8044, -122.2712),
        "end_name": "Market & 1st St, SF",
        "end_coords": (37.7915, -122.3995),
        "city": "San Francisco Bay Area, CA"
    },
    "Austin: Round Rock to Downtown Austin": {
        "start_name": "Round Rock Crossing",
        "start_coords": (30.4900, -97.6800),
        "end_name": "Congress & 6th St, Austin",
        "end_coords": (30.2680, -97.7428),
        "city": "Austin Corridor, TX"
    },
    "Bangalore: Koramangala to Electronic City": {
        "start_name": "Koramangala Sony World",
        "start_coords": (12.9345, 77.6250),
        "end_name": "Electronic City Phase 1",
        "end_coords": (12.8399, 77.6770),
        "city": "Bangalore Highway Hub, IN"
    }
}

def render_viewer_dashboard():
    """Renders the comprehensive Viewer Pre-Travel & Inspection Dashboard."""
    user = get_current_user()

    # Header Banner
    st.markdown(
        f"""
        <div class="rg-card" style="border-left: 5px solid {THEME_COLORS['accent_green']};">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                <div>
                    <h2 style="margin:0; color:#1E3A8A;">👀 Viewer Dashboard & Travel Safety Inspector</h2>
                    <p style="margin:4px 0 0 0; color:#475569;">
                        Inspect approved road reports, search locations, and check reported road conditions before travelling.
                    </p>
                </div>
                <div>
                    <span class="rg-badge" style="background:#ECFDF5; color:#065F46; border:1px solid #A7F3D0; font-size:13px; padding:6px 14px;">
                        👀 ROLE: VIEWER ({user.get('full_name', 'Commuter')})
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_pretravel, tab_search, tab_map = st.tabs([
        "🧭 1. Check Road Conditions Before Travelling",
        "🔍 2. Search Locations & Approved Road Reports",
        "🗺️ 3. Interactive Hazards Map"
    ])

    with tab_pretravel:
        render_pretravel_checker()

    with tab_search:
        render_location_search_explorer()

    with tab_map:
        from map_view import render_map_page
        render_map_page()

def render_pretravel_checker():
    """Allows Viewers to check route road conditions, risk index, and advisories before departure."""
    render_route_planning_view()

def render_location_search_explorer():
    """Allows Viewers to search for a location and view all approved road reports."""
    st.markdown("#### 🔍 Search Locations & View Approved Road Reports")
    st.caption("Search across metropolitan corridors for verified road conditions, potholes, accidents, and closures.")

    # Search and Filter Controls
    col_search, col_city, col_cat, col_sev = st.columns([2, 1.2, 1.2, 1])

    with col_search:
        search_query = st.text_input(
            "Location or Keyword Search",
            placeholder="e.g. Brooklyn Bridge, FDR Drive, Austin, Pothole, Queens...",
            key="viewer_loc_search"
        )
    with col_city:
        selected_city = st.selectbox("Corridor Hub", ["All Cities"] + list(DEFAULT_CITIES.keys()), key="viewer_city")
    with col_cat:
        selected_cat = st.selectbox("Category", ["All Categories"] + list(HAZARD_CATEGORIES.keys()), key="viewer_cat")
    with col_sev:
        selected_sev = st.selectbox("Severity", ["All Severities", "Critical", "High", "Medium", "Low"], key="viewer_sev")

    # Fetch vetted reports
    hazards = get_approved_hazards(
        search_query=search_query,
        city=selected_city,
        category=selected_cat,
        severity=selected_sev
    )

    st.markdown(f"**Found {len(hazards)} Approved Road Report(s) matching your location search:**")

    if not hazards:
        st.info("No approved road reports match your search criteria. Try broadening your location search.")
        return

    # Render Hazard Dossiers
    for h in hazards:
        sev = h.get("severity", "Medium")
        sev_color = SEVERITY_LEVELS.get(sev, {}).get("color", "#2563EB")
        status_meta = STATUS_METADATA.get(h["status"], {"icon": "🛡️", "color": "#059669"})
        cat_meta = HAZARD_CATEGORIES.get(h["category"], {"icon": "⚠️"})

        with st.container():
            col_l, col_r = st.columns([1.5, 0.9])

            with col_l:
                st.markdown(
                    f"""
                    <div class="rg-card" style="border-left: 5px solid {sev_color};">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <span class="rg-badge badge-{sev.lower()}">{cat_meta['icon']} {sev.upper()}</span>
                                <span class="rg-badge" style="background:#ECFDF5; color:#065F46; border:1px solid #A7F3D0;">
                                    {status_meta['icon']} {h['status']}
                                </span>
                            </div>
                            <span style="font-size:11px; color:#64748B;">{time_ago(h.get('created_at', ''))}</span>
                        </div>
                        <h3 style="margin:10px 0 6px 0; color:#0F172A; font-size:17px;">{h['title']}</h3>
                        <div style="font-size:13px; color:#475569; margin-bottom:8px;">
                            📍 <b>{h.get('address', 'Location')}</b> ({h.get('city', '')})<br>
                            🌐 GPS: <code>{h['latitude']:.4f}, {h['longitude']:.4f}</code>
                        </div>
                        <div style="background:#F8FAFC; border-radius:6px; padding:10px; margin-bottom:8px; font-size:13px; color:#334155;">
                            {h.get('description', '')}
                        </div>
                        <div style="background:#ECFDF5; border:1px solid #A7F3D0; padding:6px 10px; border-radius:6px; font-size:12px; color:#065F46; margin-bottom:6px;">
                            <b>💡 Recommended Action:</b> {h.get('suggested_action', 'Proceed with caution.')}
                        </div>
                        {f"<div style='background:#EFF6FF; border:1px solid #BFDBFE; padding:6px 10px; border-radius:6px; font-size:12px; color:#1E40AF; margin-bottom:6px;'><b>Public Works Note:</b> {h['resolution_notes']}</div>" if h.get('resolution_notes') else ""}
                        <div style="font-size:11px; color:#64748B; display:flex; justify-content:space-between; margin-top:6px;">
                            <span>Reported by: <b>{h.get('reporter_name', 'Citizen')}</b></span>
                            <span>👍 {h['upvotes']} Community Verifications</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col_r:
                photo_url = h.get("photo_url")
                if photo_url and photo_url.startswith("http"):
                    st.image(photo_url, caption=f"Evidence Photo: {h['title'][:30]}...", use_container_width=True)
                else:
                    st.markdown(
                        """
                        <div style="background:#F1F5F9; border:1px dashed #CBD5E1; border-radius:8px; height:180px; display:flex; align-items:center; justify-content:center; text-align:center; color:#64748B; font-size:12px; padding:14px;">
                            📷 Official verification confirmed by community report.
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
