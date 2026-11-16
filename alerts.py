"""
ROADGUARD - Smart Driver Mode & Proximity Radar System
Real-time hazard proximity warnings, tactical driver audio/visual alerts,
Emergency SOS broadcast, and municipal dispatcher notification feed.
"""

import streamlit as st
import time
from typing import Dict, Any, List
from config import THEME_COLORS, DEFAULT_CITIES, RADAR_ZONES
from database import (
    get_hazards, get_alerts, log_broadcast_alert
)
from auth import get_current_user, has_role
from utils import scan_proximity_hazards, haversine_distance, time_ago

# Simulated Driver Scenarios for instant evaluation
DRIVER_SCENARIOS = {
    "New York: Approaching Brooklyn Bridge (Accident Zone)": {
        "lat": 40.7075,
        "lng": -73.9985,
        "speed_mph": 35,
        "heading": "Manhattan Bound",
        "city": "New York Metro, NY"
    },
    "New York: Cruising FDR Drive (Pothole Proximity)": {
        "lat": 40.7320,
        "lng": -73.9730,
        "speed_mph": 45,
        "heading": "Northbound",
        "city": "New York Metro, NY"
    },
    "San Francisco: CA-1 Great Highway (Mudslide Sector)": {
        "lat": 37.7565,
        "lng": -122.5075,
        "speed_mph": 40,
        "heading": "Southbound",
        "city": "San Francisco Bay Area, CA"
    },
    "Austin: I-35 Expressway (Multi-Car Crash Corridor)": {
        "lat": 30.2760,
        "lng": -97.7320,
        "speed_mph": 50,
        "heading": "Southbound Lower Deck",
        "city": "Austin Corridor, TX"
    },
    "Bangalore: Approaching Silk Board (Flooding Underpass)": {
        "lat": 12.9190,
        "lng": 77.6225,
        "speed_mph": 25,
        "heading": "Towards Electronic City",
        "city": "Bangalore Highway Hub, IN"
    }
}

