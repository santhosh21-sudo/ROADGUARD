"""
ROADGUARD - Landing Page & Capstone Project Showcase
Modern, professional presentation landing page for college project demonstrations.
Features:
1. Hero presentation banner with live radar indicator and academic project credentials.
2. Real-time platform metrics powered directly by the permanent database.
3. Feature showcase cards covering reporting, interactive mapping, OSRM routing, and Driver HUD.
4. Technical architecture and engineering flow section.
5. Quick role launchpad and evaluator guidance.
"""

import streamlit as st
from config import APP_NAME, APP_SUBTITLE, APP_VERSION, THEME_COLORS, DEFAULT_CITIES, ROAD_PROBLEM_TYPES
from database import get_analytics_summary, get_hazards
from auth import is_authenticated, get_current_user, switch_demo_user

def render_landing_page():
    """Renders the comprehensive, attractive Landing & Project Showcase Page."""
    stats = get_analytics_summary()
    user = get_current_user() if is_authenticated() else None

    # Top Academic / Presentation Pill
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; margin-bottom:12px; gap:8px;">
            <div style="display:inline-flex; align-items:center; gap:8px; background:#EFF6FF; border:1px solid #BFDBFE; padding:6px 14px; border-radius:9999px; font-size:12px; font-weight:700; color:#1E40AF;">
                <span>🎓</span> ACADEMIC CAPSTONE PRESENTATION &bull; AI & GEOSPATIAL SMART CITY SYSTEMS
            </div>
            <div style="display:inline-flex; align-items:center; gap:6px; background:#ECFDF5; border:1px solid #A7F3D0; padding:6px 14px; border-radius:9999px; font-size:12px; font-weight:700; color:#065F46;">
                <span style="height:8px; width:8px; background:#10B981; border-radius:50%; display:inline-block; box-shadow:0 0 6px #10B981;"></span>
                <span>SYSTEM ONLINE &bull; v{APP_VERSION}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Hero Banner
    st.markdown(
        f"""
        <div class="rg-header" style="background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 50%, #065F46 100%);">
            <div style="max-width: 900px;">
                <div style="display:inline-block; background:rgba(255,255,255,0.18); padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600; margin-bottom:10px; letter-spacing:0.5px;">
                    SMART TRANSPORTATION INFRASTRUCTURE PLATFORM
                </div>
                <h1 style="font-size:38px; line-height:1.2; margin:0 0 10px 0; font-weight:800;">
                    🛡️ {APP_NAME}
                </h1>
                <p style="font-size:18px; line-height:1.5; color:#E0E7FF; margin:0 0 16px 0; font-weight:400;">
                    {APP_SUBTITLE}
                </p>
                <p style="font-size:14px; line-height:1.6; color:#CBD5E1; margin:0; max-width:820px;">
                    An intelligent civic engineering platform connecting everyday motorists, municipal public works departments, and emergency response teams.
                    Features crowd-sourced hazard detection, real-time photo verification, OSRM driving corridor buffer analysis, and vehicle proximity telemetry.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Live Statistics Grid (Strictly from Real Database Reports)
    st.markdown("### 📊 Live System Intelligence & Database Telemetry")
    st.caption("Real-time indicators calculated strictly from active database hazard reports:")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class="rg-stat-box">
                <div class="rg-stat-value" style="color:#1E40AF;">{stats['total_hazards']}</div>
                <div class="rg-stat-label">Total Road Hazards Logged</div>
                <div style="font-size:12px; color:#2563EB; margin-top:4px; font-weight:600;">Permanently Stored</div>
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
                <div style="font-size:12px; color:#DC2626; margin-top:4px; font-weight:600;">Immediate Detour Required</div>
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
                <div style="font-size:12px; color:#059669; margin-top:4px; font-weight:600;">Repaired by Public Works</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Core Capabilities & Interactive Architecture Grid
    st.markdown("### 🌟 Core Architectural Modules")
    st.caption("Key functional capabilities developed for this intelligent transportation system:")

    col_m1, col_m2, col_m3 = st.columns(3)

    with col_m1:
        st.markdown(
            f"""
            <div class="rg-card" style="border-top: 4px solid {THEME_COLORS['primary_blue']}; height: 100%;">
                <div style="font-size:28px; margin-bottom:8px;">📢</div>
                <h4 style="margin:0 0 6px 0; color:#1E3A8A;">1. Road Hazard Reporting Studio</h4>
                <p style="font-size:13px; color:#475569; line-height:1.5; margin:0 0 10px 0;">
                    Mobile-friendly citizen reporting wizard with automatic HTML5 GPS location, 6 standardized problem categories, camera photo upload, and live motorist alert preview.
                </p>
                <div style="display:flex; flex-wrap:wrap; gap:4px;">
                    <span class="rg-badge badge-low">🕳️ Potholes</span>
                    <span class="rg-badge badge-medium">🚧 Construction</span>
                    <span class="rg-badge badge-high">🌊 Flooding</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_m2:
        st.markdown(
            f"""
            <div class="rg-card" style="border-top: 4px solid {THEME_COLORS['accent_green']}; height: 100%;">
                <div style="font-size:28px; margin-bottom:8px;">🗺️</div>
                <h4 style="margin:0 0 6px 0; color:#065F46;">2. Folium Geospatial Radar</h4>
                <p style="font-size:13px; color:#475569; line-height:1.5; margin:0 0 10px 0;">
                    Interactive OpenStreetMap & Leaflet integration rendering custom categorical markers, real evidence photos inside click popups, proximity perimeter radar, and heatmaps.
                </p>
                <div style="display:flex; flex-wrap:wrap; gap:4px;">
                    <span class="rg-badge badge-status-resolved">📍 Locate GPS</span>
                    <span class="rg-badge badge-status-active">🔍 Location Search</span>
                    <span class="rg-badge" style="background:#F1F5F9; color:#334155;">🔥 Density Heatmap</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_m3:
        st.markdown(
            f"""
            <div class="rg-card" style="border-top: 4px solid #3B82F6; height: 100%;">
                <div style="font-size:28px; margin-bottom:8px;">🧭</div>
                <h4 style="margin:0 0 6px 0; color:#1E40AF;">3. OSRM Route Hazard Intelligence</h4>
                <p style="font-size:13px; color:#475569; line-height:1.5; margin:0 0 10px 0;">
                    Computes driving navigation corridors using OSRM, evaluates road hazard density along travel waypoints, distinguishes verified hazards, and provides safety advisories.
                </p>
                <div style="display:flex; flex-wrap:wrap; gap:4px;">
                    <span class="rg-badge badge-status-active">🛰️ OSRM Engine</span>
                    <span class="rg-badge badge-status-resolved">🛡️ Verified vs Citizen</span>
                    <span class="rg-badge" style="background:#EFF6FF; color:#1E40AF;">🔀 Smart Detour</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    col_m4, col_m5, col_m6 = st.columns(3)

    with col_m4:
        st.markdown(
            f"""
            <div class="rg-card" style="border-top: 4px solid #DC2626; height: 100%;">
                <div style="font-size:28px; margin-bottom:8px;">🚨</div>
                <h4 style="margin:0 0 6px 0; color:#991B1B;">4. Driver Mode & Proximity Radar</h4>
                <p style="font-size:13px; color:#475569; line-height:1.5; margin:0 0 10px 0;">
                    Tactical driver HUD providing 3-tier proximity safety envelopes (Critical &lt;350m, Warning 350-800m, Notice &lt;1.8km), Web Audio chime alerts, and SOS broadcasts.
                </p>
                <div style="display:flex; flex-wrap:wrap; gap:4px;">
                    <span class="rg-badge badge-critical">🔊 Audio Chime</span>
                    <span class="rg-badge badge-high">📡 Emergency SOS</span>
                    <span class="rg-badge" style="background:#FEE2E2; color:#991B1B;">⚡ 350m Critical Envelope</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_m5:
        st.markdown(
            f"""
            <div class="rg-card" style="border-top: 4px solid #7C3AED; height: 100%;">
                <div style="font-size:28px; margin-bottom:8px;">👥</div>
                <h4 style="margin:0 0 6px 0; color:#5B21B6;">5. Two-Role Access Control (RBAC)</h4>
                <p style="font-size:13px; color:#475569; line-height:1.5; margin:0 0 10px 0;">
                    Distinct dashboards tailored for Role 1: Reporter (submit, upload photos, track fixes) and Role 2: Viewer (inspect approved reports, pre-travel route checks).
                </p>
                <div style="display:flex; flex-wrap:wrap; gap:4px;">
                    <span class="rg-badge" style="background:#EFF6FF; color:#1D4ED8; border:1px solid #BFDBFE;">📢 Role 1: Reporter</span>
                    <span class="rg-badge" style="background:#ECFDF5; color:#065F46; border:1px solid #A7F3D0;">👀 Role 2: Viewer</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_m6:
        st.markdown(
            f"""
            <div class="rg-card" style="border-top: 4px solid #059669; height: 100%;">
                <div style="font-size:28px; margin-bottom:8px;">🏛️</div>
                <h4 style="margin:0 0 6px 0; color:#065F46;">6. Municipal Authority Portal</h4>
                <p style="font-size:13px; color:#475569; line-height:1.5; margin:0 0 10px 0;">
                    Public Works work order dispatching (`WO-NYC-8821`), incident lifecycle triage (`Reported` ➔ `Verified` ➔ `Dispatched` ➔ `In Progress` ➔ `Resolved`), and repair logging.
                </p>
                <div style="display:flex; flex-wrap:wrap; gap:4px;">
                    <span class="rg-badge badge-status-resolved">🚜 Crew Dispatch</span>
                    <span class="rg-badge badge-status-active">📋 Work Order Tracking</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Technology Stack & Academic Overview
    col_tech, col_eval = st.columns([1.4, 1.0])

    with col_tech:
        st.markdown("### 💻 Project Engineering & Technology Stack")
        st.markdown(
            f"""
            <div class="rg-card">
                <table style="width:100%; font-size:13px; border-collapse:collapse;">
                    <tr style="border-bottom:1px solid #E2E8F0;">
                        <td style="padding:8px 0; font-weight:700; color:#1E40AF; width:35%;">Application Framework</td>
                        <td style="padding:8px 0; color:#334155;">Python 3.10+ with Streamlit Web Architecture</td>
                    </tr>
                    <tr style="border-bottom:1px solid #E2E8F0;">
                        <td style="padding:8px 0; font-weight:700; color:#1E40AF;">Database & Storage</td>
                        <td style="padding:8px 0; color:#334155;">Supabase PostgreSQL (Cloud) with SQLite Local Replication</td>
                    </tr>
                    <tr style="border-bottom:1px solid #E2E8F0;">
                        <td style="padding:8px 0; font-weight:700; color:#1E40AF;">Authentication System</td>
                        <td style="padding:8px 0; color:#334155;">Supabase GoTrue JWT Auth, Google OAuth, Session Persistence</td>
                    </tr>
                    <tr style="border-bottom:1px solid #E2E8F0;">
                        <td style="padding:8px 0; font-weight:700; color:#1E40AF;">Geospatial Mapping</td>
                        <td style="padding:8px 0; color:#334155;">Folium, Leaflet.js, OpenStreetMap, HTML5 Geolocation API</td>
                    </tr>
                    <tr style="border-bottom:1px solid #E2E8F0;">
                        <td style="padding:8px 0; font-weight:700; color:#1E40AF;">Routing Engine</td>
                        <td style="padding:8px 0; color:#334155;">OSRM (Open Source Routing Machine) with Geometric Fallback</td>
                    </tr>
                    <tr>
                        <td style="padding:8px 0; font-weight:700; color:#1E40AF;">Auditory Telemetry</td>
                        <td style="padding:8px 0; color:#334155;">Web Audio API Frequency Synthesizer for Driver Proximity Chimes</td>
                    </tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_eval:
        st.markdown("### ⚡ Evaluator Quick Launchpad")
        st.markdown(
            f"""
            <div class="rg-card" style="background:#F8FAFC;">
                <div style="font-weight:700; color:#1E3A8A; font-size:14px; margin-bottom:6px;">
                    Test Different Role Perspectives:
                </div>
                <p style="font-size:12px; color:#64748B; margin-bottom:12px;">
                    Click any role below to instantly load the application from that user's perspective:
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        c_q1, c_q2 = st.columns(2)
        with c_q1:
            if st.button("📢 Alice (Reporter)", use_container_width=True, key="landing_alice"):
                switch_demo_user("alice")
            if st.button("🚨 Charlie (Emergency)", use_container_width=True, key="landing_charlie"):
                switch_demo_user("patrol_charlie")
        with c_q2:
            if st.button("👀 Bob (Viewer)", use_container_width=True, key="landing_bob"):
                switch_demo_user("viewer_bob")
            if st.button("🏛️ Officer Bob (Authority)", use_container_width=True, key="landing_officer"):
                switch_demo_user("officer_bob")
