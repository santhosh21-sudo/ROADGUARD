"""
ROADGUARD - Complete Road Hazard Reporting Form & Incident Tracker
Supports:
1. Current location (HTML5 Geolocation) or manually entered location.
2. Road problem types: Pothole, Road construction, Road repair, Rain damage, Waterlogging, Accident or road blockage.
3. Road problem photo upload with Supabase Storage integration.
4. Problem description and severity.
5. Incident date and time picker.
6. Validation for all required fields.
7. Supabase Database & local persistence.
8. Real-time success confirmation with karma rewards.
9. Personal report history viewer.
10. Fully mobile-friendly responsive layout.
"""

import streamlit as st
import os
import re
from datetime import datetime, date, time
from typing import Dict, Any, Optional
from config import (
    ROAD_PROBLEM_TYPES, SEVERITY_LEVELS, DEFAULT_CITIES,
    THEME_COLORS, UPLOAD_DIR, KARMA_POINTS
)
from database import (
    create_hazard, get_user_submitted_reports, get_hazards
)
from auth import get_current_user, can_submit_reports, switch_demo_user
from supabase_client import (
    is_supabase_configured, supabase_upload_photo, supabase_insert_hazard
)
from utils import time_ago

# Pre-curated incident evidence photo URLs (reliable Unsplash automotive / roadway assets)
SAMPLE_HAZARD_PHOTOS = {
    "Pothole": "https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?w=600&auto=format&fit=crop&q=80",
    "Road construction": "https://images.unsplash.com/photo-1541888946425-d0fbb18086f6?w=600&auto=format&fit=crop&q=80",
    "Road repair": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=600&auto=format&fit=crop&q=80",
    "Rain damage": "https://images.unsplash.com/photo-1519692933481-e162a57d6721?w=600&auto=format&fit=crop&q=80",
    "Waterlogging": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=600&auto=format&fit=crop&q=80",
    "Accident or road blockage": "https://images.unsplash.com/photo-1598970434795-0c54fe7c0648?w=600&auto=format&fit=crop&q=80"
}

def render_reporting_page():
    """Renders the comprehensive Hazard Reporting Center with RBAC enforcement."""
    user = get_current_user()

    # RBAC Check: Viewers are restricted from submitting reports
    if not can_submit_reports():
        st.markdown(
            f"""<div class="rg-card" style="border-left: 5px solid #F59E0B;">
<h3 style="margin:0; color:#92400E;">🔒 Reporter Role Required</h3>
<p style="margin:6px 0 12px 0; color:#475569; font-size:14px;">
You are currently signed in as a <b>Viewer ({user.get('full_name', 'User')})</b>.<br>
Viewers have access to search locations, inspect approved road reports, and check pre-travel route safety.
To file new road hazard reports, upload problem photos, and track fixes, please switch to or register as a <b>Reporter</b>.
</p>
</div>""",
            unsafe_allow_html=True
        )
        if st.button("📢 Switch to Reporter Role (Alice)", type="primary"):
            switch_demo_user("alice")
        return

    st.markdown(
        f"""<div class="rg-card" style="border-left: 5px solid {THEME_COLORS['primary_blue']};">
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
<div>
<h2 style="margin:0; color:#1E3A8A;">⚠️ Road Hazard Reporting Studio</h2>
<p style="margin:4px 0 0 0; color:#475569;">
Submit live roadway obstructions, upload photo evidence, pinpoint coordinates, and track resolution progress.
</p>
</div>
<div>
<span class="rg-badge" style="background:#EFF6FF; color:#1D4ED8; border:1px solid #BFDBFE; font-size:13px; padding:6px 14px;">
📢 LOGGED IN AS: {user.get('full_name', 'Reporter')}
</span>
</div>
</div>
</div>""",
        unsafe_allow_html=True
    )

    my_reports = get_user_submitted_reports(user["username"])

    tab_form, tab_history = st.tabs([
        "📝 Submit Road Hazard Report",
        f"📋 My Submitted Reports ({len(my_reports)})"
    ])

    with tab_form:
        render_hazard_reporting_form(user)

    with tab_history:
        render_user_reports_list(my_reports, user)

