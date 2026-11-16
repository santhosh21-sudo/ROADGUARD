"""
ROADGUARD - Database Layer (SQLite)
Thread-safe, self-initializing database manager with realistic pre-seeded hazard data.
"""

import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from config import DATABASE_PATH, HAZARD_CATEGORIES, SEVERITY_LEVELS, KARMA_POINTS, USER_RANKS
from supabase_client import (
    is_supabase_configured, supabase_insert_hazard, supabase_fetch_reports,
    supabase_fetch_approved_reports, supabase_fetch_user_reports,
    supabase_update_report_status, supabase_upsert_profile
)

def get_connection():
    """Create a connection with row factory enabled."""
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_pw(password: str, salt: str = "roadguard_salt_2026") -> str:
    """Standard SHA-256 password hash."""
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def calculate_badge(karma: int) -> str:
    """Determine the badge string from karma points."""
    badge_str = "🌱 Novice Scout"
    for rank in USER_RANKS:
        if karma >= rank["min_points"]:
            badge_str = f"{rank['badge']} {rank['name']}"
    return badge_str

def init_db():
    """Initializes tables and seeds initial data if database is empty."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supabase_uid TEXT UNIQUE,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT DEFAULT 'supabase_managed',
        salt TEXT DEFAULT 'supabase_managed',
        role TEXT NOT NULL DEFAULT 'citizen',
        full_name TEXT NOT NULL,
        karma_points INTEGER DEFAULT 25,
        avatar_icon TEXT DEFAULT '🚗',
        badge TEXT DEFAULT '🌱 Novice Scout',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Try to add supabase_uid column if table was previously created
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN supabase_uid TEXT UNIQUE")
    except Exception:
        pass

    # Sessions Table for Cross-Refresh Persistence
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS auth_sessions (
        session_token TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        email TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'viewer',
        access_token TEXT NOT NULL,
        refresh_token TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP
    );
    """)

    # Migrate legacy demo roles to Reporter and Viewer
    try:
        cursor.execute("UPDATE users SET role = 'reporter', avatar_icon = '📢' WHERE username IN ('alice', 'reporter_alice')")
        cursor.execute("UPDATE users SET role = 'viewer', avatar_icon = '👀' WHERE username IN ('david', 'viewer_bob')")
    except Exception:
        pass

    # 2. Hazards Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hazards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        severity TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Reported',
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        address TEXT,
        city TEXT,
        reported_by TEXT NOT NULL,
        reporter_name TEXT NOT NULL,
        upvotes INTEGER DEFAULT 1,
        downvotes INTEGER DEFAULT 0,
        lane_blocked INTEGER DEFAULT 0,
        photo_url TEXT,
        suggested_action TEXT,
        work_order_id TEXT,
        resolution_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP
    );
    """)

    # 3. Hazard Votes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hazard_votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hazard_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        vote_type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(hazard_id, username),
        FOREIGN KEY (hazard_id) REFERENCES hazards(id) ON DELETE CASCADE
    );
    """)

    # 4. Comments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hazard_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hazard_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        user_role TEXT NOT NULL,
        comment TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (hazard_id) REFERENCES hazards(id) ON DELETE CASCADE
    );
    """)

    # 5. System & Proximity Alerts Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hazard_id INTEGER,
        alert_type TEXT NOT NULL,
        severity TEXT,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        target_role TEXT DEFAULT 'all',
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 6. Saved Routes / Waypoints
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS routes_saved (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        name TEXT NOT NULL,
        start_city TEXT,
        start_lat REAL NOT NULL,
        start_lng REAL NOT NULL,
        end_city TEXT,
        end_lat REAL NOT NULL,
        end_lng REAL NOT NULL,
        risk_score INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    seed_default_data(conn)
    conn.close()

def seed_default_data(conn):
    """Seed default users and realistic hazards if empty."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()["count"] == 0:
        # Seed demo users showcasing both Reporter and Viewer roles
        demo_users = [
            ("alice", "alice@roadguard.org", "password123", "reporter", "Alice Walker", 195, "📢", "🛡️ Highway Guardian"),
            ("reporter_alice", "reporter@roadguard.org", "password123", "reporter", "Alice Walker (Lead Reporter)", 220, "📢", "⭐ Road Sentinel"),
            ("viewer_bob", "viewer@roadguard.org", "password123", "viewer", "Bob Miller (Commuter / Viewer)", 60, "👀", "🔍 Route Watcher"),
            ("david", "david@commute.net", "password123", "viewer", "David Miller", 75, "👀", "🔍 Route Watcher"),
            ("officer_bob", "bob@dot.gov", "password123", "authority", "Eng. Bob Henderson (City DOT)", 450, "🏛️", "⭐ Road Sentinel"),
            ("patrol_charlie", "charlie@police.state.gov", "password123", "emergency", "Capt. Charlie Ruiz (State Patrol Unit 4)", 520, "🚨", "👑 Master Navigator")
        ]
        for username, email, pw, role, full_name, karma, icon, badge in demo_users:
            cursor.execute("""
            INSERT INTO users (username, email, password_hash, salt, role, full_name, karma_points, avatar_icon, badge)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (username, email, hash_pw(pw), "roadguard_salt_2026", role, full_name, karma, icon, badge))
        conn.commit()

    cursor.execute("SELECT COUNT(*) as count FROM hazards")
    if cursor.fetchone()["count"] == 0:
        # Realistic sample hazards across 5 geographic hubs
        now = datetime.now()
        hazards_data = [
            # --- New York Metro ---
            (
                "Massive Crater Pothole on FDR Drive Northbound",
                "Pothole / Road Damage",
                "Deep 7-inch asphalt fracture in middle lane after heavy rain. Causing severe tire rim damage.",
                "High",
                "Community Verified",
                40.7308, -73.9742,
                "FDR Drive & E 20th St, New York, NY",
                "New York Metro, NY",
                "alice", "Alice Walker", 14, 0, 1,
                "Reduce speed to 25mph, shift to far left lane",
                None, None,
                (now - timedelta(hours=3)).isoformat()
            ),
            (
                "3-Vehicle Collision on Brooklyn Bridge Manhattan-bound",
                "Traffic Accident",
                "Rear-end multi-vehicle crash blocking two lanes. Police cruisers and tow truck on scene.",
                "Critical",
                "In Progress",
                40.7061, -73.9969,
                "Brooklyn Bridge Center Span, New York, NY",
                "New York Metro, NY",
                "patrol_charlie", "Capt. Charlie Ruiz (State Patrol Unit 4)", 38, 1, 1,
                "Detour via Manhattan Bridge or Hugh L. Carey Tunnel",
                "WO-NYC-8821", "FDNY and Highway Emergency Units attending. Towing in progress.",
                (now - timedelta(minutes=45)).isoformat()
            ),
            (
                "Submerged Highway Underpass near Long Island Expressway",
                "Road Flooding / Waterlogging",
                "Clogged storm drains causing 14 inches of standing water across Queens Blvd interchange.",
                "High",
                "Work Order Dispatched",
                40.7282, -73.8631,
                "Queens Blvd & LIE Underpass, Queens, NY",
                "New York Metro, NY",
                "david", "David Miller", 19, 0, 1,
                "Do not attempt to cross underpass; use side service road",
                "WO-NYC-8819", "Environmental pump truck en route.",
                (now - timedelta(hours=6)).isoformat()
            ),
            (
                "Traffic Signals Blackout at 5th Ave & 42nd St",
                "Traffic Signal Failure",
                "Power grid glitch caused all 4 intersection signals to flash dark. Gridlock forming.",
                "High",
                "Community Verified",
                40.7532, -73.9822,
                "5th Ave & W 42nd St, New York, NY",
                "New York Metro, NY",
                "alice", "Alice Walker", 22, 0, 0,
                "Treat as all-way stop; obey manual traffic officer gestures",
                None, None,
                (now - timedelta(hours=1, minutes=15)).isoformat()
            ),
            (
                "Resolved: Fallen Oak Branch on West Side Highway",
                "Fallen Tree / Road Debris",
                "Large branch fell during morning gale winds. Completely cleared by parkway maintenance.",
                "Medium",
                "Resolved",
                40.7610, -74.0010,
                "West Side Hwy & 54th St, New York, NY",
                "New York Metro, NY",
                "officer_bob", "Eng. Bob Henderson (City DOT)", 29, 0, 0,
                "Road completely cleared and inspected.",
                "WO-NYC-8799", "Maintenance crew chopped and hauled away wood. Asphalt swept.",
                (now - timedelta(hours=18)).isoformat()
            ),

            # --- San Francisco Bay Area ---
            (
                "Overturned Delivery Truck on Bay Bridge Westbound",
                "Traffic Accident",
                "Box truck tipped on its side near Yerba Buena Island exit. Upper deck traffic stalled.",
                "Critical",
                "In Progress",
                37.8118, -122.3653,
                "I-80 W Bay Bridge Span, San Francisco, CA",
                "San Francisco Bay Area, CA",
                "patrol_charlie", "Capt. Charlie Ruiz (State Patrol Unit 4)", 52, 2, 1,
                "Expect 45 min delay. Utilize BART or San Mateo Bridge",
                "WO-SF-4402", "Heavy rotator crane uprighting vehicle. Left two lanes cleared.",
                (now - timedelta(minutes=30)).isoformat()
            ),
            (
                "Mudslide / Earth Debris on CA-1 Pacific Coast Highway",
                "Road Cave-in / Landslide",
                "Steep cliff runoff deposited 2 tons of wet mud and rock across southbound lane.",
                "Critical",
                "Work Order Dispatched",
                37.7550, -122.5080,
                "Great Highway & Lincoln Way, San Francisco, CA",
                "San Francisco Bay Area, CA",
                "alice", "Alice Walker", 31, 0, 1,
                "Detour via Sunset Blvd or 19th Ave",
                "WO-SF-4399", "Bulldozer crew dispatched by Caltrans.",
                (now - timedelta(hours=4)).isoformat()
            ),
            (
                "Major Asphalt Trench on Market Street at 8th",
                "Pothole / Road Damage",
                "Sunken utility trench with exposed steel road plate edges damaging low-clearance vehicles.",
                "Medium",
                "Reported",
                37.7785, -122.4150,
                "Market St & 8th St, San Francisco, CA",
                "San Francisco Bay Area, CA",
                "david", "David Miller", 8, 1, 0,
                "Steer slightly left toward streetcar tracks",
                None, None,
                (now - timedelta(hours=2)).isoformat()
            ),

            # --- Austin Corridor, TX ---
            (
                "Multi-Vehicle Crash on I-35 Lower Deck Southbound",
                "Traffic Accident",
                "Three cars involved in high-speed pileup near 12th street exit. Fuel leak on roadway.",
                "Critical",
                "In Progress",
                30.2745, -97.7335,
                "I-35 Southbound & 12th St, Austin, TX",
                "Austin Corridor, TX",
                "patrol_charlie", "Capt. Charlie Ruiz (State Patrol Unit 4)", 44, 0, 1,
                "Divert to Upper Deck I-35 or take Airport Blvd",
                "WO-ATX-1090", "Hazardous materials absorbent spread. Paramedics clearing scene.",
                (now - timedelta(minutes=50)).isoformat()
            ),
            (
                "Flash Flood Water Surge across Barton Springs Road",
                "Road Flooding / Waterlogging",
                "Rapid creek swelling pushing 10 inches of rapid water over low-water crossing.",
                "High",
                "Community Verified",
                30.2635, -97.7695,
                "Barton Springs Rd & Stratford Dr, Austin, TX",
                "Austin Corridor, TX",
                "alice", "Alice Walker", 17, 0, 1,
                "Turn Around, Don't Drown. Low-water crossing gates lowered.",
                None, None,
                (now - timedelta(hours=3, minutes=20)).isoformat()
            ),
            (
                "Heavy Construction Work Zone on MoPac Expressway",
                "Construction / Work Zone",
                "Sound wall installation and lane repaving. Speed reduced from 65 to 45 mph.",
                "Medium",
                "In Progress",
                30.3080, -97.7560,
                "Loop 1 (MoPac) Northbound near 45th St, Austin, TX",
                "Austin Corridor, TX",
                "officer_bob", "Eng. Bob Henderson (City DOT)", 25, 0, 0,
                "Strict 45 mph enforced. Fines doubled in work zone.",
                "WO-ATX-1011", "Night shift resurfacing ongoing.",
                (now - timedelta(days=1)).isoformat()
            ),

            # --- London Central, UK ---
            (
                "Oil Slick near Hyde Park Corner Roundabout",
                "Oil Spill / Slippery Surface",
                "Bus hydraulic fluid spilled over 60 meters of the circular carriageway. High skid risk.",
                "High",
                "Work Order Dispatched",
                51.5033, -0.1517,
                "Hyde Park Corner, London, UK",
                "London Central Corridor, UK",
                "david", "David Miller", 27, 0, 1,
                "Decelerate gently before entering roundabout; avoid hard braking",
                "WO-LON-7110", "TfL sanding team on route to treat surface.",
                (now - timedelta(hours=2, minutes=45)).isoformat()
            ),
            (
                "Broken Water Main on Tower Bridge Approach",
                "Road Flooding / Waterlogging",
                "Thames Water main burst causing pressure geyser and localized road flooding.",
                "High",
                "In Progress",
                51.5055, -0.0754,
                "Tower Bridge S Approach & Tooley St, London, UK",
                "London Central Corridor, UK",
                "alice", "Alice Walker", 35, 1, 1,
                "Expect heavy congestion. Use London Bridge alternate",
                "WO-LON-7098", "Engineers isolating burst pipe valve.",
                (now - timedelta(hours=5)).isoformat()
            ),

            # --- Bangalore Hub, IN ---
            (
                "Severe Waterlogging under Silk Board Flyover Junction",
                "Road Flooding / Waterlogging",
                "2 feet deep monsoon accumulation. Heavy slow moving traffic towards Electronic City.",
                "Critical",
                "Work Order Dispatched",
                12.9175, 77.6238,
                "Central Silk Board Junction, Outer Ring Rd, Bangalore, IN",
                "Bangalore Highway Hub, IN",
                "david", "David Miller", 64, 0, 1,
                "Two-wheelers avoid underpass; use elevated expressway if possible",
                "WO-BLR-3102", "BBMP emergency suction pumps engaged.",
                (now - timedelta(hours=1, minutes=40)).isoformat()
            ),
            (
                "Deep Unmarked Crater Pothole on Outer Ring Road Bellandur",
                "Pothole / Road Damage",
                "Massive pothole hidden near tech park gate causing two-wheeler skids and bumper hits.",
                "High",
                "Community Verified",
                12.9298, 77.6835,
                "Outer Ring Rd near EcoSpace, Bellandur, Bangalore, IN",
                "Bangalore Highway Hub, IN",
                "alice", "Alice Walker", 41, 1, 1,
                "Stick to extreme right bus corridor lane to bypass depression",
                None, None,
                (now - timedelta(hours=4, minutes=10)).isoformat()
            )
        ]

        for h in hazards_data:
            cursor.execute("""
            INSERT INTO hazards (
                title, category, description, severity, status,
                latitude, longitude, address, city,
                reported_by, reporter_name, upvotes, downvotes, lane_blocked,
                suggested_action, work_order_id, resolution_notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, h)

        # Seed initial comments
        comments_data = [
            (1, "officer_bob", "authority", "City DOT inspection team dispatched to measure pothole dimensions and deploy asphalt cold mix."),
            (1, "david", "citizen", "Confirmed, nearly blew my tire out 15 mins ago. Drive slow!"),
            (2, "patrol_charlie", "emergency", "Center lane is now opened. Tow truck hooked up the second sedan."),
            (6, "patrol_charlie", "emergency", "Heavy rotator has pulled vehicle upright. Opening two lanes shortly."),
            (9, "officer_bob", "authority", "Hazardous materials team has contained diesel spill on I-35.")
        ]
        for c in comments_data:
            cursor.execute("""
            INSERT INTO hazard_comments (hazard_id, username, user_role, comment)
            VALUES (?, ?, ?, ?)
            """, c)

        # Seed initial alerts
        alerts_data = [
            (2, "SOS_BROADCAST", "Critical", "URGENT: Brooklyn Bridge Multi-Car Collision", "Emergency response units on scene. Expect severe delays eastbound/westbound.", "all"),
            (6, "SOS_BROADCAST", "Critical", "Bay Bridge Overturned Truck Alert", "Westbound lanes restricted. Plan alternate transit routes.", "all"),
            (1, "WORK_ORDER", "High", "Work Order Issued: FDR Drive Pothole", "Pothole patch crew assigned work order WO-NYC-8821.", "authority")
        ]
        for a in alerts_data:
            cursor.execute("""
            INSERT INTO alerts_log (hazard_id, alert_type, severity, title, message, target_role)
            VALUES (?, ?, ?, ?, ?, ?)
            """, a)

        conn.commit()

# --- Hazard Operations ---

def get_hazards(
    city: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    search_query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieve hazards from permanent Supabase database with local SQLite cache fallback."""
    # 1. Permanent Supabase Database Query
    if is_supabase_configured():
        ok, supa_rows = supabase_fetch_reports(
            city=city,
            category=category,
            severity=severity,
            status=status,
            search_query=search_query
        )
        if ok and supa_rows:
            return supa_rows

    # 2. Local SQLite Persistent Cache
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM hazards WHERE 1=1"
    params = []

    if city and city != "All Cities":
        query += " AND city = ?"
        params.append(city)

    if category and category != "All Categories":
        query += " AND category = ?"
        params.append(category)

    if severity and severity != "All Severities":
        query += " AND severity = ?"
        params.append(severity)

    if status and status != "All Statuses":
        query += " AND status = ?"
        params.append(status)

    if search_query:
        query += " AND (title LIKE ? OR description LIKE ? OR address LIKE ?)"
        like_term = f"%{search_query}%"
        params.extend([like_term, like_term, like_term])

    query += " ORDER BY CASE severity WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END, created_at DESC"
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_approved_hazards(
    search_query: Optional[str] = None,
    city: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve approved, community-verified, and resolved road reports for Viewer accounts.
    Pulls permanently from Supabase 'road_hazard_reports' when connected.
    """
    # 1. Permanent Supabase Query
    if is_supabase_configured():
        ok, supa_rows = supabase_fetch_approved_reports(
            search_query=search_query,
            city=city,
            category=category,
            severity=severity
        )
        if ok and supa_rows:
            return supa_rows

    # 2. Local SQLite Fallback
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM hazards WHERE status IN ('Community Verified', 'Work Order Dispatched', 'In Progress', 'Resolved')"
    params = []

    if city and city != "All Cities":
        query += " AND city = ?"
        params.append(city)

    if category and category != "All Categories":
        query += " AND category = ?"
        params.append(category)

    if severity and severity != "All Severities":
        query += " AND severity = ?"
        params.append(severity)

    if search_query:
        query += " AND (title LIKE ? OR description LIKE ? OR address LIKE ? OR city LIKE ?)"
        term = f"%{search_query.strip()}%"
        params.extend([term, term, term, term])

    query += " ORDER BY CASE severity WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END, created_at DESC"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_user_submitted_reports(username: str) -> List[Dict[str, Any]]:
    """Retrieve all hazard reports filed by a specific Reporter from Supabase Database."""
    # 1. Permanent Supabase Query
    if is_supabase_configured():
        ok, supa_rows = supabase_fetch_user_reports(username)
        if ok and supa_rows:
            return supa_rows

    # 2. Local SQLite Fallback
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM hazards
        WHERE reported_by = ?
        ORDER BY created_at DESC
    """, (username,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_hazard_by_id(hazard_id: int) -> Optional[Dict[str, Any]]:
    """Get single hazard details by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hazards WHERE id = ?", (hazard_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_hazard(data: Dict[str, Any]) -> int:
    """Insert a new hazard permanently into Supabase Database and local DB, and reward karma to reporter."""
    if is_supabase_configured():
        try:
            supabase_insert_hazard(data)
        except Exception:
            pass

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO hazards (
        title, category, description, severity, status,
        latitude, longitude, address, city,
        reported_by, reporter_name, upvotes, downvotes, lane_blocked,
        photo_url, suggested_action, work_order_id, resolution_notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?, ?, ?, ?, ?)
    """, (
        data["title"],
        data["category"],
        data.get("description", ""),
        data["severity"],
        data.get("status", "Reported"),
        data["latitude"],
        data["longitude"],
        data.get("address", "Pinned Location"),
        data.get("city", "Custom Area"),
        data["reported_by"],
        data["reporter_name"],
        1 if data.get("lane_blocked") else 0,
        data.get("photo_url", ""),
        data.get("suggested_action", ""),
        data.get("work_order_id", None),
        data.get("resolution_notes", "")
    ))
    hazard_id = cursor.lastrowid

    # Auto-register reporter's upvote
    cursor.execute("""
    INSERT INTO hazard_votes (hazard_id, username, vote_type)
    VALUES (?, ?, 'upvote')
    """, (hazard_id, data["reported_by"]))

    # Give karma to user
    cursor.execute("""
    UPDATE users SET karma_points = karma_points + ? WHERE username = ?
    """, (KARMA_POINTS["submit_hazard"], data["reported_by"]))

    # Update badge
    cursor.execute("SELECT karma_points FROM users WHERE username = ?", (data["reported_by"],))
    u_row = cursor.fetchone()
    if u_row:
        new_badge = calculate_badge(u_row["karma_points"])
        cursor.execute("UPDATE users SET badge = ? WHERE username = ?", (new_badge, data["reported_by"]))

    # Log an alert if High or Critical
    if data["severity"] in ["High", "Critical"]:
        cursor.execute("""
        INSERT INTO alerts_log (hazard_id, alert_type, severity, title, message, target_role)
        VALUES (?, 'NEW_HAZARD', ?, ?, ?, 'all')
        """, (
            hazard_id,
            data["severity"],
            f"Alert: {data['title']}",
            f"New {data['severity']} hazard reported at {data.get('address', 'Location')}. {data.get('suggested_action', '')}"
        ))

    conn.commit()
    conn.close()
    return hazard_id

def update_hazard_status(hazard_id: int, new_status: str, notes: str, updated_by_username: str) -> bool:
    """Update hazard status, work order, and resolution details permanently in Supabase and local DB."""
    if is_supabase_configured():
        try:
            supabase_update_report_status(hazard_id, new_status, notes)
        except Exception:
            pass

    conn = get_connection()
    cursor = conn.cursor()
    now_iso = datetime.now().isoformat()

    resolved_time = now_iso if new_status == "Resolved" else None
    cursor.execute("""
    UPDATE hazards
    SET status = ?, resolution_notes = ?, updated_at = ?, resolved_at = COALESCE(?, resolved_at)
    WHERE id = ?
    """, (new_status, notes, now_iso, resolved_time, hazard_id))

    # Log activity in comments
    cursor.execute("""
    INSERT INTO hazard_comments (hazard_id, username, user_role, comment)
    VALUES (?, ?, 'authority', ?)
    """, (hazard_id, updated_by_username, f"Status updated to '{new_status}': {notes}"))

    # Log system alert
    cursor.execute("SELECT title, reported_by FROM hazards WHERE id = ?", (hazard_id,))
    h_row = cursor.fetchone()
    if h_row:
        cursor.execute("""
        INSERT INTO alerts_log (hazard_id, alert_type, severity, title, message, target_role)
        VALUES (?, 'STATUS_CHANGE', 'Medium', ?, ?, 'all')
        """, (
            hazard_id,
            f"Hazard Status Update: {h_row['title'][:40]}...",
            f"Status changed to [{new_status}]. Note: {notes}"
        ))
        # Reward reporter if resolved
        if new_status == "Resolved":
            cursor.execute("""
            UPDATE users SET karma_points = karma_points + ? WHERE username = ?
            """, (KARMA_POINTS["hazard_resolved"], h_row["reported_by"]))

    conn.commit()
    conn.close()
    return True

def cast_vote(hazard_id: int, username: str, vote_type: str) -> Dict[str, Any]:
    """Vote on a hazard (upvote or downvote) with community verification threshold."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT vote_type FROM hazard_votes WHERE hazard_id = ? AND username = ?", (hazard_id, username))
    existing = cursor.fetchone()

    if existing:
        if existing["vote_type"] == vote_type:
            conn.close()
            return {"success": False, "message": f"You already {vote_type}d this hazard."}
        else:
            # Change vote
            cursor.execute("""
            UPDATE hazard_votes SET vote_type = ? WHERE hazard_id = ? AND username = ?
            """, (vote_type, hazard_id, username))
            if vote_type == "upvote":
                cursor.execute("UPDATE hazards SET upvotes = upvotes + 1, downvotes = MAX(0, downvotes - 1) WHERE id = ?", (hazard_id,))
            else:
                cursor.execute("UPDATE hazards SET downvotes = downvotes + 1, upvotes = MAX(0, upvotes - 1) WHERE id = ?", (hazard_id,))
    else:
        cursor.execute("""
        INSERT INTO hazard_votes (hazard_id, username, vote_type) VALUES (?, ?, ?)
        """, (hazard_id, username, vote_type))
        if vote_type == "upvote":
            cursor.execute("UPDATE hazards SET upvotes = upvotes + 1 WHERE id = ?", (hazard_id,))
        else:
            cursor.execute("UPDATE hazards SET downvotes = downvotes + 1 WHERE id = ?", (hazard_id,))

    # Check for auto community verification (if >= 3 upvotes and still 'Reported')
    cursor.execute("SELECT upvotes, status, reported_by FROM hazards WHERE id = ?", (hazard_id,))
    h_row = cursor.fetchone()
    if h_row and h_row["upvotes"] >= 3 and h_row["status"] == "Reported":
        cursor.execute("UPDATE hazards SET status = 'Community Verified' WHERE id = ?", (hazard_id,))
        # Reward reporter
        cursor.execute("UPDATE users SET karma_points = karma_points + ? WHERE username = ?", (KARMA_POINTS["hazard_verified_by_others"], h_row["reported_by"]))

    # Reward voter
    cursor.execute("UPDATE users SET karma_points = karma_points + ? WHERE username = ?", (KARMA_POINTS["vote_hazard"], username))

    conn.commit()
    conn.close()
    return {"success": True, "message": f"Vote recorded! Thank you for keeping roads safe."}

def add_comment(hazard_id: int, username: str, user_role: str, comment_text: str) -> bool:
    """Add community or official comment to hazard."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO hazard_comments (hazard_id, username, user_role, comment)
    VALUES (?, ?, ?, ?)
    """, (hazard_id, username, user_role, comment_text))
    cursor.execute("UPDATE users SET karma_points = karma_points + ? WHERE username = ?", (KARMA_POINTS["add_comment"], username))
    conn.commit()
    conn.close()
    return True

