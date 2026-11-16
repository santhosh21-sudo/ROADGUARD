# ROADGUARD 🛡️
### Smart Road Hazard Reporting & Navigation System

**ROADGUARD** is a production-grade, community-powered road safety intelligence and navigation web application built with Python and Streamlit. It connects daily commuters, emergency responders, and municipal road maintenance departments to report, verify, navigate around, and resolve roadway hazards in real time.

Designed with a modern, high-contrast light theme featuring a professional **blue, white, and green** color palette.

---

## 🌟 Key Capabilities & Features

### 1. 🔐 Complete Supabase Authentication System
- **Email & Password Sign Up:** Validates strong passwords (min 8 chars, uppercase, lowercase, numbers). Passwords are never stored in plain text and are securely handled by Supabase GoTrue.
- **Email & Password Sign In:** Authenticates users and generates secure GoTrue JWT session tokens.
- **Google OAuth Login:** Single-click sign-in via Supabase Google OAuth integration.
- **Cross-Refresh Session Persistence:** Maintains user session state across browser reloads (F5) using secure query tokens and persistent SQLite session storage.
- **Protected Application Pages:** Unauthenticated users are gated behind a secure, modern Authentication Portal.
- **Prominent Logout Button:** Clears session state and invalidates tokens on Supabase.
- **Friendly Validation & Error Messages:** Translates raw error codes into clear, helpful guidance.

### 2. 🗺️ Interactive Road Hazard Map & Geospatial Radar (Folium + Streamlit)
- **Real Supabase Reports:** Directly visualizes genuine road hazard reports stored permanently in Supabase Database.
- **Distinct Hazard Markers:** Tailored icons and colors for each hazard type:
  - 🕳️ **Potholes:** Dark Red with exclamation mark.
  - 🚧 **Road Construction:** Orange with wrench icon.
  - 🔧 **Road Repair:** Blue with gear/tool icon.
  - 🌧️ **Rain Damage:** Dark Blue with storm cloud icon.
  - 🌊 **Waterlogging:** Cadet Blue with water droplet icon.
  - 💥 **Accident / Road Blockage:** Red with emergency cross mark.
  - ✅ **Resolved:** Green with checkmark.
- **Rich Click Popups with Photos:** Clicking any marker reveals problem descriptions, uploaded evidence photos, street address, timestamp, driver advisories, and status badges.
- **Location Search:** Viewers can search any street, highway, landmark, or city to auto-center the map.
- **User Current Location:** Detects device GPS coordinates upon user permission, plotting a distinct purple user marker with a pulsing radar buffer.
- **Nearby Hazards Radar:** Filters road hazards by adjustable distance radius (1–30 km) and displays a sorted proximity alert list.
- **Responsive Layout:** Automatically scales across desktop, tablet, and mobile viewports.

### 3. 🧭 Smart Route Planning & Road Hazard Alert System (OSRM + Geospatial Radar)
- **Origin & Destination Selection:** Viewers can enter starting locations and destinations via:
  - **Preset Commuter Corridors:** Instant 1-click selection across major urban corridors (New York, San Francisco, Austin, Bangalore, London).
  - **Location & Address Search:** Geocoded search with offline metropolitan dictionary and OpenStreetMap Nominatim resolver.
  - **Custom GPS Coordinates:** Precise numeric latitude and longitude inputs.
- **Real-Time Routing Service (OSRM):** Connects to the Open Source Routing Machine (OSRM) driving API to retrieve actual turn-by-turn geometry, route distance (km/miles), and estimated driving duration.
- **Graceful Error Handling & Fallback:** If the external routing service is unavailable (network timeout, offline, rate limit), ROADGUARD displays a clear, informative notification and automatically switches to a high-precision sinusoidal geometric corridor estimator. Hazard detection is never interrupted!
- **Corridor Hazard Scanning:** Scans all active ROADGUARD reports within an adjustable radar buffer (250m to 2000m) along the driving route using point-to-segment Haversine math.
- **Targeted Road Hazard Warnings:** Issues dedicated warning cards and actionable advisories for:
  - 🕳️ **Potholes Alert:** Warnings for rim deformation, axle damage, and tire puncture risks.
  - 🚧 **Road Construction Alert:** Work zones, barricades, lane narrowing, and reduced construction speed zones.
  - 🔧 **Road Repair Alert:** Resurfacing, fresh bitumen, uneven asphalt grading, and road workers.
  - 🌧️ **Rain Damage Alert:** Storm washouts, mud/gravel slicks, and soft road shoulder erosion.
  - 🌊 **Waterlogging Alert:** Submerged pavement, deep puddles, and severe hydroplaning hazards ("Turn Around, Don't Drown").
  - 💥 **Accident / Blockage Alert:** Vehicle collisions, fuel leaks, and full lane stoppages with detour guidance.
