# lib/app_shell.py
import json
import os
import streamlit as st

USER_FILE = "users.json"

# Exact paths based on your filenames
HOME_PATH = "Home.py"
LISTINGS_PATH = "pages/1_Listings.py"
FIND_AGENT_PATH = "pages/2_Find_Agent.py"
ANALYTICS_PATH = "pages/3_Analytics.py"
PREDICT_PATH = "pages/4_Predict.py"
INQUIRY_PATH = "pages/5_Inquiry_Form.py"


def _ensure_user_file():
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w") as f:
            json.dump({}, f)


def load_users() -> dict:
    _ensure_user_file()
    with open(USER_FILE, "r") as f:
        return json.load(f)


def save_users(users: dict) -> None:
    with open(USER_FILE, "w") as f:
        json.dump(users, f)


def init_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "register_mode" not in st.session_state:
        st.session_state.register_mode = False
    if "user_email" not in st.session_state:
        st.session_state.user_email = None


def require_auth(redirect_to: str = HOME_PATH):
    """Call this near the top of protected pages."""
    if not st.session_state.get("authenticated", False):
        st.warning("Please log in to access this page.")
        st.switch_page(redirect_to)
        st.stop()


def hide_default_streamlit_pages_nav():
    st.markdown(
        """
        <style>
        /* Streamlit 1.53.x: hide multipage nav (Pages list) */
        div[data-testid="stSidebarNav"] { display: none !important; }
        section[data-testid="stSidebarNav"] { display: none !important; }
        nav[data-testid="stSidebarNav"] { display: none !important; }

        /* Also hide its children + separators (varies by patch) */
        div[data-testid="stSidebarNavItems"] { display: none !important; }
        div[data-testid="stSidebarNavSeparator"] { display: none !important; }
        button[data-testid="stSidebarNavViewButton"] { display: none !important; }

        /* Remove extra top padding left behind by the hidden nav */
        div[data-testid="stSidebar"] > div:first-child { padding-top: 0rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def sidebar_nav():
    """Sidebar navigation. Locked pages are visible but disabled until logged in."""
    authed = st.session_state.get("authenticated", False)

    st.markdown("## 🧭 Navigation")

    if st.button("🏠 Home", use_container_width=True):
        st.switch_page(HOME_PATH)

    if st.button("📋 Listings", use_container_width=True):
        st.switch_page(LISTINGS_PATH)
    
    if st.button("🧑‍💼 Find Agent 🔒", disabled=(not authed), use_container_width=True):
        st.switch_page(FIND_AGENT_PATH)

    if st.button("📊 Analytics 🔒", disabled=(not authed), use_container_width=True):
        st.switch_page(ANALYTICS_PATH)

    if st.button("🤖 Predict 🔒", disabled=(not authed), use_container_width=True):
        st.switch_page(PREDICT_PATH)

    if st.button("📝 Inquiry Form", use_container_width=True):
        st.switch_page(INQUIRY_PATH)

    if not authed:
        st.caption("🔒 Login to unlock Find Agent, Analytics and Predict.")


def auth_box():
    """Login/Register/Logout UI."""
    users = load_users()

    st.markdown("## 🔐 Secure Access")

    if (not st.session_state.authenticated) and (not st.session_state.register_mode):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):
            if users.get(email) == password:
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.success("✅ Logged in successfully!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

        if st.button("Register", use_container_width=True):
            st.session_state.register_mode = True
            st.rerun()

    elif st.session_state.register_mode:
        new_email = st.text_input("New Email")
        new_pass = st.text_input("New Password", type="password")
        confirm_pass = st.text_input("Confirm Password", type="password")

        if st.button("Submit Registration", use_container_width=True):
            if not new_email or not new_pass:
                st.error("❌ Email and password required.")
            elif new_email in users:
                st.warning("⚠️ User already exists.")
            elif new_pass != confirm_pass:
                st.error("❌ Passwords do not match.")
            else:
                users[new_email] = new_pass
                save_users(users)
                st.success("✅ Registration successful! You can now log in.")
                st.session_state.register_mode = False
                st.rerun()

        if st.button("Back to Login", use_container_width=True):
            st.session_state.register_mode = False
            st.rerun()

    else:
        st.success(f"✅ Logged in as {st.session_state.user_email}")
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.rerun()


def render_sidebar():
    """Call this in every page."""
    with st.sidebar:
        sidebar_nav()
        st.divider()
        auth_box()
