import streamlit as st
import os

# --- Page Config ---
st.set_page_config(page_title="🏠 AlloyTower Home", layout="wide")

# --- Auth Setup ---
USERS = {
    "admin": "password123",
    "user": "alloytower"
}

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- BANNER IMAGE ---
banner_path = os.path.join("deploy", "banner.png")
local_fallback = r"C:\Users\USER\Desktop\Projects\Data Science\Centralized Data Platform\deploy\banner.png"

if os.path.exists(banner_path):
    st.image(banner_path, caption="Premium Real Estate | AlloyTower Inc.", use_column_width=True)
elif os.path.exists(local_fallback):
    st.image(local_fallback, caption="Premium Real Estate | AlloyTower Inc.", width="stretch")
else:
    st.warning("🔍 Banner image not found.")

# --- Main Title ---
st.markdown("""
<h1 style='text-align: center; color: #336699;'>
    🏠 Welcome to AlloyTower Inc Real Estate Platform
</h1>
<p style='text-align: center; font-size:18px;'>
    A unified solution for data-driven real estate insights, pricing predictions, and client interactions.
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# --- Login Section (inside expander) ---
with st.expander("🔐 Login to Access Full Platform"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if USERS.get(username) == password:
            st.session_state.authenticated = True
            st.success("✅ Login successful. Use the sidebar to navigate.")
            st.experimental_rerun()
        else:
            st.error("❌ Invalid username or password")

# --- Logout button (if authenticated) ---
if st.session_state.authenticated:
    st.sidebar.success("🔓 Logged in")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.experimental_rerun()

# --- Overview Section ---
col1, col2 = st.columns([1, 2])

with col1:
    st.image(
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c",
        caption="Modern Urban Property",
        use_column_width=True
    )

with col2:
    st.subheader("📊 Company Overview")
    st.markdown("""
    **AlloyTower Inc.** was founded in **2012** with a mission to revolutionize real estate through technology.

    - 💡 We leverage **AI & Machine Learning** for price prediction  
    - 🌎 Centralized listings with rich geospatial data  
    - 📈 Integrated **Demand & Market Analytics** dashboards via Power BI            
    - 📊 Transparent, explainable models via **SHAP**  
    - 🏘️ Tools for **buyers, sellers, and agents**
    """)

st.markdown("---")

# --- Platform Features ---
st.subheader("🔍 Platform Features")

st.markdown("""
- 📋 **Property Listings** – Filter and explore properties by city, type, and status  
- 📈 **Demand and Market Analytics** – Explore Power BI dashboards for live market insights  
- 📊 **Predict Price + SHAP Explainability** – AI-powered price estimation with transparent reasoning  
- 🏘️ **Inquiry Form** – Submit questions or connect directly with agents  
""")

# --- Optional message to guide user ---
if not st.session_state.authenticated:
    st.info("🔐 Please log in to access Listings, Predict, Analytics, and Inquiry pages via the sidebar.")

# Optional: Management Team 
with st.expander("👥 Meet Our Management Team"):
    st.markdown("""
    - **CEO**: Akintayo Adesola  
    - **CTO**: Sidikat Adeyemi-Longe  
    - **Head of Data Engineering**: Maureen Maduka
    - **Head of Data Analytics**: Chinelo Akinleye
    - **Head of Business Analysis**: Rashidat Musa       
    - **Chief Product Officer**: Ogunwole Peace  
    """)

# --- Footer ---
st.markdown("---")
st.markdown("<p style='text-align:center;'>© 2026 AlloyTower Inc. All rights reserved.</p>", unsafe_allow_html=True)


