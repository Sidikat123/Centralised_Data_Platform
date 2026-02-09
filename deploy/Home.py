import streamlit as st

# --- Page Config ---
st.set_page_config(
    page_title="🏠 AlloyTower Home",
    layout="wide"
)

# --- Banner Image ---
st.image(
    r"C:\Users\USER\Desktop\Projects\Data Science\Centralized Data Platform\deploy\banner.png",
    caption="Premium Real Estate | AlloyTower Inc.",
    width="stretch"
)

# --- Main Title & Subtitle ---
st.markdown("""
<h1 style='text-align: center; color: #336699;'>
    🏠 Welcome to AlloyTower Inc Real Estate Platform
</h1>
<p style='text-align: center; font-size:18px;'>
    A unified solution for data-driven real estate insights, pricing predictions, and client interactions.
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# --- Overview Section with Image ---
col1, col2 = st.columns([1, 2])

with col1:
    st.image(
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c",
        caption="Modern Urban Property",
        width="stretch"
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

# --- Feature Navigation Info ---
st.subheader("🔍 Platform Features")

st.markdown("""
- 📋 **Property Listings** – Filter and explore properties by city, type, and status 
- 📈 **Demand and Market Analytics** – Explore Power BI dashboards for live market insights 
- 📊 **Predict Price + SHAP Explainability** – AI-powered price estimation with transparent reasoning  
- 🏘️ **Inquiry Form** – Submit questions or connect directly with agents  
""")

# Management Team 
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