def render_alerts_page():
    """Renders the Driver Mode Radar & Alert Notification Hub."""
    user = get_current_user()

    st.markdown(
        """
        <div class="rg-card" style="border-left: 5px solid #DC2626;">
            <h2 style="margin:0; color:#1E3A8A;">🚨 Driver Mode & Proximity Radar System</h2>
            <p style="margin:4px 0 0 0; color:#475569;">
                Active collision avoidance and tactical hazard radar. Emits dynamic audio/visual alerts as your vehicle approaches road hazards.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_radar, tab_sos, tab_notifications = st.tabs([
        "🚗 Active Driver Radar Mode",
        "📡 Emergency SOS Broadcast",
        "🔔 System Notification Center"
    ])

    with tab_radar:
        render_driver_radar(user)

    with tab_sos:
        render_sos_broadcaster(user)

    with tab_notifications:
        render_notification_feed(user)

def render_driver_radar(user: Dict[str, Any]):
    """Simulates or tracks live GPS location and computes proximity hazard vectors."""
    col_ctrl, col_hud = st.columns([1, 1.6])

    with col_ctrl:
        st.markdown("#### 🛰️ Vehicle GPS & Telemetry")

        scenario_name = st.selectbox(
            "Select Driver Corridor Scenario",
            list(DRIVER_SCENARIOS.keys())
        )
        scenario = DRIVER_SCENARIOS[scenario_name]

        col_lat, col_lng = st.columns(2)
        with col_lat:
            veh_lat = st.number_input(
                "Simulated Vehicle Lat",
                value=float(scenario["lat"]),
                format="%.5f",
                step=0.0005,
                key="driver_lat"
            )
        with col_lng:
            veh_lng = st.number_input(
                "Simulated Vehicle Lon",
                value=float(scenario["lng"]),
                format="%.5f",
                step=0.0005,
                key="driver_lng"
            )

        col_spd, col_hdg = st.columns(2)
        with col_spd:
            speed = st.slider("Vehicle Speed (mph)", min_value=0, max_value=85, value=scenario["speed_mph"])
        with col_hdg:
            st.text_input("Travel Heading", value=scenario["heading"], disabled=True)

        st.caption(f"Radar Scan Zone: Critical (< {RADAR_ZONES['critical']}m) | Warning (< {RADAR_ZONES['warning']}m) | Notice (< {RADAR_ZONES['notice']}m)")

        enable_audio = st.checkbox("🔊 Enable Acoustic Alert Synthesizer", value=True)

    # Compute proximity
    all_hazards = get_hazards()
    scan_results = scan_proximity_hazards(veh_lat, veh_lng, all_hazards)

    with col_hud:
        st.markdown("#### 🛡️ ROADGUARD Heads-Up Radar Display (HUD)")

        crit_count = len(scan_results["critical"])
        warn_count = len(scan_results["warning"])
        notice_count = len(scan_results["notice"])

        # Top Radar Status Strip
        if crit_count > 0:
            radar_status_html = f"""
            <div class="rg-radar-alert radar-crit">
                <div style="font-size:36px;">🚨</div>
                <div>
                    <div style="font-weight:800; font-size:18px; color:#991B1B;">CRITICAL HAZARD PROXIMITY ALERT!</div>
                    <div style="font-size:13px; color:#B91C1C;">{crit_count} imminent hazard(s) within immediate braking distance (&lt;350m).</div>
                </div>
            </div>
            """
            st.markdown(radar_status_html, unsafe_allow_html=True)
            if enable_audio:
                # Embed HTML5 Web Audio API beep chime for realistic driver alert
                st.components.v1.html("""
                <script>
                try {
                    const ctx = new (window.AudioContext || window.webkitAudioContext)();
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.type = 'sawtooth';
                    osc.frequency.setValueAtTime(880, ctx.currentTime); // High pitch alarm
                    osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.3);
                    gain.gain.setValueAtTime(0.15, ctx.currentTime);
                    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.start();
                    osc.stop(ctx.currentTime + 0.35);
                } catch(e) {}
                </script>
                """, height=0)

        elif warn_count > 0:
            radar_status_html = f"""
            <div class="rg-radar-alert radar-warn">
                <div style="font-size:32px;">⚠️</div>
                <div>
                    <div style="font-weight:700; font-size:16px; color:#92400E;">ROADWAY CAUTION RADAR</div>
                    <div style="font-size:13px; color:#B45309;">{warn_count} active hazard(s) ahead within 800m. Maintain buffer distance.</div>
                </div>
            </div>
            """
            st.markdown(radar_status_html, unsafe_allow_html=True)

        else:
            radar_status_html = f"""
            <div class="rg-radar-alert radar-info">
                <div style="font-size:32px;">🟢</div>
                <div>
                    <div style="font-weight:700; font-size:16px; color:#065F46;">ROADWAY CLEAR AHEAD</div>
                    <div style="font-size:13px; color:#047857;">No immediate threats in your vehicle's safety envelope. Cruise safely.</div>
                </div>
            </div>
            """
            st.markdown(radar_status_html, unsafe_allow_html=True)

        # Immediate Critical Hazards
        if crit_count > 0:
            st.markdown("##### 🚨 Critical Threats Ahead (< 350m):")
            for h in scan_results["critical"]:
                st.markdown(
                    f"""
                    <div style="background:#FFF1F2; border:1px solid #FDA4AF; border-radius:10px; padding:12px; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:800; color:#BE123C; font-size:15px;">{h['title']}</span>
                            <span style="font-weight:800; background:#E11D48; color:white; padding:3px 8px; border-radius:6px; font-size:12px;">
                                📍 {h['current_dist_m']} METERS AHEAD
                            </span>
                        </div>
                        <div style="margin:4px 0; font-size:13px; color:#334155;">📍 {h.get('address', '')}</div>
                        <div style="background:#FFE4E6; border-left:3px solid #E11D48; padding:6px 10px; border-radius:4px; margin-top:6px; font-size:12px; font-weight:700; color:#9F1239;">
                            🛑 TACTICAL ADVISORY: {h.get('suggested_action', 'Reduce speed and prepare for lane detour immediately.')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Warning Zone
        if warn_count > 0:
            st.markdown("##### ⚠️ Caution Zone (350m - 800m):")
            for h in scan_results["warning"]:
                st.markdown(
                    f"""
                    <div style="background:#FFFBEB; border:1px solid #FCD34D; border-radius:10px; padding:10px; margin-bottom:8px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:700; color:#92400E; font-size:14px;">{h['title']}</span>
                            <span style="font-weight:700; color:#B45309; font-size:12px;">{h['current_dist_m']}m</span>
                        </div>
                        <div style="font-size:12px; color:#78350F; margin-top:2px;">
                            💡 {h.get('suggested_action', 'Drive cautiously.')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Advisory Notice Zone
        if notice_count > 0:
            with st.expander(f"ℹ️ Advisory Distance Hazards (800m - 1.8km) [{notice_count}]", expanded=False):
                for h in scan_results["notice"]:
                    st.write(f"• **{h['title']}** — {h['current_dist_km']} km away ({h['severity']})")

def render_sos_broadcaster(user: Dict[str, Any]):
    """Allows emergency broadcast dispatch for severe incidents."""
    st.markdown("#### 📡 Rapid Emergency SOS Alert Broadcast")
    st.caption("Broadcast high-priority emergency notifications to all connected vehicles and road dispatchers.")

    col1, col2 = st.columns([1.2, 0.8])

    with col1:
        sos_title = st.text_input("Emergency Alert Title", value="URGENT: Roadway Blockage / Collision Alert")
        sos_sev = st.selectbox("Broadcast Severity", ["Critical", "High"])
        sos_msg = st.text_area(
            "Incident Particulars & Emergency Directives",
            value="All lanes blocked due to active emergency event. Yield immediately to arriving emergency vehicles.",
            height=100
        )

        trigger_broadcast = st.button("🚨 Broadcast SOS Emergency Alert", use_container_width=True)

        if trigger_broadcast:
            new_alert_id = log_broadcast_alert(sos_title, sos_msg, sos_sev)
            st.success(f"Emergency Broadcast #{new_alert_id} dispatched across ROADGUARD network!")
            st.rerun()

    with col2:
        st.markdown(
            """
            <div class="rg-card" style="background:#FEF2F2; border:1px solid #F87171;">
                <h4 style="color:#991B1B; margin:0 0 8px 0;">🛡️ Protocol Guidelines</h4>
                <ul style="font-size:12px; color:#7F1D1D; padding-left:18px; margin:0;">
                    <li>Only dispatch for severe safety disruptions or collisions.</li>
                    <li>Notifies municipal crews, police, and active navigation corridors.</li>
                    <li>Recorded permanently into public safety audit logs.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

def render_notification_feed(user: Dict[str, Any]):
    """Displays platform alerts log and municipal notifications."""
    st.markdown("#### 🔔 System Notifications & Dispatch Ledger")

    alerts = get_alerts(limit=25)

    if not alerts:
        st.info("No active notifications in the ledger.")
        return

    for a in alerts:
        border_col = "#DC2626" if a["severity"] == "Critical" else ("#F59E0B" if a["severity"] == "High" else "#2563EB")
        bg_col = "#FEF2F2" if a["severity"] == "Critical" else "#F8FAFC"

        st.markdown(
            f"""
            <div style="background:{bg_col}; border-left:4px solid {border_col}; border-radius:8px; padding:12px 16px; margin-bottom:10px; border-top:1px solid #E2E8F0; border-right:1px solid #E2E8F0; border-bottom:1px solid #E2E8F0;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:700; color:#1E3A8A; font-size:14px;">{a['title']}</span>
                    <span style="font-size:11px; color:#64748B;">{time_ago(a['created_at'])}</span>
                </div>
                <div style="font-size:13px; color:#334155; margin-top:4px;">{a['message']}</div>
                {f"<div style='font-size:11px; color:#475569; margin-top:4px;'>📍 Context: {a.get('address', '')}</div>" if a.get('address') else ""}
            </div>
            """,
            unsafe_allow_html=True
        )
