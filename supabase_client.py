"""
ROADGUARD - Supabase Authentication Client
Direct GoTrue REST API integration with zero external dependencies.
Supports Email/Password Signup, Login, Google OAuth, Session Verification, and Password Recovery.
"""

import os
import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, Any, Optional, Tuple
import streamlit as st

def get_supabase_config() -> Dict[str, str]:
    """
    Retrieves Supabase configuration from Streamlit secrets or environment variables.
    Falls back gracefully if secrets are not yet defined.
    """
    url = ""
    key = ""
    redirect_url = "http://localhost:8501"

    # 1. Try Streamlit Secrets
    try:
        if hasattr(st, "secrets") and "supabase" in st.secrets:
            sec = st.secrets["supabase"]
            url = sec.get("url", "")
            key = sec.get("key", "")
            redirect_url = sec.get("redirect_url", "http://localhost:8501")
    except Exception:
        pass

    # 2. Try Environment Variables
    if not url:
        url = os.environ.get("SUPABASE_URL", "")
    if not key:
        key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_KEY", "")
    if not redirect_url or redirect_url == "http://localhost:8501":
        redirect_url = os.environ.get("SUPABASE_REDIRECT_URL", "http://localhost:8501")

    # Clean trailing slashes
    if url:
        url = url.rstrip("/")

    return {
        "url": url,
        "key": key,
        "redirect_url": redirect_url
    }

def is_supabase_configured() -> bool:
    """Checks whether valid, non-placeholder Supabase credentials exist."""
    cfg = get_supabase_config()
    url = cfg["url"].strip()
    key = cfg["key"].strip()

    if not url or not key:
        return False
    if "your-project-id" in url or "your-supabase-anon-key" in key:
        return False
    if not url.startswith("http://") and not url.startswith("https://"):
        return False
    return True

def _http_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    bearer_token: Optional[str] = None
) -> Tuple[bool, Dict[str, Any], int]:
    """
    Internal standard-library HTTP client for Supabase GoTrue Auth REST API.
    Returns (success, response_dict_or_error, http_status_code).
    """
    cfg = get_supabase_config()
    url = f"{cfg['url']}/auth/v1{endpoint}"

    headers = {
        "apikey": cfg["key"],
        "Content-Type": "application/json"
    }
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"

    body_bytes = json.dumps(data).encode("utf-8") if data is not None else None

    req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            status_code = response.getcode()
            res_body = response.read().decode("utf-8")
            if res_body:
                try:
                    res_json = json.loads(res_body)
                except Exception:
                    res_json = {"raw": res_body}
            else:
                res_json = {"status": "ok"}
            return True, res_json, status_code

    except urllib.error.HTTPError as e:
        status_code = e.code
        try:
            err_body = e.read().decode("utf-8")
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"message": f"HTTP {status_code}: {e.reason}"}
        return False, err_json, status_code

    except urllib.error.URLError as e:
        return False, {"message": f"Network error connecting to Supabase: {e.reason}"}, 0

    except Exception as e:
        return False, {"message": f"Unexpected error: {str(e)}"}, 0

def clean_error_message(err_dict: Dict[str, Any]) -> str:
    """Translates raw Supabase error messages into user-friendly explanations."""
    raw = (
        err_dict.get("error_description") or
        err_dict.get("msg") or
        err_dict.get("message") or
        err_dict.get("error") or
        str(err_dict)
    )
    raw_lower = raw.lower()

    if "invalid login credentials" in raw_lower:
        return "Incorrect email or password. Please verify your credentials or reset your password."
    elif "email not confirmed" in raw_lower:
        return "Your email address has not been confirmed yet. Please check your inbox for the Supabase verification link."
    elif "user already registered" in raw_lower or "already exists" in raw_lower:
        return "An account with this email address already exists. Please sign in instead."
    elif "password should be at least" in raw_lower:
        return "Password is too weak. Please choose a password with at least 8 characters, letters, and numbers."
    elif "rate limit" in raw_lower:
        return "Too many attempts. Please wait a few moments before trying again."
    elif "network error" in raw_lower:
        return "Unable to reach Supabase. Please check your internet connection or verify your Supabase URL."

    return raw

