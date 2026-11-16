"""
ROADGUARD - Routing Service & Corridor Hazard Intelligence Engine
Integrates:
1. OSRM (Open Source Routing Machine) Driving Routing API with graceful timeout & error recovery.
2. High-fidelity geometric fallback corridor generator for offline or firewalled environments.
3. Offline landmark geocoding & OpenStreetMap Nominatim resolver.
4. Route hazard corridor interception with distance-to-segment math.
5. Strict distinction between Verified Hazards (community/authority confirmed) and Unverified Citizen Reports.
6. Safety Protocol: Never claims a road is safe just because zero reports exist.
"""

import urllib.request
import urllib.error
import json
import math
import socket
from typing import List, Dict, Any, Tuple, Optional
from config import THEME_COLORS, SEVERITY_LEVELS, ROAD_PROBLEM_TYPES

# Built-in Metropolitan Hub Landmark Dictionary for instant offline geocoding
OFFLINE_LANDMARKS: Dict[str, Dict[str, Any]] = {
    # New York Metro
    "cadman plaza, brooklyn": {"name": "Cadman Plaza, Brooklyn", "coords": (40.6958, -73.9912), "city": "New York Metro, NY"},
    "brooklyn bridge": {"name": "Brooklyn Bridge", "coords": (40.7061, -73.9969), "city": "New York Metro, NY"},
    "times square, midtown": {"name": "Times Square, Midtown", "coords": (40.7580, -73.9855), "city": "New York Metro, NY"},
    "midtown north hub": {"name": "Midtown North Hub (59th St)", "coords": (40.7640, -73.9730), "city": "New York Metro, NY"},
    "financial district, manhattan": {"name": "Financial District (Wall St)", "coords": (40.7075, -74.0090), "city": "New York Metro, NY"},
    "flushing meadows, queens": {"name": "Flushing Meadows, Queens", "coords": (40.7498, -73.8407), "city": "New York Metro, NY"},
    "downtown ferry pier": {"name": "Downtown Manhattan Ferry Pier", "coords": (40.7020, -74.0125), "city": "New York Metro, NY"},
    "fdr drive at 34th st": {"name": "FDR Drive & 34th St", "coords": (40.7425, -73.9720), "city": "New York Metro, NY"},

    # San Francisco Bay Area
    "downtown oakland": {"name": "Downtown Oakland (City Center)", "coords": (37.8044, -122.2712), "city": "San Francisco Bay Area, CA"},
    "market & 1st st, sf": {"name": "Market & 1st St, Downtown SF", "coords": (37.7915, -122.3995), "city": "San Francisco Bay Area, CA"},
    "market st & 8th st, sf": {"name": "Market & 8th St (Civic Center)", "coords": (37.7785, -122.4150), "city": "San Francisco Bay Area, CA"},
    "bay bridge toll plaza": {"name": "Bay Bridge Toll Plaza, Oakland", "coords": (37.8220, -122.3250), "city": "San Francisco Bay Area, CA"},
    "fisherman's wharf, sf": {"name": "Fisherman's Wharf, SF", "coords": (37.8080, -122.4177), "city": "San Francisco Bay Area, CA"},

    # Austin Corridor, TX
    "round rock crossing": {"name": "Round Rock Crossing, TX", "coords": (30.4900, -97.6800), "city": "Austin Corridor, TX"},
    "congress & 6th st, austin": {"name": "Congress Ave & 6th St, Downtown Austin", "coords": (30.2680, -97.7428), "city": "Austin Corridor, TX"},
    "barton springs road": {"name": "Barton Springs Rd & Stratford Dr", "coords": (30.2635, -97.7695), "city": "Austin Corridor, TX"},
    "i-35 lower deck at 12th st": {"name": "I-35 Lower Deck & 12th St", "coords": (30.2745, -97.7335), "city": "Austin Corridor, TX"},
    "austin-bergstrom airport": {"name": "Austin-Bergstrom Int'l Airport", "coords": (30.1975, -97.6664), "city": "Austin Corridor, TX"},

    # Bangalore Highway Hub, IN
    "koramangala sony world": {"name": "Koramangala Sony World Junction", "coords": (12.9345, 77.6250), "city": "Bangalore Highway Hub, IN"},
    "electronic city phase 1": {"name": "Electronic City Phase 1", "coords": (12.8399, 77.6770), "city": "Bangalore Highway Hub, IN"},
    "central silk board junction": {"name": "Central Silk Board Junction", "coords": (12.9175, 77.6238), "city": "Bangalore Highway Hub, IN"},
    "bellandur outer ring road": {"name": "Outer Ring Road, Bellandur", "coords": (12.9298, 77.6835), "city": "Bangalore Highway Hub, IN"},

    # London Central Corridor, UK
    "hyde park corner": {"name": "Hyde Park Corner, London", "coords": (51.5033, -0.1517), "city": "London Central Corridor, UK"},
    "tower bridge approach": {"name": "Tower Bridge Approach, London", "coords": (51.5055, -0.0754), "city": "London Central Corridor, UK"},
    "kings cross st pancras": {"name": "Kings Cross St Pancras", "coords": (51.5308, -0.1238), "city": "London Central Corridor, UK"}
}

