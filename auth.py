"""
ROADGUARD - Supabase Authentication & Session Management System
Provides secure Email/Password Sign Up, Sign In, Google OAuth, Session Persistence
across browser reloads, Protected Application Page Gates, and Friendly Error Validation.
"""

import streamlit as st
import secrets
import re
from typing import Optional, Dict, Any, Tuple
from config import USER_ROLES, THEME_COLORS
from database import (
    get_user_by_username, get_user_by_email, sync_supabase_user,
    save_session, get_session, delete_session, create_user
)
from supabase_client import (
    is_supabase_configured, supabase_sign_up, supabase_sign_in_with_password,
    supabase_get_google_oauth_url, supabase_get_user, supabase_sign_out,
    supabase_reset_password, get_supabase_config
)

# --- Validation Utilities ---

def validate_email_format(email: str) -> Tuple[bool, str]:
    """Ensures input matches valid email address formatting."""
    email_clean = email.strip()
    if not email_clean:
        return False, "Email address is required."
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email_clean):
        return False, "Please enter a valid email address (e.g., motorist@example.com)."
    return True, "Valid email format."

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Enforces secure password criteria:
    - Minimum 8 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one numerical digit (0-9)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must include at least one uppercase letter (A-Z)."
    if not any(c.islower() for c in password):
        return False, "Password must include at least one lowercase letter (a-z)."
    if not any(c.isdigit() for c in password):
        return False, "Password must include at least one numerical digit (0-9)."
    return True, "Strong password."

# --- Session Initialization & Cross-Refresh Persistence ---

def init_auth():
    """
    Initializes session state and restores active sessions across browser refreshes (F5).
    Evaluates URL query parameters for session tokens or OAuth callbacks.
    """
    # 1. Check if user is already authenticated in this memory cycle
    if st.session_state.get("authenticated") and st.session_state.get("user"):
        return

    # 2. Check for Google OAuth callback via PKCE code (?code=...)
    if "code" in st.query_params:
        auth_code = st.query_params.get("code")
        # Clean query param
        del st.query_params["code"]
        handle_oauth_code_callback(auth_code)
        return

    # 3. Check for Google OAuth callback via forwarded hash token (?oauth_token=...)
    if "oauth_token" in st.query_params:
        oauth_token = st.query_params.get("oauth_token")
        oauth_refresh = st.query_params.get("oauth_refresh", "")
        # Clean query parameters
        del st.query_params["oauth_token"]
        if "oauth_refresh" in st.query_params:
            del st.query_params["oauth_refresh"]
        handle_oauth_token_callback(oauth_token, oauth_refresh)
        return

    # 4. Check for persistent session token in URL query parameters (?session=...)
    persisted_token = st.query_params.get("session")
    if persisted_token:
        cached = get_session(persisted_token)
        if cached:
            # Refresh user from database
            user = get_user_by_email(cached["email"]) or get_user_by_username(cached["email"].split("@")[0])
            if user:
                st.session_state.user = user
                st.session_state.authenticated = True
                st.session_state.session_token = persisted_token
                st.session_state.access_token = cached.get("access_token", "")
                return
            else:
                delete_session(persisted_token)
                del st.query_params["session"]
        else:
            # Invalid or expired token
            if "session" in st.query_params:
                del st.query_params["session"]

    # 5. Default unauthenticated state
    if "user" not in st.session_state:
        st.session_state.user = None
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

def handle_oauth_token_callback(access_token: str, refresh_token: str):
    """Processes Google OAuth token returned from Supabase."""
    supabase_user = supabase_get_user(access_token)
    if supabase_user:
        local_user = sync_supabase_user(supabase_user)
        session_token = secrets.token_urlsafe(32)
        save_session(session_token, local_user, access_token, refresh_token)
        st.session_state.user = local_user
        st.session_state.authenticated = True
        st.session_state.session_token = session_token
        st.session_state.access_token = access_token
        st.query_params["session"] = session_token
        st.toast("🎉 Successfully authenticated with Google!", icon="✅")
        st.rerun()

def handle_oauth_code_callback(auth_code: str):
    """Processes Google OAuth PKCE auth code."""
    # Attempt to exchange code with Supabase if gotrue PKCE is used
    from supabase_client import _http_request
    success, res, status = _http_request("/token?grant_type=pkce", method="POST", data={"auth_code": auth_code})
    if success and "access_token" in res:
        token = res["access_token"]
        refresh = res.get("refresh_token", "")
        handle_oauth_token_callback(token, refresh)
    else:
        st.error("Google authentication code expired or invalid. Please try signing in again.")

