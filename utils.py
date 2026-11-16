"""
ROADGUARD - Utilities & Algorithmic Engines
Haversine mathematics, route corridor risk analysis, proximity detection,
humanized time formatting, and modern Blue-White-Green UI styling injection.
"""

import math
from datetime import datetime
from typing import List, Dict, Any, Tuple
import streamlit as st
from config import THEME_COLORS, SEVERITY_LEVELS, RADAR_ZONES

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth in meters.
    Uses pure standard library math for high performance and zero external dependencies.
    """
    R = 6371000.0  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def distance_point_to_segment(p_lat: float, p_lon: float,
                              a_lat: float, a_lon: float,
                              b_lat: float, b_lon: float) -> float:
    """
    Minimum distance in meters from point P to line segment AB.
    """
    # Flat-earth approximation in meters for small local segments
    lat_mid = math.radians((a_lat + b_lat) / 2.0)
    m_per_deg_lat = 111132.92
    m_per_deg_lon = 111412.84 * math.cos(lat_mid)

    px = (p_lon - a_lon) * m_per_deg_lon
    py = (p_lat - a_lat) * m_per_deg_lat
    bx = (b_lon - a_lon) * m_per_deg_lon
    by = (b_lat - a_lat) * m_per_deg_lat

    seg_len_sq = bx * bx + by * by
    if seg_len_sq == 0:
        return math.hypot(px, py)

    t = max(0.0, min(1.0, (px * bx + py * by) / seg_len_sq))
    proj_x = t * bx
    proj_y = t * by
    return math.hypot(px - proj_x, py - proj_y)

def calculate_corridor_hazards(
    start_coords: Tuple[float, float],
    end_coords: Tuple[float, float],
    hazards: List[Dict[str, Any]],
    corridor_buffer_m: float = 750.0
) -> Dict[str, Any]:
    """
    Analyzes hazards along a navigation corridor between origin and destination.
    Returns intercepted hazards, total risk score, and safety rating.
    """
    s_lat, s_lon = start_coords
    e_lat, e_lon = end_coords

    # Interpolate realistic corridor waypoints (including a slight roadway curvature)
    num_steps = 15
    waypoints = []
    for i in range(num_steps + 1):
        frac = i / float(num_steps)
        # Add slight natural curvature mimicking real highway paths
        curve_offset = math.sin(frac * math.pi) * 0.003
        wp_lat = s_lat + frac * (e_lat - s_lat) + curve_offset * 0.5
        wp_lon = s_lon + frac * (e_lon - s_lon) + curve_offset
        waypoints.append((wp_lat, wp_lon))

    intercepted = []
    total_weight = 0

    for h in hazards:
        if h.get("status") == "Resolved":
            continue
        h_lat = h["latitude"]
        h_lon = h["longitude"]

        # Check minimum distance to any segment of the route
        min_dist = float("inf")
        for j in range(len(waypoints) - 1):
            d = distance_point_to_segment(h_lat, h_lon,
                                          waypoints[j][0], waypoints[j][1],
                                          waypoints[j+1][0], waypoints[j+1][1])
            if d < min_dist:
                min_dist = d

        if min_dist <= corridor_buffer_m:
            sev = h.get("severity", "Medium")
            w = SEVERITY_LEVELS.get(sev, {}).get("weight", 2)
            total_weight += w
            item = dict(h)
            item["distance_to_corridor_m"] = round(min_dist, 1)
            intercepted.append(item)

    # Sort intercepted by distance
    intercepted.sort(key=lambda x: x["distance_to_corridor_m"])

    # Risk Score calculation (0 - 100)
    risk_score = min(100, total_weight * 12)
    if risk_score == 0:
        grade = "Unmonitored / Zero Reports Logged"
        grade_color = THEME_COLORS["primary_blue"]
        summary = "Zero active hazard reports logged along this corridor. Note: Absence of reports does not guarantee road is safe or clear."
    elif risk_score <= 20:
        grade = "A (Low Risk)"
        grade_color = THEME_COLORS["accent_green"]
        summary = "Corridor is generally clear. Minor slowdowns may apply."
    elif risk_score <= 45:
        grade = "B (Moderate Caution)"
        grade_color = THEME_COLORS["severity_medium"]
        summary = "Active hazards detected. Maintain buffer distance."
    elif risk_score <= 75:
        grade = "C (High Caution)"
        grade_color = THEME_COLORS["severity_high"]
        summary = "Multiple hazards or lane blockages reported. Expect delays."
    else:
        grade = "D (Severe Danger)"
        grade_color = THEME_COLORS["severity_critical"]
        summary = "Critical road hazard on route! Alternate bypass strongly recommended."

    return {
        "waypoints": waypoints,
        "intercepted_hazards": intercepted,
        "hazard_count": len(intercepted),
        "risk_score": risk_score,
        "risk_grade": grade,
        "risk_color": grade_color,
        "summary": summary
    }

def scan_proximity_hazards(
    current_lat: float,
    current_lon: float,
    hazards: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Evaluates active hazards against current driver coordinates and groups them by radar zone.
    """
    critical_zone = []
    warning_zone = []
    notice_zone = []

    for h in hazards:
        if h.get("status") == "Resolved":
            continue
        dist_m = haversine_distance(current_lat, current_lon, h["latitude"], h["longitude"])

        hazard_copy = dict(h)
        hazard_copy["current_dist_m"] = round(dist_m)
        hazard_copy["current_dist_km"] = round(dist_m / 1000.0, 2)

        if dist_m <= RADAR_ZONES["critical"]:
            critical_zone.append(hazard_copy)
        elif dist_m <= RADAR_ZONES["warning"]:
            warning_zone.append(hazard_copy)
        elif dist_m <= RADAR_ZONES["notice"]:
            notice_zone.append(hazard_copy)

    critical_zone.sort(key=lambda x: x["current_dist_m"])
    warning_zone.sort(key=lambda x: x["current_dist_m"])
    notice_zone.sort(key=lambda x: x["current_dist_m"])

    return {
        "critical": critical_zone,
        "warning": warning_zone,
        "notice": notice_zone
    }