def geocode_location(query: str) -> Optional[Dict[str, Any]]:
    """
    Resolves a location string to coordinates and standardized name.
    1. Fast dictionary lookup matching known metropolitan corridors.
    2. Fallback to OpenStreetMap Nominatim geocoder API with safety timeout.
    """
    if not query or not query.strip():
        return None

    clean_query = query.strip().lower()

    # 1. Check offline dictionary (exact or substring match)
    for key, data in OFFLINE_LANDMARKS.items():
        if key in clean_query or clean_query in key:
            return {
                "name": data["name"],
                "coords": data["coords"],
                "lat": data["coords"][0],
                "lon": data["coords"][1],
                "city": data["city"],
                "source": "Local Metrology Cache"
            }

    # 2. Online Geocoding via Nominatim
    try:
        encoded = urllib.parse.quote(query.strip())
        url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&limit=1"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "RoadGuard-SmartNav/2.4 (https://github.com/roadguard; navigation@roadguard.app)",
                "Accept-Language": "en"
            }
        )
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and len(data) > 0:
                first = data[0]
                lat = float(first["lat"])
                lon = float(first["lon"])
                return {
                    "name": first.get("display_name", query)[:60],
                    "coords": (lat, lon),
                    "lat": lat,
                    "lon": lon,
                    "city": "Geocoded Location",
                    "source": "OpenStreetMap Nominatim"
                }
    except Exception:
        pass

    return None

def generate_fallback_corridor_waypoints(
    start_coords: Tuple[float, float],
    end_coords: Tuple[float, float],
    num_steps: int = 30
) -> List[Tuple[float, float]]:
    """
    Generates realistic corridor waypoints using sinusoidal roadway curvature modeling.
    Ensures uninterrupted navigation analysis even when third-party routing APIs are offline.
    """
    s_lat, s_lon = start_coords
    e_lat, e_lon = end_coords

    waypoints = []
    for i in range(num_steps + 1):
        frac = i / float(num_steps)
        # Model highway arc deflection
        curve_offset = math.sin(frac * math.pi) * 0.0035
        wp_lat = s_lat + frac * (e_lat - s_lat) + curve_offset * 0.4
        wp_lon = s_lon + frac * (e_lon - s_lon) + curve_offset
        waypoints.append((round(wp_lat, 6), round(wp_lon, 6)))

    return waypoints