def get_comments(hazard_id: int) -> List[Dict[str, Any]]:
    """Retrieve comments for a specific hazard."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.*, u.full_name, u.avatar_icon, u.badge
    FROM hazard_comments c
    LEFT JOIN users u ON c.username = u.username
    WHERE c.hazard_id = ?
    ORDER BY c.created_at ASC
    """, (hazard_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

# --- User & Auth Operations ---

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Fetch user profile by username."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Fetch user profile by email address."""
    if not email:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def sync_supabase_user(supabase_user: Dict[str, Any], role_override: Optional[str] = None) -> Dict[str, Any]:
    """
    Synchronizes a user authenticated via Supabase (email/password or Google OAuth) with ROADGUARD database.
    Preserves Safety Karma, civic rank badges, and hazard reporting history.
    """
    conn = get_connection()
    cursor = conn.cursor()

    uid = supabase_user.get("id") or ""
    email = (supabase_user.get("email") or "").strip().lower()
    user_meta = supabase_user.get("user_metadata") or {}

    full_name = (
        user_meta.get("full_name") or
        user_meta.get("name") or
        (email.split("@")[0].title() if email else "RoadGuard Driver")
    )
    role = role_override or user_meta.get("role") or "citizen"
    base_username = email.split("@")[0].lower().replace(".", "_") if email else f"user_{uid[:6]}"

    # Check if user already exists by email or supabase_uid
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = ? OR supabase_uid = ?", (email, uid))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE users SET supabase_uid = COALESCE(?, supabase_uid), full_name = COALESCE(?, full_name)
            WHERE id = ?
        """, (uid, full_name, existing["id"]))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE id = ?", (existing["id"],))
        user_row = dict(cursor.fetchone())
    else:
        # Check username uniqueness
        cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE username = ?", (base_username,))
        final_uname = base_username if cursor.fetchone()["cnt"] == 0 else f"{base_username}_{uid[:4]}"
        icon = "🏛️" if role == "authority" else ("🚨" if role == "emergency" else "🚗")
        cursor.execute("""
            INSERT INTO users (supabase_uid, username, email, password_hash, salt, role, full_name, karma_points, avatar_icon, badge)
            VALUES (?, ?, ?, 'supabase_managed', 'supabase_managed', ?, ?, 25, ?, '🌱 Novice Scout')
        """, (uid, final_uname, email, role, full_name, icon))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user_row = dict(cursor.fetchone())

    conn.close()

    # Synchronize profile into Supabase 'user_profiles' table permanently
    if is_supabase_configured() and uid:
        try:
            supabase_upsert_profile(
                user_id=uid,
                email=email,
                username=user_row.get("username", base_username),
                full_name=user_row.get("full_name", full_name),
                role=user_row.get("role", role),
                karma=user_row.get("karma_points", 25)
            )
        except Exception:
            pass

    return user_row

def save_session(
    session_token: str,
    user_dict: Dict[str, Any],
    access_token: str,
    refresh_token: Optional[str] = None,
    expires_in_sec: int = 604800  # 7 days
) -> bool:
    """Stores an authenticated user session in the persistent database."""
    conn = get_connection()
    cursor = conn.cursor()
    expires_at = (datetime.now() + timedelta(seconds=expires_in_sec)).isoformat()
    cursor.execute("""
        INSERT OR REPLACE INTO auth_sessions (
            session_token, user_id, email, full_name, role, access_token, refresh_token, expires_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_token,
        str(user_dict.get("id") or user_dict.get("supabase_uid") or ""),
        user_dict.get("email", ""),
        user_dict.get("full_name", ""),
        user_dict.get("role", "citizen"),
        access_token,
        refresh_token or "",
        expires_at
    ))
    conn.commit()
    conn.close()
    return True