def time_ago(iso_str: str) -> str:
    """Returns human-readable relative time (e.g. '15 mins ago')."""
    if not iso_str:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", ""))
        diff = datetime.now() - dt
        seconds = diff.total_seconds()
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            return f"{int(seconds // 60)} mins ago"
        elif seconds < 86400:
            return f"{int(seconds // 3600)} hours ago"
        elif seconds < 604800:
            return f"{int(seconds // 86400)} days ago"
        else:
            return dt.strftime("%b %d, %Y")
    except Exception:
        return str(iso_str)[:10]

def export_hazards_csv(hazards: List[Dict[str, Any]]) -> str:
    """Generate CSV string from list of hazard dictionaries."""
    headers = ["ID", "Title", "Category", "Severity", "Status", "Latitude", "Longitude",
               "Address", "City", "Reported_By", "Upvotes", "Lane_Blocked", "Created_At"]
    lines = [",".join(headers)]
    for h in hazards:
        row = [
            str(h.get("id", "")),
            f'"{str(h.get("title", "")).replace(chr(34), chr(39))}"',
            f'"{str(h.get("category", ""))}"',
            str(h.get("severity", "")),
            str(h.get("status", "")),
            str(h.get("latitude", "")),
            str(h.get("longitude", "")),
            f'"{str(h.get("address", "")).replace(chr(34), chr(39))}"',
            f'"{str(h.get("city", ""))}"',
            str(h.get("reported_by", "")),
            str(h.get("upvotes", 0)),
            str(h.get("lane_blocked", 0)),
            str(h.get("created_at", ""))
        ]
        lines.append(",".join(row))
    return "\n".join(lines)