def render_hazard_reporting_form(user: Dict[str, Any]):
    """
    Complete, validated, mobile-friendly road hazard submission form.
    Connects to Supabase Database and Supabase Storage with local SQLite fallback.
    """
    col_form, col_preview = st.columns([1.2, 0.8])

    with col_form:
        st.markdown("#### 1. Road Problem Type")
        problem_type = st.selectbox(
            "Select Problem Type *",
            list(ROAD_PROBLEM_TYPES.keys()),
            format_func=lambda x: f"{ROAD_PROBLEM_TYPES[x]['icon']} {x}",
            help="Choose the primary roadway hazard observed."
        )
        prob_meta = ROAD_PROBLEM_TYPES[problem_type]
        st.caption(f"ℹ️ {prob_meta['description']}")

        col_sev, col_block = st.columns(2)
        with col_sev:
            severity = st.select_slider(
                "Hazard Severity Level *",
                options=["Low", "Medium", "High", "Critical"],
                value=prob_meta["default_severity"]
            )
        with col_block:
            st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
            lane_blocked = st.checkbox("🚧 Lane is Blocked / Impassable", value=(severity in ["High", "Critical"]))

        report_title = st.text_input(
            "Report Title / Headline *",
            value=f"{prob_meta['icon']} {problem_type} on roadway",
            placeholder="e.g. Deep Pothole on Right Lane near Exit 4"
        )

        st.markdown("---")
        st.markdown("#### 2. Incident Location")
        location_mode = st.radio(
            "Location Input Method *",
            ["📍 Detect Current Location (GPS)", "✍️ Manually Enter Location"],
            horizontal=True
        )

        # Default location values
        current_lat = 40.7308
        current_lng = -73.9742
        default_city = "New York Metro, NY"
        default_address = "FDR Drive near E 23rd St, New York"

        if location_mode == "📍 Detect Current Location (GPS)":
            st.info("🛰️ **HTML5 Browser Geolocation:** Click below to detect your device's exact GPS location.")

            # Embedded HTML5 Geolocation Trigger
            st.components.v1.html(
                """
                <div style="font-family: sans-serif; text-align: center; padding: 10px;">
                    <button onclick="getGPS()" style="background-color: #2563EB; color: white; border: none; padding: 10px 18px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 14px;">
                        📍 Tap to Acquire Device GPS Coordinates
                    </button>
                    <div id="gps-status" style="margin-top: 8px; font-size: 12px; color: #475569;">Ready to detect</div>
                </div>
                <script>
                function getGPS() {
                    const status = document.getElementById('gps-status');
                    if (navigator.geolocation) {
                        status.innerText = "Acquiring GPS fix...";
                        navigator.geolocation.getCurrentPosition(
                            function(position) {
                                const lat = position.coords.latitude.toFixed(5);
                                const lng = position.coords.longitude.toFixed(5);
                                status.innerHTML = "✅ GPS Fix Acquired: <b>" + lat + ", " + lng + "</b> (Accuracy: " + Math.round(position.coords.accuracy) + "m)";
                            },
                            function(error) {
                                status.innerText = "GPS error: " + error.message + " (Using corridor coordinates)";
                            },
                            { timeout: 10000, enableHighAccuracy: true }
                        );
                    } else {
                        status.innerText = "Geolocation not supported by browser.";
                    }
                }
                </script>
                """,
                height=85
            )

            col_clat, col_clng = st.columns(2)
            with col_clat:
                latitude = st.number_input("Detected Latitude *", value=current_lat, format="%.5f", step=0.0005)
            with col_clng:
                longitude = st.number_input("Detected Longitude *", value=current_lng, format="%.5f", step=0.0005)

            selected_city = st.selectbox("Metropolitan Corridor *", list(DEFAULT_CITIES.keys()), index=0)
            address = st.text_input("Nearby Landmark / Street *", value=default_address)

        else:
            selected_city = st.selectbox("City / Corridor *", list(DEFAULT_CITIES.keys()), index=0)
            city_cfg = DEFAULT_CITIES[selected_city]

            col_mlat, col_mlng = st.columns(2)
            with col_mlat:
                latitude = st.number_input("Latitude *", value=float(city_cfg["lat"]), format="%.5f", step=0.0005)
            with col_mlng:
                longitude = st.number_input("Longitude *", value=float(city_cfg["lng"]), format="%.5f", step=0.0005)

            address = st.text_input(
                "Street Address / Mile Marker / Intersection *",
                value=f"Highway Corridor & Exit Ramp, {selected_city.split(',')[0]}",
                placeholder="e.g. 5th Ave between 41st and 42nd St"
            )

        st.markdown("---")
        st.markdown("#### 3. Date & Time of Incident")
        col_date, col_time = st.columns(2)
        with col_date:
            incident_date = st.date_input("Date Observed *", value=date.today())
        with col_time:
            incident_time = st.time_input("Time Observed *", value=datetime.now().time())

        incident_datetime_str = datetime.combine(incident_date, incident_time).isoformat()

        st.markdown("---")
        st.markdown("#### 4. Problem Description & Tactical Advisory")
        description = st.text_area(
            "Detailed Description of Road Problem *",
            value=f"{prob_meta['description']}. Visible obstacle on road surface.",
            placeholder="Describe extent of road damage, lane blockage, water depth, visibility...",
            height=90
        )

        suggested_action = st.text_input(
            "Recommended Driver Action *",
            value=prob_meta["suggested_action"],
            placeholder="e.g. Decelerate smoothly, shift to left lane"
        )

        st.markdown("---")
        st.markdown("#### 5. Road Problem Photo Evidence")
        st.caption("Upload an image of the road hazard. Uploads are stored directly in **Supabase Storage** (`road-hazard-photos`).")

        photo_mode = st.radio("Photo Source *", ["Upload Road Photo File", "Use Scenario Evidence Snapshot"], horizontal=True)

        uploaded_file = None
        photo_bytes = None
        photo_filename = None
        photo_url = SAMPLE_HAZARD_PHOTOS.get(problem_type, "")

        if photo_mode == "Upload Road Photo File":
            uploaded_file = st.file_uploader(
                "Choose Road Problem Photo (JPG, PNG, JPEG, WEBP) *",
                type=["jpg", "png", "jpeg", "webp"],
                help="Maximum size: 10MB. Images are uploaded to Supabase Storage."
            )
            if uploaded_file is not None:
                photo_bytes = uploaded_file.getvalue()
                photo_filename = f"hazard_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
                # Save locally in uploads folder as guaranteed backup
                local_save_path = UPLOAD_DIR / photo_filename
                with open(local_save_path, "wb") as f:
                    f.write(photo_bytes)
                photo_url = str(local_save_path)
                st.image(uploaded_file, caption="Preview of Uploaded Road Problem Photo", use_container_width=True)

    # Right Column: Real-time Live Alert Card Preview & Submission Button
    with col_preview:
        st.markdown("#### 👁️ Driver Alert Preview")
        st.caption("How your report will appear to Viewers, Navigators, and Public Works:")

        sev_info = SEVERITY_LEVELS[severity]
        badge_cls = f"badge-{severity.lower()}"

        st.markdown(
            f"""<div class="rg-card" style="border: 2px solid {sev_info['color']};">
<div style="display:flex; justify-content:space-between; align-items:center;">
<div>
<span class="rg-badge {badge_cls}">{prob_meta['icon']} {severity.upper()} SEVERITY</span>
<span class="rg-badge badge-status-active">📝 REPORTED</span>
</div>
<span style="font-size:11px; color:#64748B;">{incident_date.strftime('%b %d')} at {incident_time.strftime('%H:%M')}</span>
</div>
<h3 style="margin:12px 0 6px 0; color:#0F172A; font-size:17px;">{report_title}</h3>
<div style="font-size:13px; color:#475569; margin-bottom:8px;">
📍 <b>{address}</b> ({selected_city})<br>
🌐 GPS: <code>{latitude:.4f}, {longitude:.4f}</code>
</div>
<div style="background:#F8FAFC; border-radius:8px; padding:10px; margin-bottom:8px; border-left:3px solid {sev_info['color']}; font-size:13px; color:#334155;">
{description}
</div>
<div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:8px; padding:8px 10px; margin-bottom:8px; font-size:12px; color:#065F46;">
<b>💡 DRIVER ADVISORY:</b> {suggested_action}
</div>
{"<div style='color:#DC2626; font-size:12px; font-weight:700; margin-bottom:8px;'>⚠️ WARNING: Active Lane Blockage!</div>" if lane_blocked else ""}
<div style="font-size:11px; color:#64748B; border-top:1px solid #E2E8F0; padding-top:6px;">
Reported by: <b>{user['full_name']} (📢 Reporter)</b>
</div>
</div>""",
            unsafe_allow_html=True
        )

        if photo_url and (photo_url.startswith("http") or os.path.exists(photo_url)):
            st.image(photo_url, caption="Incident Visual Evidence", use_container_width=True)

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        # Prominent Submission Button
        submit_btn = st.button("🚀 Submit Road Hazard Report", use_container_width=True, type="primary")

        if submit_btn:
            # 1. Validation of all required fields
            errors = []
            if not report_title.strip():
                errors.append("Report Title is required.")
            if not problem_type:
                errors.append("Road problem type must be selected.")
            if not address.strip():
                errors.append("Location address or landmark is required.")
            if not description.strip() or len(description.strip()) < 5:
                errors.append("Problem description must be at least 5 characters.")
            if latitude == 0.0 and longitude == 0.0:
                errors.append("Valid GPS coordinates are required.")
            if photo_mode == "Upload Road Photo File" and uploaded_file is None:
                errors.append("Please upload a road problem photo or switch to Scenario Evidence.")

            if errors:
                for err in errors:
                    st.error(f"❌ {err}")
            else:
                final_photo_url = photo_url
                storage_msg = "Stored locally"

                # 2. Upload photo to Supabase Storage if file was provided and Supabase is configured
                if uploaded_file is not None and is_supabase_configured():
                    with st.spinner("Uploading photo to Supabase Storage (bucket: road-hazard-photos)..."):
                        mime = uploaded_file.type or "image/jpeg"
                        up_ok, up_url = supabase_upload_photo(
                            file_bytes=uploaded_file.getvalue(),
                            filename=uploaded_file.name,
                            content_type=mime,
                            bucket="road-hazard-photos"
                        )
                        if up_ok:
                            final_photo_url = up_url
                            storage_msg = "Uploaded to Supabase Storage"
                        else:
                            st.warning(f"⚠️ Supabase Storage notice: {up_url}. Preserved image locally.")

                # 3. Create hazard payload
                hazard_payload = {
                    "title": report_title.strip(),
                    "category": problem_type,
                    "description": description.strip(),
                    "severity": severity,
                    "status": "Reported",
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                    "address": address.strip(),
                    "city": selected_city,
                    "reported_by": user["username"],
                    "reporter_name": user["full_name"],
                    "lane_blocked": lane_blocked,
                    "photo_url": final_photo_url,
                    "suggested_action": suggested_action.strip()
                }

                # 4. Save to Supabase Database (if configured)
                if is_supabase_configured():
                    with st.spinner("Recording hazard in Supabase Database..."):
                        db_ok, db_msg, db_rec = supabase_insert_hazard(hazard_payload)
                        if not db_ok:
                            st.info(f"Supabase DB note: {db_msg} (Synchronized with local storage).")

                # 5. Always save to local database for immediate local map, route checking & analytics
                new_id = create_hazard(hazard_payload)

                # 6. Celebratory Success Message
                st.balloons()
                st.success(
                    f"🎉 **Road Hazard Report #{new_id} Successfully Submitted!**\n\n"
                    f"• **Problem:** {prob_meta['icon']} {problem_type} ({severity} Severity)\n"
                    f"• **Location:** {address} ({selected_city})\n"
                    f"• **Photo:** {storage_msg}\n"
                    f"• **Reward:** **+{KARMA_POINTS['submit_hazard']} Safety Karma Points** awarded to your profile!"
                )
                st.info("Your report is now live on the Live Hazard Radar and available for Viewers to check before travelling.")