def get_osrm_route(
    start_coords: Tuple[float, float],
    end_coords: Tuple[float, float],
    timeout_sec: float = 6.0
) -> Dict[str, Any]:
    """
    Queries the OSRM (Open Source Routing Machine) Public Routing API to compute
    the driving route geometry, distance, and duration.
    
    If the routing service is unavailable (network timeout, DNS failure, 429/500 HTTP, offline),
    it captures the exact error and provides a high-fidelity geometric fallback corridor so
    hazard inspection remains fully operational.
    """
    s_lat, s_lon = start_coords
    e_lat, e_lon = end_coords

    # OSRM expects coordinates in order: {longitude},{latitude}
    osrm_url = (
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{s_lon:.6f},{s_lat:.6f};{e_lon:.6f},{e_lat:.6f}"
        f"?overview=full&geometries=geojson&steps=true"
    )

    req = urllib.request.Request(
        osrm_url,
        headers={
            "User-Agent": "RoadGuard-Navigator/2.4 (roadguard-app; safe-travel@roadguard.app)",
            "Accept": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            data = json.loads(resp.read().decode("utf-8"))

            if data.get("code") == "Ok" and data.get("routes"):
                primary_route = data["routes"][0]
                geojson_coords = primary_route["geometry"]["coordinates"]

                # Convert [lon, lat] from GeoJSON into (lat, lon) for Folium & geospatial math
                route_waypoints = [(pt[1], pt[0]) for pt in geojson_coords]

                dist_m = float(primary_route.get("distance", 0.0))
                dur_s = float(primary_route.get("duration", 0.0))

                # Extract route leg summary if available
                legs = primary_route.get("legs", [])
                summary_name = legs[0].get("summary", "Primary Highway Arterial") if legs else "Direct Driving Corridor"
                steps = legs[0].get("steps", []) if legs else []

                return {
                    "success": True,
                    "service_status": "ONLINE",
                    "routing_engine": "OSRM Live Driving Service",
                    "waypoints": route_waypoints,
                    "distance_m": round(dist_m, 1),
                    "distance_km": round(dist_m / 1000.0, 2),
                    "distance_miles": round(dist_m / 1609.34, 2),
                    "duration_sec": round(dur_s, 1),
                    "duration_min": round(dur_s / 60.0, 1),
                    "duration_str": f"{int(dur_s // 3600)}h {int((dur_s % 3600) // 60)}m" if dur_s >= 3600 else f"{int(dur_s // 60)} mins",
                    "summary": summary_name or "Driving Corridor",
                    "steps": steps,
                    "is_fallback": False,
                    "error_message": None
                }

    except urllib.error.HTTPError as he:
        error_msg = f"OSRM Routing Server HTTP {he.code}: {he.reason}"
    except urllib.error.URLError as ue:
        error_msg = f"Routing service unreachable ({ue.reason})"
    except socket.timeout:
        error_msg = f"Routing service connection timed out after {timeout_sec} seconds."
    except Exception as ex:
        error_msg = f"Routing service notice: {str(ex)}"

    # Graceful fallback: construct realistic corridor polyline
    fallback_wps = generate_fallback_corridor_waypoints(start_coords, end_coords, num_steps=25)

    # Approximate direct distance via Haversine
    from utils import haversine_distance
    direct_dist_m = haversine_distance(s_lat, s_lon, e_lat, e_lon)
    # Urban road factor ~1.25-1.35x direct straight line
    est_driving_dist_m = direct_dist_m * 1.28
    # Estimate driving time at ~40 km/h average speed in metro/suburban conditions
    est_driving_dur_s = (est_driving_dist_m / 1000.0) / 40.0 * 3600.0

    return {
        "success": False,
        "service_status": "OFFLINE_FALLBACK",
        "routing_engine": "Geometric Corridor Estimator",
        "waypoints": fallback_wps,
        "distance_m": round(est_driving_dist_m, 1),
        "distance_km": round(est_driving_dist_m / 1000.0, 2),
        "distance_miles": round(est_driving_dist_m / 1609.34, 2),
        "duration_sec": round(est_driving_dur_s, 1),
        "duration_min": round(est_driving_dur_s / 60.0, 1),
        "duration_str": f"{int(est_driving_dur_s // 60)} mins (estimated)",
        "summary": "Direct Corridor Interpolation (Geometric Fallback)",
        "steps": [],
        "is_fallback": True,
        "error_message": error_msg
    }

def analyze_corridor_hazards(
    waypoints: List[Tuple[float, float]],
    hazards: List[Dict[str, Any]],
    corridor_buffer_m: float = 750.0
) -> Dict[str, Any]:
    """
    Scans road hazard reports against the calculated navigation route polyline.
    
    Key Safety & Regulatory Requirements Enforced:
    1. Distinguishes Verified Hazards (vetted by municipal authority or community)
       from Unverified Citizen Reports (logged, pending field inspection).
    2. Groups hazards by targeted problem types:
       - Potholes (tire rim, axle damage)
       - Road construction (work zones, machinery, lane narrowing)
       - Road repair (asphalt patching, flaggers)
       - Rain damage (washouts, shoulder erosion)
       - Waterlogging (standing flood pools, hydroplaning risk)
       - Accidents & blockages (stoppages, wrecks, emergency units)
    3. MANDATORY SAFETY CONSTRAINT: Does NOT claim a road is safe just because zero reports exist.
       Explicitly issues an unmonitored road advisory when report count is zero.
    """
    from utils import distance_point_to_segment

    if not waypoints or len(waypoints) < 2:
        return {
            "intercepted_hazards": [],
            "verified_hazards": [],
            "unverified_hazards": [],
            "total_count": 0,
            "verified_count": 0,
            "unverified_count": 0,
            "category_breakdown": {},
            "potholes": [],
            "construction": [],
            "repair": [],
            "rain_damage": [],
            "waterlogging": [],
            "accidents": [],
            "risk_score": 0,
            "risk_grade": "Unmonitored / Zero Reports Logged",
            "risk_color": "#2563EB",
            "summary": "Zero active hazard reports logged along this route corridor.",
            "safety_advisory": (
                "⚠️ Safety Notice: Zero active reports logged along this corridor. "
                "IMPORTANT: The absence of reports does NOT guarantee that the road is safe or clear. "
                "Municipal road conditions degrade continuously, and unmonitored potholes, waterlogging, or debris may exist. "
                "Always drive attentively, maintain safe following distances, and obey speed limits."
            ),
            "is_safe_claim": False
        }

    intercepted = []
    verified_list = []
    unverified_list = []

    # Categorical lists
    potholes = []
    construction = []
    repair = []
    rain_damage = []
    waterlogging = []
    accidents = []
    other_hazards = []

    total_weight = 0

    for h in hazards:
        # Ignore completed/resolved fixes
        if h.get("status") == "Resolved":
            continue

        h_lat = float(h.get("latitude", 0.0))
        h_lon = float(h.get("longitude", 0.0))

        # Measure shortest distance from this hazard to any segment of the route polyline
        min_dist = float("inf")
        for j in range(len(waypoints) - 1):
            d = distance_point_to_segment(
                h_lat, h_lon,
                waypoints[j][0], waypoints[j][1],
                waypoints[j+1][0], waypoints[j+1][1]
            )
            if d < min_dist:
                min_dist = d

        if min_dist <= corridor_buffer_m:
            item = dict(h)
            item["distance_to_route_m"] = round(min_dist, 1)

            # Check verification status
            status = item.get("status", "Reported")
            is_verified = status in ["Community Verified", "Work Order Dispatched", "In Progress"]
            item["is_verified"] = is_verified
            item["verification_badge"] = "🛡️ VERIFIED HAZARD" if is_verified else "📝 UNVERIFIED CITIZEN REPORT"

            # Assign weight for risk calculation
            sev = item.get("severity", "Medium")
            w = SEVERITY_LEVELS.get(sev, {}).get("weight", 2)
            if item.get("lane_blocked"):
                w += 2
            total_weight += w

            intercepted.append(item)

            if is_verified:
                verified_list.append(item)
            else:
                unverified_list.append(item)

            # Group by road problem type
            cat = item.get("category", "").lower()
            title = item.get("title", "").lower()
            desc = item.get("description", "").lower()

            if "pothole" in cat or "pothole" in title or "pothole" in desc or "crater" in desc:
                potholes.append(item)
            elif "construction" in cat or "work zone" in cat or "construction" in desc:
                construction.append(item)
            elif "repair" in cat or "patching" in desc or "resurfacing" in desc:
                repair.append(item)
            elif "rain" in cat or "washout" in desc or "erosion" in desc:
                rain_damage.append(item)
            elif "waterlog" in cat or "flood" in cat or "water" in desc or "submerged" in desc:
                waterlogging.append(item)
            elif "accident" in cat or "blockage" in cat or "crash" in desc or "collision" in desc:
                accidents.append(item)
            else:
                other_hazards.append(item)

    # Sort each list by closest distance to corridor
    intercepted.sort(key=lambda x: x["distance_to_route_m"])
    verified_list.sort(key=lambda x: x["distance_to_route_m"])
    unverified_list.sort(key=lambda x: x["distance_to_route_m"])

    # Aggregate counts
    total_count = len(intercepted)
    verified_count = len(verified_list)
    unverified_count = len(unverified_list)

    # Strict Safety Compliance: When hazard count is 0, DO NOT claim safe!
    if total_count == 0:
        risk_score = 0
        risk_grade = "Unmonitored / Zero Reports Logged"
        risk_color = "#2563EB"  # Deep Royal Blue (Information/Neutral, NOT Green "All Clear")
        summary = "No active citizen or municipal hazard reports logged along this corridor."
        safety_advisory = (
            "⚠️ Safety Notice: Zero active reports logged along this route corridor.\n\n"
            "REMINDER: The absence of reports does NOT guarantee that the road is safe or hazard-free. "
            "Municipal road surfaces deteriorate rapidly due to weather and traffic loads. Unreported potholes, water pools, or surface cracks may be present. "
            "Maintain standard driving vigilance, adhere to posted speed limits, and keep safe braking distances."
        )
        is_safe_claim = False
    else:
        # Calculate risk score (0-100)
        risk_score = min(100, int(total_weight * 11))

        if risk_score <= 25:
            risk_grade = "Low Risk (Minor Obstructions)"
            risk_color = THEME_COLORS["severity_medium"]
            summary = f"{total_count} hazard(s) reported along corridor ({verified_count} verified). Minor delays possible."
        elif risk_score <= 55:
            risk_grade = "Moderate Caution (Active Hazards)"
            risk_color = THEME_COLORS["severity_high"]
            summary = f"{total_count} hazard(s) detected ({verified_count} verified, {unverified_count} unverified). Drive with vigilance."
        elif risk_score <= 80:
            risk_grade = "High Danger (Lane Obstructions)"
            risk_color = THEME_COLORS["severity_critical"]
            summary = f"Significant road hazards or lane blockages along corridor. Consider alternate detour."
        else:
            risk_grade = "Severe Emergency (Critical Hazard)"
            risk_color = "#991B1B"
            summary = f"Critical road blockages or hazardous conditions detected! Detour strongly recommended."

        safety_advisory = (
            f"⚠️ Caution: {total_count} road hazard report(s) identified within {int(corridor_buffer_m)}m of your travel route. "
            f"Includes {verified_count} verified hazard(s) and {unverified_count} pending citizen report(s). "
            f"Reduce speed near reported coordinates and prepare for lane shifts."
        )
        is_safe_claim = False

    return {
        "intercepted_hazards": intercepted,
        "verified_hazards": verified_list,
        "unverified_hazards": unverified_list,
        "total_count": total_count,
        "verified_count": verified_count,
        "unverified_count": unverified_count,
        "category_breakdown": {
            "Potholes": len(potholes),
            "Road construction": len(construction),
            "Road repair": len(repair),
            "Rain damage": len(rain_damage),
            "Waterlogging": len(waterlogging),
            "Accident or road blockage": len(accidents),
            "Other Hazards": len(other_hazards)
        },
        "potholes": potholes,
        "construction": construction,
        "repair": repair,
        "rain_damage": rain_damage,
        "waterlogging": waterlogging,
        "accidents": accidents,
        "other_hazards": other_hazards,
        "risk_score": risk_score,
        "risk_grade": risk_grade,
        "risk_color": risk_color,
        "summary": summary,
        "safety_advisory": safety_advisory,
        "is_safe_claim": is_safe_claim
    }