# --- Public Supabase Auth API ---

def supabase_sign_up(
    email: str,
    password: str,
    full_name: str,
    role: str = "citizen"
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Registers a new user via Supabase GoTrue Auth.
    Returns (success, message, user_or_session_data).
    """
    if not is_supabase_configured():
        return False, "Supabase credentials are not configured. Please see configuration guide.", None

    payload = {
        "email": email.strip().lower(),
        "password": password,
        "data": {
            "full_name": full_name.strip(),
            "role": role,
            "avatar_icon": "🏛️" if role == "authority" else ("🚨" if role == "emergency" else "🚗")
        }
    }

    success, res, status = _http_request("/signup", method="POST", data=payload)

    if success:
        # Check if email confirmation is required or immediate session was granted
        if "access_token" in res:
            return True, "Account created and logged in successfully!", res
        else:
            # Email confirmation required by Supabase project settings
            return True, "Account registered! A confirmation email has been sent. Please verify your email to log in.", res
    else:
        return False, clean_error_message(res), None

def supabase_sign_in_with_password(
    email: str,
    password: str
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Authenticates an existing user via Supabase GoTrue Auth with email and password.
    Returns (success, message, session_dict).
    """
    if not is_supabase_configured():
        return False, "Supabase credentials are not configured.", None

    payload = {
        "email": email.strip().lower(),
        "password": password
    }

    success, res, status = _http_request("/token?grant_type=password", method="POST", data=payload)

    if success and "access_token" in res:
        return True, "Login successful!", res
    else:
        return False, clean_error_message(res), None

def supabase_get_google_oauth_url(redirect_url: Optional[str] = None) -> str:
    """
    Generates the Supabase GoTrue Google OAuth authorization URL.
    """
    cfg = get_supabase_config()
    target_redirect = redirect_url or cfg["redirect_url"]
    encoded_redirect = urllib.parse.quote(target_redirect, safe="")
    return f"{cfg['url']}/auth/v1/authorize?provider=google&redirect_to={encoded_redirect}"

def supabase_get_user(access_token: str) -> Optional[Dict[str, Any]]:
    """
    Validates the bearer token against Supabase /auth/v1/user.
    Returns the user object if valid, None otherwise.
    """
    if not is_supabase_configured() or not access_token:
        return None

    success, res, status = _http_request("/user", method="GET", bearer_token=access_token)
    if success and "id" in res:
        return res
    return None

def supabase_sign_out(access_token: str) -> bool:
    """
    Invalidates the active session on Supabase servers.
    """
    if not is_supabase_configured() or not access_token:
        return True

    success, res, status = _http_request("/logout", method="POST", bearer_token=access_token)
    return success

def supabase_reset_password(email: str, redirect_url: Optional[str] = None) -> Tuple[bool, str]:
    """
    Sends a password reset recovery email via Supabase.
    """
    if not is_supabase_configured():
        return False, "Supabase credentials are not configured."

    cfg = get_supabase_config()
    payload = {
        "email": email.strip().lower(),
        "redirect_to": redirect_url or cfg["redirect_url"]
    }

    success, res, status = _http_request("/recover", method="POST", data=payload)
    if success:
        return True, "Password reset instructions sent! Please check your email."
    else:
        return False, clean_error_message(res)

# --- Supabase Storage & Database Operations ---

def _storage_request(
    endpoint: str,
    method: str = "POST",
    data_bytes: Optional[bytes] = None,
    content_type: str = "image/jpeg",
    bearer_token: Optional[str] = None
) -> Tuple[bool, Dict[str, Any], int]:
    """Internal HTTP client for Supabase Storage API."""
    cfg = get_supabase_config()
    url = f"{cfg['url']}/storage/v1{endpoint}"

    headers = {
        "apikey": cfg["key"],
        "Authorization": f"Bearer {bearer_token or cfg['key']}",
        "Content-Type": content_type
    }

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            status_code = response.getcode()
            res_body = response.read().decode("utf-8")
            try:
                res_json = json.loads(res_body) if res_body else {"status": "ok"}
            except Exception:
                res_json = {"raw": res_body}
            return True, res_json, status_code

    except urllib.error.HTTPError as e:
        status_code = e.code
        try:
            err_json = json.loads(e.read().decode("utf-8"))
        except Exception:
            err_json = {"message": f"Storage HTTP {status_code}: {e.reason}"}
        return False, err_json, status_code

    except Exception as e:
        return False, {"message": f"Storage error: {str(e)}"}, 0

def supabase_upload_photo(
    file_bytes: bytes,
    filename: str,
    content_type: str = "image/jpeg",
    bucket: str = "road-hazard-photos"
) -> Tuple[bool, str]:
    """
    Uploads a road hazard problem photo directly to Supabase Storage bucket.
    Returns (success, public_image_url_or_error_message).
    """
    if not is_supabase_configured():
        return False, "Supabase credentials are not configured."

    cfg = get_supabase_config()
    clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    target_path = f"/object/{bucket}/{clean_name}"

    # Attempt direct upload to bucket
    success, res, status = _storage_request(
        target_path,
        method="POST",
        data_bytes=file_bytes,
        content_type=content_type
    )

    if success:
        public_url = f"{cfg['url']}/storage/v1/object/public/{bucket}/{clean_name}"
        return True, public_url

    # If bucket does not exist (404), attempt auto-creating the public bucket
    if status == 404 or "not found" in str(res).lower():
        _storage_request(
            "/bucket",
            method="POST",
            data_bytes=json.dumps({"id": bucket, "name": bucket, "public": True}).encode("utf-8"),
            content_type="application/json"
        )
        # Retry upload
        retry_success, retry_res, retry_status = _storage_request(
            target_path,
            method="POST",
            data_bytes=file_bytes,
            content_type=content_type
        )
        if retry_success:
            public_url = f"{cfg['url']}/storage/v1/object/public/{bucket}/{clean_name}"
            return True, public_url

    return False, clean_error_message(res)

def supabase_insert_hazard(
    hazard_data: Dict[str, Any],
    access_token: Optional[str] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Inserts a road hazard report permanently into Supabase Database via PostgREST API.
    Saves to 'road_hazard_reports' and records photo evidence into 'report_photos'.
    """
    if not is_supabase_configured():
        return False, "Supabase is not configured.", None

    cfg = get_supabase_config()
    headers = {
        "apikey": cfg["key"],
        "Authorization": f"Bearer {access_token or cfg['key']}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    # Map payload matching schema.sql
    payload = {
        "title": hazard_data["title"],
        "problem_type": hazard_data.get("category", hazard_data.get("problem_type", "Pothole")),
        "description": hazard_data.get("description", ""),
        "severity": hazard_data.get("severity", "Medium"),
        "status": hazard_data.get("status", "Reported"),
        "latitude": float(hazard_data["latitude"]),
        "longitude": float(hazard_data["longitude"]),
        "address": hazard_data.get("address", "Pinned Location"),
        "city": hazard_data.get("city", "General Area"),
        "lane_blocked": bool(hazard_data.get("lane_blocked", False)),
        "suggested_action": hazard_data.get("suggested_action", ""),
        "reported_by_username": hazard_data.get("reported_by", "anonymous"),
        "reporter_name": hazard_data.get("reporter_name", "Citizen Reporter"),
        "photo_url": hazard_data.get("photo_url", ""),
        "upvotes": 1
    }

    # Primary target table is road_hazard_reports
    url = f"{cfg['url']}/rest/v1/road_hazard_reports"
    body_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body) if res_body else []
            record = res_json[0] if isinstance(res_json, list) and res_json else res_json

            # If photo provided, link into report_photos table permanently
            report_id = record.get("id")
            if report_id and hazard_data.get("photo_url"):
                photo_payload = {
                    "report_id": report_id,
                    "photo_url": hazard_data["photo_url"],
                    "file_name": f"report_{report_id}_photo"
                }
                photo_req = urllib.request.Request(
                    f"{cfg['url']}/rest/v1/report_photos",
                    data=json.dumps(photo_payload).encode("utf-8"),
                    headers=headers,
                    method="POST"
                )
                try:
                    urllib.request.urlopen(photo_req, timeout=6)
                except Exception:
                    pass

            return True, "Report and photo permanently stored in Supabase Database!", record

    except urllib.error.HTTPError as e:
        status_code = e.code
        # Graceful fallback to legacy table name 'hazards' if user hasn't run new schema yet
        if status_code == 404:
            try:
                legacy_req = urllib.request.Request(f"{cfg['url']}/rest/v1/hazards", data=body_bytes, headers=headers, method="POST")
                with urllib.request.urlopen(legacy_req, timeout=12) as legacy_res:
                    res_json = json.loads(legacy_res.read().decode("utf-8"))
                    record = res_json[0] if isinstance(res_json, list) and res_json else res_json
                    return True, "Report stored in Supabase Database (hazards table)!", record
            except Exception:
                pass
        try:
            err_json = json.loads(e.read().decode("utf-8"))
        except Exception:
            err_json = {"message": f"Database HTTP {status_code}: {e.reason}"}
        return False, clean_error_message(err_json), None

    except Exception as e:
        return False, f"Database error: {str(e)}", None

def supabase_fetch_reports(
    city: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    search_query: Optional[str] = None
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Retrieves all road hazard reports permanently stored in Supabase Database.
    Embeds associated photo records from 'report_photos'.
    """
    if not is_supabase_configured():
        return False, []

    cfg = get_supabase_config()
    headers = {
        "apikey": cfg["key"],
        "Authorization": f"Bearer {cfg['key']}",
        "Accept": "application/json"
    }

    query_params = ["select=*,report_photos(*)", "order=created_at.desc"]

    if city and city != "All Cities":
        query_params.append(f"city=eq.{urllib.parse.quote(city)}")
    if severity and severity != "All Severities":
        query_params.append(f"severity=eq.{urllib.parse.quote(severity)}")
    if status and status != "All Statuses":
        query_params.append(f"status=eq.{urllib.parse.quote(status)}")
    if category and category != "All Categories":
        query_params.append(f"problem_type=eq.{urllib.parse.quote(category)}")
    if search_query:
        clean_q = urllib.parse.quote(f"*{search_query.strip()}*")
        query_params.append(f"or=(title.ilike.{clean_q},description.ilike.{clean_q},address.ilike.{clean_q})")

    url = f"{cfg['url']}/rest/v1/road_hazard_reports?{'&'.join(query_params)}"
    req = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            rows = json.loads(res_body) if res_body else []
            # Normalize schema differences (problem_type <-> category)
            for r in rows:
                if "problem_type" in r and "category" not in r:
                    r["category"] = r["problem_type"]
                if "reported_by_username" in r and "reported_by" not in r:
                    r["reported_by"] = r["reported_by_username"]
            return True, rows
    except Exception:
        # Fallback to legacy 'hazards' table if new schema isn't created yet
        try:
            legacy_url = f"{cfg['url']}/rest/v1/hazards?select=*&order=created_at.desc"
            legacy_req = urllib.request.Request(legacy_url, headers=headers, method="GET")
            with urllib.request.urlopen(legacy_req, timeout=8) as leg_res:
                rows = json.loads(leg_res.read().decode("utf-8"))
                return True, rows
        except Exception:
            return False, []

def supabase_fetch_approved_reports(
    search_query: Optional[str] = None,
    city: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None
) -> Tuple[bool, List[Dict[str, Any]]]:
    """Retrieves all approved and community-verified road reports from Supabase."""
    if not is_supabase_configured():
        return False, []

    cfg = get_supabase_config()
    headers = {
        "apikey": cfg["key"],
        "Authorization": f"Bearer {cfg['key']}",
        "Accept": "application/json"
    }

    query_params = [
        "select=*,report_photos(*)",
        'status=in.("Community Verified","Work Order Dispatched","In Progress","Resolved")',
        "order=created_at.desc"
    ]
    if city and city != "All Cities":
        query_params.append(f"city=eq.{urllib.parse.quote(city)}")
    if severity and severity != "All Severities":
        query_params.append(f"severity=eq.{urllib.parse.quote(severity)}")
    if category and category != "All Categories":
        query_params.append(f"problem_type=eq.{urllib.parse.quote(category)}")
    if search_query:
        clean_q = urllib.parse.quote(f"*{search_query.strip()}*")
        query_params.append(f"or=(title.ilike.{clean_q},description.ilike.{clean_q},address.ilike.{clean_q})")

    url = f"{cfg['url']}/rest/v1/road_hazard_reports?{'&'.join(query_params)}"
    req = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            rows = json.loads(response.read().decode("utf-8"))
            for r in rows:
                if "problem_type" in r and "category" not in r:
                    r["category"] = r["problem_type"]
                if "reported_by_username" in r and "reported_by" not in r:
                    r["reported_by"] = r["reported_by_username"]
            return True, rows
    except Exception:
        return False, []

def supabase_fetch_user_reports(username: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """Retrieves all reports filed by a specific Reporter from Supabase."""
    if not is_supabase_configured() or not username:
        return False, []

    cfg = get_supabase_config()
    headers = {
        "apikey": cfg["key"],
        "Authorization": f"Bearer {cfg['key']}",
        "Accept": "application/json"
    }

    url = f"{cfg['url']}/rest/v1/road_hazard_reports?reported_by_username=eq.{urllib.parse.quote(username)}&select=*,report_photos(*)&order=created_at.desc"
    req = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            rows = json.loads(response.read().decode("utf-8"))
            for r in rows:
                if "problem_type" in r and "category" not in r:
                    r["category"] = r["problem_type"]
                if "reported_by_username" in r and "reported_by" not in r:
                    r["reported_by"] = r["reported_by_username"]
            return True, rows
    except Exception:
        return False, []

def supabase_update_report_status(
    report_id: int,
    new_status: str,
    resolution_notes: str,
    access_token: Optional[str] = None
) -> bool:
    """Updates the status and resolution notes of a road hazard report in Supabase."""
    if not is_supabase_configured():
        return False

    cfg = get_supabase_config()
    headers = {
        "apikey": cfg["key"],
        "Authorization": f"Bearer {access_token or cfg['key']}",
        "Content-Type": "application/json"
    }

    payload = {
        "status": new_status,
        "resolution_notes": resolution_notes
    }

    url = f"{cfg['url']}/rest/v1/road_hazard_reports?id=eq.{report_id}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="PATCH")

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.getcode() in [200, 204]
    except Exception:
        # Retry with legacy table
        try:
            legacy_url = f"{cfg['url']}/rest/v1/hazards?id=eq.{report_id}"
            leg_req = urllib.request.Request(legacy_url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="PATCH")
            with urllib.request.urlopen(leg_req, timeout=6) as leg_res:
                return leg_res.getcode() in [200, 204]
        except Exception:
            return False

def supabase_upsert_profile(
    user_id: str,
    email: str,
    username: str,
    full_name: str,
    role: str = "viewer",
    karma: int = 25
) -> bool:
    """Saves or updates a permanent user profile in Supabase 'user_profiles' table."""
    if not is_supabase_configured() or not user_id:
        return False

    cfg = get_supabase_config()
    headers = {
        "apikey": cfg["key"],
        "Authorization": f"Bearer {cfg['key']}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    icon = "📢" if role == "reporter" else ("🏛️" if role == "authority" else ("🚨" if role == "emergency" else "👀"))
    payload = {
        "id": user_id,
        "email": email.strip().lower(),
        "username": username.strip().lower(),
        "full_name": full_name.strip(),
        "role": role,
        "karma_points": karma,
        "avatar_icon": icon
    }

    url = f"{cfg['url']}/rest/v1/user_profiles"
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            return response.getcode() in [200, 201, 204]
    except Exception:
        return False