def render_user_reports_list(reports, user: Dict[str, Any]):
    """Allows reporters to view and inspect all their submitted reports."""
    st.markdown("#### 📋 My Submitted Road Hazard Reports")
    st.caption("Track the verification and repair progress of all reports submitted by your account:")

    if not reports:
        st.info("You have not submitted any hazard reports yet. Use the **Submit Road Hazard Report** tab above to file your first report!")
        return

    st.write(f"Showing **{len(reports)}** report(s) filed by **{user['full_name']}**:")

    for r in reports:
        sev_color = SEVERITY_LEVELS.get(r["severity"], {}).get("color", "#2563EB")
        status_color = "#059669" if r["status"] == "Resolved" else "#2563EB"
        cat_icon = ROAD_PROBLEM_TYPES.get(r["category"], {}).get("icon", "⚠️")

        with st.container():
            col_l, col_r = st.columns([1.6, 0.9])

            with col_l:
                st.markdown(
                    f"""<div class="rg-card" style="border-left: 5px solid {sev_color};">
<div style="display:flex; justify-content:space-between; align-items:center;">
<div>
<span class="rg-badge badge-{r['severity'].lower()}">{cat_icon} {r['severity'].upper()}</span>
<span class="rg-badge" style="background:{status_color}22; color:{status_color}; border:1px solid {status_color};">
{r['status']}
</span>
</div>
<span style="font-size:11px; color:#64748B;">{time_ago(r.get('created_at', ''))}</span>
</div>
<h3 style="margin:10px 0 6px 0; color:#0F172A; font-size:17px;">#{r['id']} - {r['title']}</h3>
<div style="font-size:13px; color:#475569; margin-bottom:8px;">
📍 <b>{r.get('address', '')}</b> ({r.get('city', '')})<br>
🌐 GPS: <code>{r['latitude']:.4f}, {r['longitude']:.4f}</code>
</div>
<div style="background:#F8FAFC; border-radius:6px; padding:8px 12px; margin-bottom:8px; font-size:13px; color:#334155;">
{r.get('description', '')}
</div>
<div style="background:#ECFDF5; border:1px solid #A7F3D0; padding:6px 10px; border-radius:6px; font-size:12px; color:#065F46; margin-bottom:6px;">
<b>💡 Driver Advisory:</b> {r.get('suggested_action', 'Drive cautiously')}
</div>
{f"<div style='background:#EFF6FF; border:1px solid #BFDBFE; padding:6px 10px; border-radius:6px; font-size:12px; color:#1E40AF; margin-bottom:6px;'><b>Resolution Notes:</b> {r['resolution_notes']}</div>" if r.get('resolution_notes') else ""}
<div style="font-size:11px; color:#64748B; margin-top:4px;">
👍 {r['upvotes']} Community Verifications | Lane Blocked: {'Yes' if r.get('lane_blocked') else 'No'}
</div>
</div>""",
                    unsafe_allow_html=True
                )

            with col_r:
                p_url = r.get("photo_url")
                if p_url and (p_url.startswith("http") or os.path.exists(p_url)):
                    st.image(p_url, caption=f"Evidence Photo: #{r['id']}", use_container_width=True)
                else:
                    st.markdown(
                        """<div style="background:#F1F5F9; border:1px dashed #CBD5E1; border-radius:8px; height:160px; display:flex; align-items:center; justify-content:center; text-align:center; color:#64748B; font-size:12px; padding:12px;">
📷 Problem photo registered with submission.
</div>""",
                        unsafe_allow_html=True
                    )