def apply_custom_theme():
    """
    Injects custom CSS adhering strictly to the requested light theme:
    Modern, professional palette with blue, white, and green.
    """
    custom_css = f"""
    <style>
    /* Google Fonts Import */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: {THEME_COLORS["text_main"]};
    }}

    /* Top Header & App Shell */
    .stApp {{
        background-color: {THEME_COLORS["background_light"]};
    }}

    /* Primary Container Card */
    .rg-card {{
        background-color: {THEME_COLORS["surface_white"]};
        border-radius: 12px;
        padding: 20px 24px;
        border: 1px solid {THEME_COLORS["card_border"]};
        box-shadow: 0 2px 4px -1px rgba(15, 23, 42, 0.04), 0 4px 6px -1px rgba(15, 23, 42, 0.02);
        margin-bottom: 16px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .rg-card:hover {{
        box-shadow: 0 6px 12px -2px rgba(15, 23, 42, 0.08);
    }}

    /* Stat KPI Card */
    .rg-stat-box {{
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        border-radius: 12px;
        padding: 16px 20px;
        border: 1px solid {THEME_COLORS["card_border"]};
        border-left: 4px solid {THEME_COLORS["primary_blue"]};
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .rg-stat-box.green {{
        border-left-color: {THEME_COLORS["accent_green"]};
    }}
    .rg-stat-box.red {{
        border-left-color: {THEME_COLORS["severity_critical"]};
    }}
    .rg-stat-box.amber {{
        border-left-color: {THEME_COLORS["severity_medium"]};
    }}

    .rg-stat-value {{
        font-size: 28px;
        font-weight: 700;
        color: {THEME_COLORS["text_main"]};
        line-height: 1.1;
    }}
    .rg-stat-label {{
        font-size: 13px;
        font-weight: 500;
        color: {THEME_COLORS["text_muted"]};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }}

    /* Badges */
    .rg-badge {{
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        text-align: center;
        margin-right: 6px;
    }}
    .badge-critical {{
        background-color: #FEE2E2;
        color: #991B1B;
        border: 1px solid #FCA5A5;
    }}
    .badge-high {{
        background-color: #FFEDD5;
        color: #9A3412;
        border: 1px solid #FDBA74;
    }}
    .badge-medium {{
        background-color: #FEF3C7;
        color: #92400E;
        border: 1px solid #FCD34D;
    }}
    .badge-low {{
        background-color: #D1FAE5;
        color: #065F46;
        border: 1px solid #6EE7B7;
    }}
    .badge-status-resolved {{
        background-color: #ECFDF5;
        color: #047857;
        border: 1px solid #A7F3D0;
    }}
    .badge-status-active {{
        background-color: #EFF6FF;
        color: #1D4ED8;
        border: 1px solid #BFDBFE;
    }}

    /* App Header Banner */
    .rg-header {{
        background: linear-gradient(135deg, #1E40AF 0%, #1E3A8A 60%, #065F46 100%);
        border-radius: 14px;
        padding: 24px 30px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 10px 15px -3px rgba(30, 64, 175, 0.2);
    }}
    .rg-header h1 {{
        color: white;
        font-size: 32px;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0;
    }}
    .rg-header p {{
        color: #E2E8F0;
        font-size: 15px;
        margin: 6px 0 0 0;
        font-weight: 400;
    }}

    /* Buttons styling */
    div.stButton > button:first-child {{
        background-color: {THEME_COLORS["primary_blue"]};
        color: white;
        font-weight: 600;
        border-radius: 8px;
        border: none;
        padding: 8px 18px;
        transition: all 0.2s ease;
    }}
    div.stButton > button:first-child:hover {{
        background-color: #1D4ED8;
        box-shadow: 0 4px 8px rgba(37, 99, 235, 0.25);
    }}

    /* Green action buttons */
    .green-btn button {{
        background-color: {THEME_COLORS["accent_green"]} !important;
        color: white !important;
    }}
    .green-btn button:hover {{
        background-color: #047857 !important;
    }}

    /* Radar Pulse Box */
    .rg-radar-alert {{
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 14px;
    }}
    .radar-crit {{
        background-color: #FEF2F2;
        border: 2px solid #DC2626;
        animation: pulseCrit 1.8s infinite;
    }}
    .radar-warn {{
        background-color: #FFFBEB;
        border: 2px solid #F59E0B;
    }}
    .radar-info {{
        background-color: #F0FDF4;
        border: 2px solid #10B981;
    }}

    @keyframes pulseCrit {{
        0% {{ box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.4); }}
        70% {{ box-shadow: 0 0 0 10px rgba(220, 38, 38, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }}
    }}

    /* User Profile Pill in Sidebar */
    .user-profile-pill {{
        background: #F1F5F9;
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 16px;
    }}

    /* Mobile-Friendly Responsive Layout */
    @media (max-width: 768px) {{
        .rg-card {{
            padding: 14px 16px !important;
            margin-bottom: 12px !important;
            border-radius: 10px !important;
        }}
        .rg-header {{
            padding: 16px 18px !important;
            margin-bottom: 16px !important;
            border-radius: 10px !important;
        }}
        .rg-header h1 {{
            font-size: 22px !important;
        }}
        .rg-header p {{
            font-size: 13px !important;
        }}
        .rg-stat-box {{
            padding: 12px 14px !important;
            margin-bottom: 8px !important;
        }}
        .rg-stat-value {{
            font-size: 22px !important;
        }}
        div[data-testid="column"] {{
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
            margin-bottom: 10px !important;
        }}
        div.stButton > button {{
            width: 100% !important;
            font-size: 15px !important;
            min-height: 48px !important;
            border-radius: 8px !important;
        }}
        input, select, textarea {{
            font-size: 16px !important;
        }}
        .rg-badge {{
            font-size: 11px !important;
            padding: 3px 8px !important;
            margin-bottom: 4px !important;
        }}
    }}

    /* Hide default streamlit decorations */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