def get_session(session_token: str) -> Optional[Dict[str, Any]]:
    """Retrieves an active session token, validating expiration."""
    if not session_token:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM auth_sessions WHERE session_token = ?", (session_token,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    s = dict(row)
    if s.get("expires_at"):
        try:
            if datetime.now() > datetime.fromisoformat(s["expires_at"]):
                delete_session(session_token)
                return None
        except Exception:
            pass
    return s

def delete_session(session_token: str) -> bool:
    """Removes a session token from persistent storage upon logout."""
    if not session_token:
        return True
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM auth_sessions WHERE session_token = ?", (session_token,))
    conn.commit()
    conn.close()
    return True

def create_user(username: str, email: str, password: str, full_name: str, role: str = "citizen") -> Tuple[bool, str]:
    """Register a new user."""
    conn = get_connection()
    cursor = conn.cursor()
    salt = "roadguard_salt_2026"
    pw_hash = hash_pw(password, salt)
    icon = "👤" if role == "citizen" else ("🏛️" if role == "authority" else "🚨")

    try:
        cursor.execute("""
        INSERT INTO users (username, email, password_hash, salt, role, full_name, karma_points, avatar_icon, badge)
        VALUES (?, ?, ?, ?, ?, ?, 25, ?, '🌱 Novice Scout')
        """, (username, email, pw_hash, salt, role, full_name, icon))
        conn.commit()
        conn.close()
        return True, "User registered successfully!"
    except sqlite3.IntegrityError as e:
        conn.close()
        if "username" in str(e):
            return False, "Username already exists. Please choose another."
        elif "email" in str(e):
            return False, "Email already registered."
        return False, f"Registration failed: {e}"