def get_current_user() -> Optional[Dict[str, Any]]:
    """Returns the currently authenticated user dictionary."""
    init_auth()
    if st.session_state.get("user"):
        # Refresh latest karma & badge stats
        email = st.session_state.user.get("email")
        if email:
            refreshed = get_user_by_email(email)
            if refreshed:
                st.session_state.user = refreshed
    return st.session_state.get("user")

def is_authenticated() -> bool:
    """Verifies whether the current user is securely logged in."""
    init_auth()
    return st.session_state.get("authenticated", False)

def has_role(required_role: str) -> bool:
    """Evaluates role-based permissions for Reporter, Viewer, and Authority."""
    user = get_current_user()
    if not user:
        return False
    user_role = user.get("role", "viewer")

    # Viewer permissions: All authenticated users can view
    if required_role == "viewer":
        return True

    # Reporter permissions: reporters, authorities, and emergency can report
    if required_role in ["reporter", "citizen"]:
        return user_role in ["reporter", "citizen", "authority", "emergency"]

    # Authority & Emergency
    if user_role == "emergency" and required_role in ["authority", "reporter"]:
        return True
    return user_role == required_role

def is_reporter() -> bool:
    """Checks whether active user is a Reporter with submission rights."""
    return has_role("reporter")

def is_viewer() -> bool:
    """Checks whether active user has the Viewer role."""
    user = get_current_user()
    return bool(user and user.get("role") == "viewer")

def can_submit_reports() -> bool:
    """RBAC check: Only Reporters and Authorities can submit road hazard reports."""
    user = get_current_user()
    if not user:
        return False
    return user.get("role") in ["reporter", "citizen", "authority", "emergency"]

def logout_user():
    """
    Terminates the active session:
    1. Notifies Supabase to invalidate tokens.
    2. Deletes session token from local database.
    3. Clears Streamlit session state and query params.
    """
    token = st.session_state.get("session_token")
    access_tok = st.session_state.get("access_token", "")

    if access_tok:
        supabase_sign_out(access_tok)
    if token:
        delete_session(token)

    st.session_state.user = None
    st.session_state.authenticated = False
    st.session_state.session_token = None
    st.session_state.access_token = None

    if "session" in st.query_params:
        del st.query_params["session"]

    st.toast("You have been securely signed out.", icon="👋")
    st.rerun()

def switch_demo_user(username: str):
    """Demo switcher for evaluating municipal and emergency role perspectives."""
    user = get_user_by_username(username)
    if user:
        session_token = secrets.token_urlsafe(32)
        save_session(session_token, user, "demo_access_token")
        st.session_state.user = user
        st.session_state.authenticated = True
        st.session_state.session_token = session_token
        st.query_params["session"] = session_token
        st.toast(f"Switched role to {user['full_name']} ({user['role'].upper()})", icon="🔄")
        st.rerun()

# --- Protected Page Gate & Authentication Portal ---

