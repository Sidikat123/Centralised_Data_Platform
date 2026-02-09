import streamlit as st

st.set_page_config(page_title="📈 Market Analytics", layout="wide")

st.title("📊 Demand and Market Analytics")
st.markdown("Visual insights into regional demand, historical pricing trends, and market movement.")

# Embed Power BI public report
powerbi_url = "https://app.powerbi.com/view?r=YOUR_PUBLIC_REPORT_ID"

st.markdown(
    f"""
    <iframe title="Power BI Report" 
            width="100%" height="650" 
            src="{powerbi_url}" 
            frameborder="0" allowFullScreen="true"></iframe>
    """,
    unsafe_allow_html=True
)