def get_leaderboard(limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve top community contributors."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT username, full_name, role, karma_points, avatar_icon, badge,
           (SELECT COUNT(*) FROM hazards WHERE reported_by = users.username) as reports_count
    FROM users
    ORDER BY karma_points DESC
    LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

# --- Alerts & Notifications ---

def get_alerts(limit: int = 15) -> List[Dict[str, Any]]:
    """Fetch recent alert feed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT a.*, h.category, h.address, h.city
    FROM alerts_log a
    LEFT JOIN hazards h ON a.hazard_id = h.id
    ORDER BY a.created_at DESC
    LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def log_broadcast_alert(title: str, message: str, severity: str = "Critical", hazard_id: Optional[int] = None) -> int:
    """Publish an emergency broadcast notification."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO alerts_log (hazard_id, alert_type, severity, title, message, target_role)
    VALUES (?, 'SOS_BROADCAST', ?, ?, ?, 'all')
    """, (hazard_id, severity, title, message))
    alert_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return alert_id

# --- Analytics Summary ---

def get_analytics_summary() -> Dict[str, Any]:
    """Calculate platform-wide hazard statistics."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM hazards")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as active FROM hazards WHERE status != 'Resolved'")
    active = cursor.fetchone()["active"]

    cursor.execute("SELECT COUNT(*) as resolved FROM hazards WHERE status = 'Resolved'")
    resolved = cursor.fetchone()["resolved"]

    cursor.execute("SELECT COUNT(*) as critical FROM hazards WHERE severity = 'Critical' AND status != 'Resolved'")
    critical = cursor.fetchone()["critical"]

    cursor.execute("SELECT COUNT(*) as verified FROM hazards WHERE status IN ('Community Verified', 'In Progress')")
    verified = cursor.fetchone()["verified"]

    cursor.execute("""
    SELECT category, COUNT(*) as count
    FROM hazards
    GROUP BY category
    ORDER BY count DESC
    """)
    cat_breakdown = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
    SELECT city, COUNT(*) as count
    FROM hazards
    WHERE city IS NOT NULL
    GROUP BY city
    ORDER BY count DESC
    """)
    city_breakdown = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "total_hazards": total,
        "active_hazards": active,
        "resolved_hazards": resolved,
        "critical_hazards": critical,
        "verified_hazards": verified,
        "category_breakdown": cat_breakdown,
        "city_breakdown": city_breakdown
    }
