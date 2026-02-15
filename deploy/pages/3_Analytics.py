import streamlit as st
import streamlit.components.v1 as components
from lib.app_shell import init_state, hide_default_streamlit_pages_nav, render_sidebar, require_auth

st.set_page_config(page_title="📈 Demand and Market Analytics", layout="wide")

init_state()
hide_default_streamlit_pages_nav()
render_sidebar()

require_auth()  # ✅ blocks access if not logged in

st.title("📊 Demand and Market Analytics")
st.markdown("Visual insights into regional demand, historical pricing trends, and market movement.")

powerbi_url = "https://app.powerbi.com/view?r=eyJrIjoiNGQwMzE2ODItMDE4OS00OTkzLTgzNmUtMzgyY2E4NTQwZTM0IiwidCI6ImZmMGYzZTNhLTNlNTMtNDU0Zi1iMmI1LTZjNjg3NTNiOGVlNCJ9&pageName=5b8b3826dc605438b5de9"

st.markdown(
    f"""
    <div style="width: 100%; margin-top: 0.5rem;">
      <iframe
        title="INC PROJECT"
        src="{powerbi_url}"
        style="width: 100%; height: 650px; border: 0; display: block;"
        allowfullscreen="true">
      </iframe>
    </div>
    """,
    unsafe_allow_html=True
)