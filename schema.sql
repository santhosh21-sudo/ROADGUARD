-- =====================================================================
-- ROADGUARD - Permanent Supabase PostgreSQL Database Schema
-- Smart Road Hazard Reporting & Navigation System
-- Includes: User Profiles, User Roles, Road Hazard Reports, Report Photos
-- Complete Row Level Security (RLS) Policies & Automatic Profile Trigger
-- =====================================================================

-- Enable necessary PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------------------
-- 1. USER ROLES TABLE
-- Defines system roles: Reporter, Viewer, Authority, Emergency
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.user_roles (
    role_key TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Seed default user roles
INSERT INTO public.user_roles (role_key, name, description)
VALUES 
    ('reporter', 'Road Hazard Reporter', 'Can submit road hazard reports, upload problem photos, and track submitted reports'),
    ('viewer', 'Pre-Travel Hazard Viewer', 'Can view approved road reports, search locations, inspect hazard dossiers, and check pre-travel route safety'),
    ('authority', 'Public Works Authority', 'Can manage work orders, dispatch repair squads, and resolve road hazards'),
    ('emergency', 'Highway Emergency Services', 'Can broadcast critical emergency SOS alerts and monitor collision sectors')
ON CONFLICT (role_key) DO UPDATE 
SET name = EXCLUDED.name, description = EXCLUDED.description;

-- ---------------------------------------------------------------------
-- 2. USER PROFILES TABLE
-- Connected to Supabase Auth (auth.users)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'viewer' REFERENCES public.user_roles(role_key),
    karma_points INTEGER DEFAULT 25,
    avatar_icon TEXT DEFAULT '🚗',
    badge TEXT DEFAULT '🌱 Novice Scout',
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Index for profile queries
CREATE INDEX IF NOT EXISTS idx_user_profiles_username ON public.user_profiles(username);
CREATE INDEX IF NOT EXISTS idx_user_profiles_role ON public.user_profiles(role);

-- ---------------------------------------------------------------------
-- 3. ROAD HAZARD REPORTS TABLE
-- Permanent storage for road hazard reports
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.road_hazard_reports (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    problem_type TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
    status TEXT NOT NULL DEFAULT 'Reported' CHECK (status IN ('Reported', 'Community Verified', 'Work Order Dispatched', 'In Progress', 'Resolved')),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    address TEXT NOT NULL,
    city TEXT DEFAULT 'General Area',
    lane_blocked BOOLEAN DEFAULT FALSE,
    suggested_action TEXT,
    work_order_id TEXT,
    resolution_notes TEXT,
    reported_by_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    reported_by_username TEXT NOT NULL,
    reporter_name TEXT NOT NULL,
    upvotes INTEGER DEFAULT 1,
    downvotes INTEGER DEFAULT 0,
    photo_url TEXT,
    incident_datetime TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Indexes for fast geospatial and filter lookups
CREATE INDEX IF NOT EXISTS idx_road_reports_status ON public.road_hazard_reports(status);
CREATE INDEX IF NOT EXISTS idx_road_reports_severity ON public.road_hazard_reports(severity);
CREATE INDEX IF NOT EXISTS idx_road_reports_coords ON public.road_hazard_reports(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_road_reports_city ON public.road_hazard_reports(city);
CREATE INDEX IF NOT EXISTS idx_road_reports_reporter ON public.road_hazard_reports(reported_by_username);

-- ---------------------------------------------------------------------
-- 4. REPORT PHOTOS TABLE
-- Tracks uploaded evidence photos linked to Supabase Storage
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.report_photos (
    id BIGSERIAL PRIMARY KEY,
    report_id BIGINT REFERENCES public.road_hazard_reports(id) ON DELETE CASCADE,
    photo_url TEXT NOT NULL,
    storage_path TEXT,
    file_name TEXT,
    content_type TEXT DEFAULT 'image/jpeg',
    uploaded_by_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

CREATE INDEX IF NOT EXISTS idx_report_photos_report ON public.report_photos(report_id);

-- ---------------------------------------------------------------------
-- 5. AUTOMATIC PROFILE CREATION TRIGGER
-- When a user signs up via Supabase Auth, automatically creates a user_profiles row
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    raw_role TEXT;
    raw_name TEXT;
    raw_uname TEXT;
BEGIN
    raw_role := COALESCE(new.raw_user_meta_data->>'role', 'viewer');
    raw_name := COALESCE(new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'name', split_part(new.email, '@', 1));
    raw_uname := split_part(new.email, '@', 1);

    -- Ensure role exists in user_roles
    IF NOT EXISTS (SELECT 1 FROM public.user_roles WHERE role_key = raw_role) THEN
        raw_role := 'viewer';
    END IF;

    INSERT INTO public.user_profiles (id, email, username, full_name, role, avatar_icon)
    VALUES (
        new.id,
        new.email,
        raw_uname,
        raw_name,
        raw_role,
        CASE WHEN raw_role = 'reporter' THEN '📢' WHEN raw_role = 'authority' THEN '🏛️' WHEN raw_role = 'emergency' THEN '🚨' ELSE '👀' END
    )
    ON CONFLICT (id) DO UPDATE 
    SET full_name = EXCLUDED.full_name, role = EXCLUDED.role;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop existing trigger if present, then recreate
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ---------------------------------------------------------------------
-- 6. ROW LEVEL SECURITY (RLS) POLICIES
-- Secure database access policies
-- ---------------------------------------------------------------------

-- Enable RLS on all public tables
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.road_hazard_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.report_photos ENABLE ROW LEVEL SECURITY;

-- Clean existing policies if re-running
DROP POLICY IF EXISTS "Public read on user_roles" ON public.user_roles;
DROP POLICY IF EXISTS "Public read on user_profiles" ON public.user_profiles;
DROP POLICY IF EXISTS "Users can insert own profile" ON public.user_profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.user_profiles;

DROP POLICY IF EXISTS "Allow public read on road reports" ON public.road_hazard_reports;
DROP POLICY IF EXISTS "Allow authenticated to insert reports" ON public.road_hazard_reports;
DROP POLICY IF EXISTS "Allow update on own reports or by authority" ON public.road_hazard_reports;

DROP POLICY IF EXISTS "Allow public read on report photos" ON public.report_photos;
DROP POLICY IF EXISTS "Allow authenticated to insert report photos" ON public.report_photos;

-- A) user_roles Policies:
CREATE POLICY "Public read on user_roles"
    ON public.user_roles FOR SELECT
    TO anon, authenticated
    USING (true);

-- B) user_profiles Policies:
CREATE POLICY "Public read on user_profiles"
    ON public.user_profiles FOR SELECT
    TO anon, authenticated
    USING (true);

CREATE POLICY "Users can insert own profile"
    ON public.user_profiles FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.user_profiles FOR UPDATE
    TO authenticated
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- C) road_hazard_reports Policies:
-- Anyone (anons & authenticated) can view all active and approved road hazard reports
CREATE POLICY "Allow public read on road reports"
    ON public.road_hazard_reports FOR SELECT
    TO anon, authenticated
    USING (true);

-- Authenticated users (reporters/authorities) can submit road hazard reports
CREATE POLICY "Allow authenticated to insert reports"
    ON public.road_hazard_reports FOR INSERT
    TO authenticated
    WITH CHECK (true);

-- Reporters can update their own reports; authorities/emergency units can update statuses & work orders
CREATE POLICY "Allow update on own reports or by authority"
    ON public.road_hazard_reports FOR UPDATE
    TO authenticated
    USING (
        auth.uid() = reported_by_id
        OR EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE user_profiles.id = auth.uid() 
            AND user_profiles.role IN ('authority', 'emergency')
        )
    );