def render_auth_gateway():
    """
    Renders the modern, full-page Authentication Gateway when the user is not authenticated.
    Blocks access to protected pages until valid login occurs.
    """
    # Embedded JS helper: Extracts Google OAuth hash tokens (#access_token=...) and redirects to query params
    st.components.v1.html(
        """
        <script>
        try {
            if (window.location.hash && window.location.hash.includes('access_token')) {
                const hashParams = new URLSearchParams(window.location.hash.substring(1));
                const token = hashParams.get('access_token');
                const refresh = hashParams.get('refresh_token') || '';
                if (token) {
                    window.location.href = window.location.pathname + '?oauth_token=' + encodeURIComponent(token) + '&oauth_refresh=' + encodeURIComponent(refresh);
                }
            }
        } catch(e) {}
        </script>
        """,
        height=0
    )

    supabase_ready = is_supabase_configured()

    col_center = st.columns([1, 2, 1])[1]

    with col_center:
        st.markdown(
            f"""
            <div class="rg-card" style="text-align:center; padding: 28px 30px; border-top: 5px solid {THEME_COLORS['primary_blue']};">
                <div style="font-size: 42px; margin-bottom: 8px;">🛡️</div>
                <h2 style="margin: 0; color: #1E3A8A; font-weight: 800; font-size: 26px;">Welcome to ROADGUARD</h2>
                <p style="margin: 6px 0 0 0; color: #64748B; font-size: 14px;">
                    Smart Road Hazard Reporting & Navigation System
                </p>
                <div style="margin-top: 14px; display: inline-flex; align-items: center; gap: 6px; background: #EFF6FF; border: 1px solid #BFDBFE; padding: 4px 12px; border-radius: 9999px; font-size: 12px; color: #1D4ED8; font-weight: 600;">
                    🔒 Protected Platform • Supabase Authentication
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if not supabase_ready:
            st.warning(
                "⚠️ **Supabase Credentials Needed for Live Auth**\n\n"
                "To enable live Supabase Email Sign-up, Sign-in, and Google OAuth, add your `url` and `key` to `.streamlit/secrets.toml`. "
                "See the configuration guide below or test with pre-seeded demo accounts."
            )

        # Tab Navigation
        tab_login, tab_signup, tab_google, tab_forgot = st.tabs([
            "🔑 Sign In",
            "📝 Create Account",
            "🌐 Google Sign In",
            "❓ Forgot Password"
        ])

        # --- TAB 1: Email & Password Sign In ---
        with tab_login:
            st.markdown("##### Sign In with Email & Password")

            # College Presentation / Evaluator Quick Login Strip
            st.markdown(
                """
                <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:8px; padding:10px 14px; margin-bottom:14px;">
                    <div style="font-weight:700; color:#1E40AF; font-size:12px; margin-bottom:6px;">
                        ⚡ EVALUATOR QUICK SIGN-IN (FOR PRESENTATIONS):
                    </div>
                    <div style="font-size:11px; color:#475569; margin-bottom:8px;">
                        Skip credential typing during testing or evaluation:
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            col_q1, col_q2 = st.columns(2)
            with col_q1:
                if st.button("📢 Demo Reporter (Alice)", use_container_width=True, key="quick_alice_top"):
                    switch_demo_user("alice")
                    st.rerun()
            with col_q2:
                if st.button("👀 Demo Viewer (Bob)", use_container_width=True, key="quick_viewer_top"):
                    switch_demo_user("viewer_bob")
                    st.rerun()

            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

            with st.form("signin_form", clear_on_submit=False):
                email = st.text_input("Email Address", placeholder="driver@example.com", key="login_email")
                password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
                remember_me = st.checkbox("Keep me logged in on this browser (7 days)", value=True)

                submit_login = st.form_submit_button("Sign In to ROADGUARD", use_container_width=True, type="primary")

                if submit_login:
                    valid_email, email_msg = validate_email_format(email)
                    if not valid_email:
                        st.error(email_msg)
                    elif not password:
                        st.error("Please enter your account password.")
                    else:
                        if supabase_ready:
                            with st.spinner("Authenticating with Supabase..."):
                                success, msg, session_data = supabase_sign_in_with_password(email, password)
                                if success and session_data:
                                    token = session_data["access_token"]
                                    refresh = session_data.get("refresh_token", "")
                                    user_obj = session_data.get("user", {})
                                    local_user = sync_supabase_user(user_obj)

                                    session_token = secrets.token_urlsafe(32)
                                    expiry_sec = 604800 if remember_me else 86400
                                    save_session(session_token, local_user, token, refresh, expires_in_sec=expiry_sec)

                                    st.session_state.user = local_user
                                    st.session_state.authenticated = True
                                    st.session_state.session_token = session_token
                                    st.session_state.access_token = token
                                    st.query_params["session"] = session_token

                                    st.success(f"Welcome back, {local_user['full_name']}!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {msg}")
                        else:
                            # Demo mode check
                            user = get_user_by_email(email) or get_user_by_username(email.split("@")[0])
                            if user and password == "password123":
                                session_token = secrets.token_urlsafe(32)
                                save_session(session_token, user, "demo_token")
                                st.session_state.user = user
                                st.session_state.authenticated = True
                                st.session_state.session_token = session_token
                                st.query_params["session"] = session_token
                                st.success(f"Welcome back, {user['full_name']}! (Demo Mode)")
                                st.rerun()
                            else:
                                st.error("Invalid credentials. (Hint: In demo mode, use email 'alice@roadguard.org' and password 'password123')")

        # --- TAB 2: Email & Password Sign Up ---
        with tab_signup:
            st.markdown("##### Register a New Account")
            with st.form("signup_form", clear_on_submit=False):
                new_name = st.text_input("Full Name", placeholder="e.g. Jane Smith", key="reg_name")
                new_email = st.text_input("Email Address", placeholder="jane@example.com", key="reg_email")

                st.markdown("**Choose Your Account Role:**")
                new_role = st.radio(
                    "Select Account Role",
                    ["reporter", "viewer"],
                    format_func=lambda r: f"{USER_ROLES[r]['icon']} {USER_ROLES[r]['label']} — {USER_ROLES[r]['tagline']}",
                    help="Reporters can submit hazards and upload photos. Viewers can search locations and check pre-travel route safety."
                )

                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    new_password = st.text_input("Password", type="password", placeholder="Min 8 chars, A-Z, 0-9", key="reg_pass")
                with col_p2:
                    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Repeat password", key="reg_confirm")

                st.caption("🔒 Passwords are encrypted and verified directly via Supabase GoTrue Auth.")
                submit_signup = st.form_submit_button("Create My Account", use_container_width=True)

                if submit_signup:
                    valid_email, email_msg = validate_email_format(new_email)
                    valid_pass, pass_msg = validate_password_strength(new_password)

                    if not new_name.strip():
                        st.error("Please enter your full name.")
                    elif not valid_email:
                        st.error(email_msg)
                    elif not valid_pass:
                        st.error(f"Weak Password: {pass_msg}")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match. Please re-enter identical passwords.")
                    else:
                        if supabase_ready:
                            with st.spinner("Creating account with Supabase..."):
                                success, msg, res_data = supabase_sign_up(new_email, new_password, new_name, new_role)
                                if success:
                                    if res_data and "access_token" in res_data:
                                        # Auto-logged in
                                        local_user = sync_supabase_user(res_data.get("user", {}), role_override=new_role)
                                        session_token = secrets.token_urlsafe(32)
                                        save_session(session_token, local_user, res_data["access_token"], res_data.get("refresh_token"))
                                        st.session_state.user = local_user
                                        st.session_state.authenticated = True
                                        st.session_state.session_token = session_token
                                        st.query_params["session"] = session_token
                                        st.success(f"🎉 Account registered successfully! Welcome {local_user['full_name']}.")
                                        st.rerun()
                                    else:
                                        st.success(f"📬 {msg}")
                                        st.info("Once confirmed, return to the **Sign In** tab to enter ROADGUARD.")
                                else:
                                    st.error(f"❌ {msg}")
                        else:
                            # Local registration fallback for testing
                            ok, msg = create_user(new_email.split("@")[0], new_email, new_password, new_name, new_role)
                            if ok:
                                st.success("Account created in demo mode! You can now log in.")
                            else:
                                st.error(msg)

        # --- TAB 3: Google Login via Supabase OAuth ---
        with tab_google:
            st.markdown("##### Single Sign-On with Google")
            st.caption("Authenticate quickly using your Google Account through Supabase OAuth.")

            if supabase_ready:
                cfg = get_supabase_config()
                google_oauth_url = supabase_get_google_oauth_url()

                st.markdown(
                    f"""
                    <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; padding:18px; text-align:center; margin: 12px 0;">
                        <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" width="36" style="margin-bottom:8px;" alt="Google"/>
                        <div style="font-weight:700; color:#1E3A8A; font-size:16px;">Supabase Google OAuth</div>
                        <p style="font-size:13px; color:#64748B; margin:4px 0 14px 0;">
                            Secure single-click authentication. Redirects to Google consent and returns to ROADGUARD.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.link_button(
                    "🌐 Continue with Google",
                    google_oauth_url,
                    use_container_width=True
                )

                st.caption(f"Redirect URI configured: `{cfg['redirect_url']}`")
            else:
                st.info(
                    "🌐 **Google OAuth requires Supabase configuration.**\n\n"
                    "1. Set up your Supabase project URL and Key in `.streamlit/secrets.toml`.\n"
                    "2. Enable Google Provider in your Supabase Dashboard under Authentication -> Providers.\n"
                    "See the expander below for exact step-by-step instructions."
                )

        # --- TAB 4: Password Recovery ---
        with tab_forgot:
            st.markdown("##### Reset Account Password")
            st.caption("Receive a password reset link to your registered email.")
            with st.form("recovery_form"):
                rec_email = st.text_input("Registered Email Address", placeholder="user@example.com")
                submit_rec = st.form_submit_button("Send Recovery Instructions", use_container_width=True)
                if submit_rec:
                    valid_email, email_msg = validate_email_format(rec_email)
                    if not valid_email:
                        st.error(email_msg)
                    else:
                        if supabase_ready:
                            with st.spinner("Contacting Supabase..."):
                                ok, msg = supabase_reset_password(rec_email)
                                if ok:
                                    st.success(f"📬 {msg}")
                                else:
                                    st.error(f"❌ {msg}")
                        else:
                            st.info("In demo mode: Passwords for demo accounts can be reset by switching roles in the demo panel below.")

        # --- Quick Demo Role Switcher (For Evaluation & Testing) ---
        with st.expander("⚡ Instant Demo Mode / Role Switcher"):
            st.caption("Test the ROADGUARD platform as either a Reporter or a Viewer:")
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                if st.button("📢 Reporter (Alice)", use_container_width=True, key="gate_alice"):
                    switch_demo_user("alice")
                if st.button("🚨 Emergency (Charlie)", use_container_width=True, key="gate_charlie"):
                    switch_demo_user("patrol_charlie")
            with c_d2:
                if st.button("👀 Viewer (Bob)", use_container_width=True, key="gate_viewer"):
                    switch_demo_user("viewer_bob")
                if st.button("🏛️ Authority (Bob)", use_container_width=True, key="gate_bob"):
                    switch_demo_user("officer_bob")

        # --- Supabase Configuration Guide ---
        with st.expander("🛠️ How to Configure Live Supabase Authentication"):
            st.markdown(
                """
                ### Step-by-Step Supabase Setup Guide:

                1. **Create a Free Supabase Project:**
                   - Go to [https://supabase.com](https://supabase.com) and sign in.
                   - Click **New Project** and name it `roadguard`.

                2. **Get API Keys:**
                   - In your Supabase project dashboard, navigate to **Project Settings** (gear icon) -> **API**.
                   - Copy the **Project URL** (e.g., `https://xyzproject.supabase.co`).
                   - Copy the **`anon` `public` Key**.

                3. **Configure URL Settings:**
                   - Go to **Authentication** -> **URL Configuration**.
                   - Set **Site URL** to `http://localhost:8501`.
                   - Add to **Redirect URLs**: `http://localhost:8501` and `http://localhost:8501/*`.

                4. **Configure Google OAuth (Optional):**
                   - In Supabase, go to **Authentication** -> **Providers** -> **Google**.
                   - Toggle **Enable Google provider**.
                   - Follow Google Cloud Console instructions to create an OAuth 2.0 Client ID and add Supabase's callback URL.

                5. **Add to `.streamlit/secrets.toml`:**
                   Create or edit `.streamlit/secrets.toml`:
                   ```toml
                   [supabase]
                   url = "https://your-project-id.supabase.co"
                   key = "your-anon-key-here"
                   redirect_url = "http://localhost:8501"
                   ```
                """
            )

def render_auth_sidebar():
    """
    Renders active user details, role badge, safety karma, and a prominent Logout button.
    Only called when the user is authenticated.
    """
    init_auth()
    user = get_current_user()

    if not user:
        return

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔐 User Profile")

    role_meta = USER_ROLES.get(user.get("role", "citizen"), {"label": user.get("role", "Citizen"), "icon": "👤"})
    email_display = user.get("email", "")

    st.sidebar.markdown(
        f"""
        <div class="user-profile-pill">
            <div style="display:flex; align-items:center; justify-content:space-between;">
                <div style="font-weight:700; font-size:15px; color:#1E3A8A;">
                    {user.get('avatar_icon', '🚗')} {user['full_name']}
                </div>
            </div>
            <div style="font-size:11px; color:#64748B; margin-top:2px; word-break:break-all;">
                {email_display}
            </div>
            <div style="margin-top:6px; font-size:12px; color:#475569;">
                <b>Role:</b> {role_meta['icon']} {role_meta['label']}
            </div>
            <div style="margin-top:2px; font-size:12px; color:#059669; font-weight:600;">
                <b>Rank:</b> {user.get('badge', '🌱 Novice Scout')}
            </div>
            <div style="margin-top:2px; font-size:12px; color:#D97706; font-weight:600;">
                <b>Safety Karma:</b> ⭐ {user.get('karma_points', 25)} pts
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Demo quick switch (for testing both roles)
    with st.sidebar.expander("🔄 Switch Role Perspective"):
        st.caption("Quickly test both role perspectives:")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📢 Reporter", use_container_width=True, key="side_reporter"):
                switch_demo_user("alice")
            if st.button("🚨 Emergency", use_container_width=True, key="side_charlie"):
                switch_demo_user("patrol_charlie")
        with col2:
            if st.button("👀 Viewer", use_container_width=True, key="side_viewer"):
                switch_demo_user("viewer_bob")
            if st.button("🏛️ Authority", use_container_width=True, key="side_bob"):
                switch_demo_user("officer_bob")

    # Logout button
    if st.sidebar.button("🚪 Log Out of ROADGUARD", use_container_width=True, type="primary"):
        logout_user()