- **Clear Distinction Between Reported and Verified Hazards:**
  - `🛡️ VERIFIED HAZARDS`: Solid shield markers and green badges for reports confirmed by municipal public works teams or validated by community consensus.
  - `📝 UNVERIFIED CITIZEN REPORTS`: Amber warning markers and yellow badges for user-submitted reports pending municipal field inspection.
  - Separate tabs and filter controls allow viewers to inspect verified hazards vs unverified triage items.
- **Strict Safety Constraint (No False Safety Claims):** ROADGUARD **never** claims a road is safe just because zero reports are on file. When no reports are detected, an explicit safety disclaimer reminds drivers: *"Absence of reports does not guarantee that the road is safe or clear. Conditions change dynamically. Always maintain defensive driving vigilance."*

### 4. ⚠️ Citizen Hazard Reporting Center
- **Incident Categorization:** Potholes, Collisions, Flooding, Fallen Trees, Work Zones, Traffic Signal Blackouts, Oil Slicks, Landslides, and Animals.
- **Location Selector:** Preset metropolitan corridors with auto-coordinate filling and manual GPS pinpointing.
- **Real-Time Alert Preview Card:** Renders an exact preview of the alert banner motorists will receive before submitting.
- **Civic Gamification:** Earn **+25 Safety Karma** for submissions, unlocking ranks from *Novice Scout* to *Master Navigator*.

### 5. 🚨 Driver Mode & Heads-Up Proximity Radar (HUD)
- **Real-Time Radar Simulation:** Tracks vehicle GPS coordinates, speed, and heading.
- **3-Tier Safety Envelopes:** Critical (< 350m, red banner & audio chime), Caution (350m–800m), and Advisory (< 1.8km).
- **Emergency SOS Broadcaster:** Instant network-wide broadcast of urgent obstructions to all active drivers.

### 6. 🏛️ Municipal Authority & Public Works Portal
- **Incident Triage Queue:** Filter by *Reported*, *Community Verified*, *Work Order Dispatched*, *In Progress*, and *Resolved*.
- **Work Order Management:** Assign official municipal dispatch codes (e.g. `WO-NYC-8822`) and repair squads.

---

## 👥 Two Tailored User Roles & Dedicated Dashboards

ROADGUARD enforces clean Role-Based Access Control (RBAC) with tailored dashboards:

### 📢 ROLE 1: REPORTER
- **Submit Road Hazard Reports:** Multi-category hazard submission studio (potholes, accidents, flooding, debris, cave-ins, etc.).
- **Upload Problem Photos:** File uploader for real camera snapshots (PNG, JPG, JPEG) and scenario evidence.
- **Pin Location & Details:** GPS coordinate picker, corridor preset selection, address landmark, and description.
- **My Submitted Reports Tracker:** Personal timeline tracking verification progress (`Reported` ➔ `Community Verified` ➔ `Work Order Dispatched` ➔ `Resolved`), upvote counts, and Public Works comments.
- **Dedicated Dashboard:** [reporter_dashboard.py](file:///C:/Users/santhosh/.gemini/antigravity/scratch/roadguard/reporter_dashboard.py)

### 👀 ROLE 2: VIEWER
- **View Approved Road Reports:** Filtered stream displaying only community-verified, dispatched, and resolved road hazards.
- **Location Search:** Search by highway name, street address, city corridor, or keyword.
- **Inspect Hazard Dossiers:** Detailed inspection panel with evidence photos, severity tags, GPS coordinates, and recommended driver precautions.
- **Pre-Travel Road Conditions Checker:** Check road conditions before travelling between origin and destination, evaluate corridor risk scores (`A+` to `D`), and view recommended safe bypasses.
- **Dedicated Dashboard:** [viewer_dashboard.py](file:///C:/Users/santhosh/.gemini/antigravity/scratch/roadguard/viewer_dashboard.py)

---

## 📁 Clean Project Structure

```text
roadguard/
├── app.py                          # Main layout, navigation menu & multi-page orchestrator
├── landing_page.py                 # (NEW) Academic capstone landing page & project showcase
├── auth.py                         # Supabase Auth, login/signup portals & role gates
├── reporter_dashboard.py           # Dedicated operations dashboard for ROLE 1: REPORTER
├── viewer_dashboard.py             # Dedicated pre-travel & inspection dashboard for ROLE 2: VIEWER
├── reporting.py                    # Multi-step road hazard reporting wizard with photo upload
├── map_view.py                     # Folium geospatial radar, filters, clusters & heatmap
├── routing_service.py              # OSRM driving route engine, geocoding & hazard analysis
├── route_planner.py                # Interactive route planning, hazard alerts & Folium map
├── alerts.py                       # Driver Mode HUD, audio chime & SOS broadcasting
├── my_reports.py                   # (NEW) Submitted reports tracker with lifecycle status pipeline
├── profile_page.py                 # (NEW) User profile, Safety Karma rank progression & logout
├── config.py                       # User roles (Reporter & Viewer), severities, colors
├── database.py                     # SQLite engine, approved hazards query & session vault
├── supabase_client.py              # Supabase GoTrue Auth REST client (Signup/Signin/OAuth)
├── schema.sql                      # Permanent Supabase PostgreSQL Schema & RLS Policies
├── requirements.txt                # Python package dependencies
├── utils.py                        # Haversine math, corridor risk scores & CSS theme
├── README.md                       # Documentation & setup guide
├── .streamlit/
│   ├── config.toml                 # Streamlit theme (Blue/White/Green palette)
│   └── secrets.toml.example        # Environment and Supabase API template
└── uploads/                        # Incident evidence image directory
```

---

## 🔧 Supabase Configuration Guide

To enable live Supabase Authentication for ROADGUARD, follow these steps:

### Step 1: Create a Supabase Project
1. Go to [https://supabase.com](https://supabase.com) and create an account or sign in.
2. Click **New Project**, select an organization, name it `roadguard`, set a database password, and choose your preferred region.

### Step 2: Retrieve API URL and Anon Key
1. In your project dashboard, navigate to **Project Settings** (gear icon) -> **API**.
2. Copy the **Project URL** (format: `https://<project-ref>.supabase.co`).
3. Copy the **`anon` `public` Key** (a long JWT string).

### Step 3: Configure URL Settings (Crucial for Redirects & OAuth)
1. In the Supabase left sidebar, go to **Authentication** -> **URL Configuration**.
2. Under **Site URL**, enter:
   ```text
   http://localhost:8501
   ```
3. Under **Redirect URLs**, click **Add URL** and add:
   ```text
   http://localhost:8501
   http://localhost:8501/*
   ```
4. Click **Save**.

### Step 4: Run the Permanent SQL Schema (Database Tables & RLS Policies)
1. In your Supabase project dashboard, open the **SQL Editor** (icon `>_` in the left sidebar).
2. Click **New Query**.
3. Copy and paste the entire SQL script from [schema.sql](file:///C:/Users/santhosh/.gemini/antigravity/scratch/roadguard/schema.sql).
4. Click **Run** (or `Ctrl+Enter`).
This permanently creates:
- `public.user_roles`: Reporter, Viewer, Authority, Emergency roles.
- `public.user_profiles`: Linked to `auth.users` with karma points and badges.
- `public.road_hazard_reports`: Permanent road hazard storage with indexes.
- `public.report_photos`: Evidence photos linked to reports.
- Complete Row Level Security (RLS) policies and automatic user creation trigger.

### Step 5: Configure Google OAuth (Optional for Google Sign-In)
1. Go to [Google Cloud Console](https://console.cloud.google.com/) -> **APIs & Services** -> **Credentials**.
2. Create an **OAuth 2.0 Client ID** (Application type: *Web application*).
3. In **Authorized redirect URIs**, add your Supabase project callback URL:
   ```text
   https://<your-project-ref>.supabase.co/auth/v1/callback
   ```
4. Copy the generated **Client ID** and **Client Secret**.
5. Back in Supabase, go to **Authentication** -> **Providers** -> **Google**.
6. Toggle **Enable Google provider**, paste your **Client ID** and **Client Secret**, and click **Save**.

### Step 6: Configure Supabase Storage (For Road Problem Photos)
1. In the Supabase left sidebar, click **Storage**.
2. Click **New Bucket**, name it:
   ```text
   road-hazard-photos
   ```
3. Toggle **Public bucket** to **ON** (allows public view access for verified hazard photos on maps and dashboards).
4. Click **Save bucket**.

### Step 7: Configure Streamlit Secrets
In your project directory, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`:
```powershell
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```
Open `.streamlit/secrets.toml` and fill in your Supabase credentials:
```toml
[supabase]
url = "https://your-project-id.supabase.co"
key = "your-supabase-anon-key-here"
redirect_url = "http://localhost:8501"
storage_bucket = "road-hazard-photos"
```

---

## 🚀 How to Run the Project

### Step 1: Open Terminal in the Project Directory
```powershell
cd C:\Users\santhosh\.gemini\antigravity\scratch\roadguard
```

### Step 2: Create and Activate a Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(On macOS / Linux: `source venv/bin/activate`)*

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Launch ROADGUARD
```powershell
streamlit run app.py
```

### Step 5: Open in Browser
Streamlit will launch at:
```text
http://localhost:8501
```

---

## 🔑 Demo Mode / Role Evaluation Switcher

If you run ROADGUARD in offline mode or before configuring your Supabase project, you can log in with one click using the **Instant Role Switcher**:

| Profile | Role | Dashboard / Capabilities |
| :--- | :--- | :--- |
| `Alice Walker` (`alice`) | **📢 REPORTER** | File hazard reports, upload problem photos, pin GPS locations, track my reports |
| `Bob Miller` (`viewer_bob`) | **👀 VIEWER** | View approved reports, search locations, inspect hazard dossiers, check travel conditions |
| `Eng. Bob Henderson` (`officer_bob`) | **🏛️ AUTHORITY** | Public works triage, dispatch work orders, resolve road hazards |
| `Capt. Charlie Ruiz` (`patrol_charlie`) | **🚨 EMERGENCY** | Broadcast critical SOS alerts, highway patrol rapid response |