-- D) report_photos Policies:
CREATE POLICY "Allow public read on report photos"
    ON public.report_photos FOR SELECT
    TO anon, authenticated
    USING (true);

CREATE POLICY "Allow authenticated to insert report photos"
    ON public.report_photos FOR INSERT
    TO authenticated
    WITH CHECK (true);

-- ---------------------------------------------------------------------
-- 7. INITIAL SAMPLE HAZARDS (For immediate live display)
-- ---------------------------------------------------------------------
INSERT INTO public.road_hazard_reports (
    title, problem_type, description, severity, status,
    latitude, longitude, address, city, lane_blocked, suggested_action,
    reported_by_username, reporter_name, upvotes, photo_url
)
VALUES
    (
        'Massive Crater Pothole on FDR Drive Northbound',
        'Pothole',
        'Deep 7-inch asphalt fracture in middle lane after heavy rain. Causing severe tire rim damage.',
        'High',
        'Community Verified',
        40.7308, -73.9742,
        'FDR Drive & E 20th St, New York, NY',
        'New York Metro, NY',
        true,
        'Reduce speed to 25mph, shift to far left lane',
        'alice', 'Alice Walker (Reporter)', 18,
        'https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?w=600&auto=format&fit=crop&q=80'
    ),
    (
        '3-Vehicle Collision on Brooklyn Bridge Manhattan-bound',
        'Accident or road blockage',
        'Multi-vehicle rear-end collision blocking two lanes. Police cruisers and tow truck on scene.',
        'Critical',
        'In Progress',
        40.7061, -73.9969,
        'Brooklyn Bridge Center Span, New York, NY',
        'New York Metro, NY',
        true,
        'Detour via Manhattan Bridge or Hugh L. Carey Tunnel',
        'patrol_charlie', 'Capt. Charlie Ruiz (State Patrol)', 42,
        'https://images.unsplash.com/photo-1598970434795-0c54fe7c0648?w=600&auto=format&fit=crop&q=80'
    ),
    (
        'Submerged Highway Underpass near Long Island Expressway',
        'Waterlogging',
        'Clogged storm drains causing 14 inches of standing water across Queens Blvd interchange.',
        'High',
        'Work Order Dispatched',
        40.7282, -73.8631,
        'Queens Blvd & LIE Underpass, Queens, NY',
        'New York Metro, NY',
        true,
        'Do not attempt to cross underpass; use side service road',
        'david', 'David Miller', 24,
        'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=600&auto=format&fit=crop&q=80'
    ),
    (
        'Heavy Road Construction Zone on CA-1 Pacific Coast Highway',
        'Road construction',
        'Active roadwork, barricades, lane narrowing, heavy machinery operating near roadway.',
        'Medium',
        'In Progress',
        37.7550, -122.5080,
        'CA-1 & Lincoln Way, San Francisco, CA',
        'San Francisco Bay Area, CA',
        false,
        'Observe 25mph construction zone speed limit',
        'alice', 'Alice Walker (Reporter)', 15,
        'https://images.unsplash.com/photo-1541888946425-d0fbb18086f6?w=600&auto=format&fit=crop&q=80'
    ),
    (
        'Flash Flood Rain Damage across Barton Springs Road',
        'Rain damage',
        'Mud washout and creek overflow across low-water road crossing.',
        'High',
        'Community Verified',
        30.2635, -97.7695,
        'Barton Springs Rd & Stratford Dr, Austin, TX',
        'Austin Corridor, TX',
        true,
        'Turn Around, Don''t Drown; gates lowered',
        'alice', 'Alice Walker (Reporter)', 28,
        'https://images.unsplash.com/photo-1519692933481-e162a57d6721?w=600&auto=format&fit=crop&q=80'
    )
ON CONFLICT DO NOTHING;
