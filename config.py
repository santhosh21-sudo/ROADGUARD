"""
ROADGUARD - Configuration & System Constants
Smart Road Hazard Reporting & Navigation System
Theme: Professional Blue, White, and Green Light UI
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "roadguard.db"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Application Branding
APP_NAME = "ROADGUARD"
APP_SUBTITLE = "Smart Road Hazard Reporting & Navigation System"
APP_VERSION = "2.4.0"
APP_SLOGAN = "Empowering safer journeys through collective road intelligence"

# Professional Light Theme Colors (Blue, White, Green)
THEME_COLORS = {
    "primary_blue": "#1E40AF",        # Deep Royal Blue (Navigation & Authority)
    "primary_blue_light": "#3B82F6",  # Bright Blue
    "accent_green": "#059669",        # Emerald Green (Safety, Cleared, Eco)
    "accent_green_light": "#10B981",  # Mint Green
    "accent_green_subtle": "#ECFDF5", # Soft Green Tint
    "background_light": "#F8FAFC",    # Slate 50 ultra-clean background
    "surface_white": "#FFFFFF",       # Pure white for cards & containers
    "card_border": "#E2E8F0",         # Slate 200 border
    "text_main": "#0F172A",           # Slate 900 primary text
    "text_muted": "#475569",          # Slate 600 secondary text
    # Severity indicators
    "severity_low": "#10B981",        # Emerald
    "severity_medium": "#F59E0B",     # Amber
    "severity_high": "#F97316",       # Orange
    "severity_critical": "#DC2626",   # Ruby Red
}

# Exact Road Problem Types Required by ROADGUARD
ROAD_PROBLEM_TYPES = {
    "Pothole": {
        "icon": "🕳️",
        "description": "Deep asphalt crater, surface disintegration, or sharp road cracks",
        "default_severity": "Medium",
        "suggested_action": "Reduce speed, maintain lane buffer to prevent tire rim damage"
    },
    "Road construction": {
        "icon": "🚧",
        "description": "Active roadwork, barricades, lane narrowing, or heavy machinery",
        "default_severity": "Medium",
        "suggested_action": "Observe temporary construction speed limits and watch for flaggers"
    },
    "Road repair": {
        "icon": "🔧",
        "description": "Ongoing resurfacing, asphalt patching, or utility trench maintenance",
        "default_severity": "Low",
        "suggested_action": "Slow down and prepare for minor lane deflection"
    },
    "Rain damage": {
        "icon": "🌧️",
        "description": "Mud washout, gravel erosion, cracked asphalt, or shoulder slip from storm",
        "default_severity": "High",
        "suggested_action": "Drive with caution; watch for loose debris and reduced grip"
    },
    "Waterlogging": {
        "icon": "🌊",
        "description": "Submerged road surface, flash pool, drainage overflow, or flooded underpass",
        "default_severity": "High",
        "suggested_action": "Do not cross standing water; turn around and detour safely"
    },
    "Accident or road blockage": {
        "icon": "💥",
        "description": "Vehicle collision, overturned transport, fallen tree, or blocked traffic lanes",
        "default_severity": "Critical",
        "suggested_action": "Yield to emergency responders, slow down immediately, and detour"
    }
}

# Backward compatible categories dictionary
HAZARD_CATEGORIES = ROAD_PROBLEM_TYPES.copy()
HAZARD_CATEGORIES.update({
    "Pothole / Road Damage": ROAD_PROBLEM_TYPES["Pothole"],
    "Traffic Accident": ROAD_PROBLEM_TYPES["Accident or road blockage"],
    "Road Flooding / Waterlogging": ROAD_PROBLEM_TYPES["Waterlogging"],
    "Construction / Work Zone": ROAD_PROBLEM_TYPES["Road construction"],
    "Fallen Tree / Road Debris": {
        "icon": "🌲",
        "description": "Fallen boughs, cargo spill, rocks, or large obstacles",
        "default_severity": "High",
        "suggested_action": "Prepare for lane merge or detour"
    },
    "Traffic Signal Failure": {
        "icon": "🚦",
        "description": "Blacked-out or malfunctioning traffic lights at intersection",
        "default_severity": "High",
        "suggested_action": "Treat intersection as an all-way 4-way stop"
    },
    "Oil Spill / Slippery Surface": {
        "icon": "⚠️",
        "description": "Diesel spill, chemical slick, black ice, or gravel patch",
        "default_severity": "High",
        "suggested_action": "Avoid sudden braking or sharp steering maneuvers"
    },
    "Road Cave-in / Landslide": {
        "icon": "🛑",
        "description": "Embankment failure, sinkhole, or mudslide covering lanes",
        "default_severity": "Critical",
        "suggested_action": "Stop and seek an alternate detour immediately"
    }
})

# Hazard Severity Definitions
SEVERITY_LEVELS = {
    "Low": {
        "color": THEME_COLORS["severity_low"],
        "badge_bg": "#D1FAE5",
        "text_color": "#065F46",
        "weight": 1,
        "description": "Minor inconvenience. Traffic continues at normal or slightly reduced flow."
    },
    "Medium": {
        "color": THEME_COLORS["severity_medium"],
        "badge_bg": "#FEF3C7",
        "text_color": "#92400E",
        "weight": 2,
        "description": "Noticeable hazard. Requires lane adjustment or speed reduction."
    },
    "High": {
        "color": THEME_COLORS["severity_high"],
        "badge_bg": "#FFEDD5",
        "text_color": "#9A3412",
        "weight": 3,
        "description": "Serious danger. One or more lanes blocked, vehicle damage risk."
    },
    "Critical": {
        "color": THEME_COLORS["severity_critical"],
        "badge_bg": "#FEE2E2",
        "text_color": "#991B1B",
        "weight": 5,
        "description": "Extreme danger / Road closed. Threat to human life or total stoppage."
    }
}

# Hazard Workflow Statuses
STATUS_OPTIONS = [
    "Reported",
    "Community Verified",
    "Work Order Dispatched",
    "In Progress",
    "Resolved"
]

STATUS_METADATA = {
    "Reported": {"color": "#64748B", "icon": "📝", "desc": "Citizen report logged and pending validation"},
    "Community Verified": {"color": "#2563EB", "icon": "🛡️", "desc": "Upvoted by community members as active"},
    "Work Order Dispatched": {"color": "#D97706", "icon": "🚜", "desc": "Transmitted to municipal maintenance crew"},
    "In Progress": {"color": "#7C3AED", "icon": "🔧", "desc": "Repair team currently operating on-site"},
    "Resolved": {"color": "#059669", "icon": "✅", "desc": "Road inspected and cleared for safe traffic"}
}

# Two Primary User Roles (Reporter & Viewer) + Extended Authority
USER_ROLES = {
    "reporter": {
        "label": "Road Hazard Reporter",
        "icon": "📢",
        "tagline": "Submit hazards, upload photos & track reports",
        "description": "Authorized to file road hazard reports, upload incident photos, pin locations, and track fix status.",
        "can_submit_reports": True,
        "can_upload_photos": True,
        "can_view_own_reports": True,
        "can_view_approved": True,
        "can_search_locations": True,
        "dashboard_name": "📢 Reporter Dashboard"
    },
    "viewer": {
        "label": "Pre-Travel Hazard Viewer",
        "icon": "👀",
        "tagline": "Search locations, inspect hazards & check route safety",
        "description": "Authorized to view approved road reports, search locations, inspect hazard dossiers, and check route conditions before travelling.",
        "can_submit_reports": False,
        "can_upload_photos": False,
        "can_view_own_reports": False,
        "can_view_approved": True,
        "can_search_locations": True,
        "dashboard_name": "👀 Viewer Dashboard"
    },
    "citizen": {
        "label": "Road Hazard Reporter",
        "icon": "📢",
        "tagline": "Submit hazards, upload photos & track reports",
        "description": "Authorized to file road hazard reports, upload incident photos, and track fixes.",
        "can_submit_reports": True,
        "can_upload_photos": True,
        "can_view_own_reports": True,
        "can_view_approved": True,
        "can_search_locations": True,
        "dashboard_name": "📢 Reporter Dashboard"
    },
    "authority": {
        "label": "Road & Public Works Authority",
        "icon": "🏛️",
        "tagline": "Municipal dispatch and hazard resolution",
        "description": "Dispatch road maintenance work orders, verify and resolve hazards",
        "can_submit_reports": True,
        "can_upload_photos": True,
        "can_view_own_reports": True,
        "can_view_approved": True,
        "can_search_locations": True,
        "dashboard_name": "🏛️ Municipal Authority Portal"
    },
    "emergency": {
        "label": "Highway Emergency Services",
        "icon": "🚨",
        "tagline": "Highway patrol and SOS dispatch",
        "description": "Broadcast critical SOS alerts, prioritize rapid crash response",
        "can_submit_reports": True,
        "can_upload_photos": True,
        "can_view_own_reports": True,
        "can_view_approved": True,
        "can_search_locations": True,
        "dashboard_name": "🚨 Emergency Operations"
    }
}

# Preset Hub Cities with realistic road corridors
DEFAULT_CITIES = {
    "New York Metro, NY": {
        "lat": 40.7128,
        "lng": -74.0060,
        "zoom": 12,
        "radius_km": 25
    },
    "San Francisco Bay Area, CA": {
        "lat": 37.7749,
        "lng": -122.4194,
        "zoom": 12,
        "radius_km": 20
    },
    "Chicago Central, IL": {
        "lat": 41.8781,
        "lng": -87.6298,
        "zoom": 12,
        "radius_km": 22
    },
    "Austin Corridor, TX": {
        "lat": 30.2672,
        "lng": -97.7431,
        "zoom": 12,
        "radius_km": 20
    },
    "London Central Corridor, UK": {
        "lat": 51.5074,
        "lng": -0.1278,
        "zoom": 12,
        "radius_km": 18
    },
    "Bangalore Highway Hub, IN": {
        "lat": 12.9716,
        "lng": 77.5946,
        "zoom": 12,
        "radius_km": 25
    }
}

# Proximity Alert Radii (in meters)
RADAR_ZONES = {
    "critical": 350,   # Red audio/visual immediate braking warning
    "warning": 800,    # Orange visual lane caution
    "notice": 1800     # Blue route advisory notice
}

# Karma & Gamification Rules
KARMA_POINTS = {
    "submit_hazard": 25,
    "hazard_verified_by_others": 15,
    "vote_hazard": 5,
    "add_comment": 3,
    "hazard_resolved": 50
}

USER_RANKS = [
    {"name": "Novice Scout", "min_points": 0, "badge": "🌱"},
    {"name": "Route Watcher", "min_points": 50, "badge": "🔍"},
    {"name": "Highway Guardian", "min_points": 150, "badge": "🛡️"},
    {"name": "Road Sentinel", "min_points": 350, "badge": "⭐"},
    {"name": "Master Navigator", "min_points": 700, "badge": "👑"}
]
