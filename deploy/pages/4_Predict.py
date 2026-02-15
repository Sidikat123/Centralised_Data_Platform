import streamlit as st
import pandas as pd
from pathlib import Path
import requests
from datetime import datetime
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from streamlit_shap import st_shap 
from huggingface_hub import hf_hub_download
from lib.app_shell import init_state, hide_default_streamlit_pages_nav, render_sidebar, require_auth
import pickle
import json
import shap
import os
import joblib  
from dotenv import load_dotenv

# --- Load .env variables ---
load_dotenv()

# Detect Local Environment 
IS_LOCAL = os.getenv("IS_LOCAL", "true").lower() == "true"
ENABLE_SHAP = IS_LOCAL  # SHAP is only enabled locally

# Load Hugging Face Token 
hf_token = os.getenv("HF_TOKEN")

# On Streamlit Cloud, token may come from secrets
if not hf_token:
    try:
        hf_token = st.secrets["HF_TOKEN"] 
    except Exception:
        hf_token = None

if not hf_token and not IS_LOCAL:
    st.warning("🔑 Hugging Face token not found. Model download may fail.")

# --- Hugging Face Repo ---
REPO_ID = "Sidikat123/Centralised-Data-Platform-Model"

artifact_files = {
    "model": "randomforest_tuned_model.pkl",
    "features": "features_schema.json",
    "freq_map": "frequency_maps.json",
    "ref_avg": "reference_averages.json"
}

artifact_paths = {}

# 🟢 LOCAL ENVIRONMENT (load from local /model folder)
if IS_LOCAL:

    # Get project root (two levels up from deploy/pages/)
    PROJECT_ROOT = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )

    LOCAL_MODEL_DIR = os.path.join(PROJECT_ROOT, "model")

    for key, filename in artifact_files.items():
        artifact_paths[key] = os.path.join(LOCAL_MODEL_DIR, filename)
    

# 🔵 STREAMLIT CLOUD (download from HuggingFace)
else:
    try:
        from huggingface_hub import hf_hub_download

        for key, filename in artifact_files.items():
            artifact_paths[key] = hf_hub_download(
                repo_id=REPO_ID,
                filename=filename,
                token=hf_token
            )

    except Exception as e:
        st.error(f"❌ Failed to load model/artifacts from Hugging Face Hub: {e}")
        st.stop()

# --- Final paths used later in app ---
model_path = artifact_paths["model"]
features_path = artifact_paths["features"]
freq_map_path = artifact_paths["freq_map"]
ref_avg_path = artifact_paths["ref_avg"]

# Load model
@st.cache_resource
def load_model():
    try:
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        return model
    except Exception as e:
        st.error(f"❌ Error loading model: {e}")
        return None

model = load_model()  # Load the model

st.write("Model loaded:", model is not None)  # Debug check

# Load other artifacts
with open(features_path, "r") as f:
    FEATURE_COLUMNS = json.load(f)

with open(freq_map_path, "r") as f:
    FREQ_MAPS = json.load(f)

with open(ref_avg_path, "r") as f:
    reference_averages = json.load(f)

# Normalize keys
reference_averages["zipcode"] = {
    str(k).strip(): v for k, v in reference_averages.get("zipcode", {}).items()
}
reference_averages["propertytype"] = {
    k.strip().lower(): v for k, v in reference_averages.get("propertytype", {}).items()
}

# SHAP Compatibility
FEATURE_COLUMNS = [str(col) for col in FEATURE_COLUMNS]

@st.cache_resource
def load_explainer(_model):
    return shap.TreeExplainer(_model)

# --- load cities/states from your CSV ---
@st.cache_data
def load_agent_data() -> pd.DataFrame:
    deploy_dir = Path(__file__).resolve().parents[1]  # .../deploy
    csv_path = deploy_dir / "Agent.csv"
    df = pd.read_csv(csv_path)

    # basic cleanup
    for c in ["CITY", "STATE"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()
            df.loc[df[c].isin(["", "nan", "None"]), c] = pd.NA

    df = df.dropna(subset=["CITY", "STATE"])
    return df

df_geo = load_agent_data()

# Precompute lookups
all_cities = sorted(df_geo["CITY"].unique().tolist())
all_states = sorted(df_geo["STATE"].unique().tolist())

city_to_states = (
    df_geo.groupby("CITY")["STATE"]
    .apply(lambda s: sorted(s.unique().tolist()))
    .to_dict()
)

state_to_cities = (
    df_geo.groupby("STATE")["CITY"]
    .apply(lambda s: sorted(s.unique().tolist()))
    .to_dict()
)

# Session defaults
if "CITY" not in st.session_state:
    st.session_state.CITY = "All"
if "STATE" not in st.session_state:
    st.session_state.STATE = "All"

# Controls whether STATE dropdown is restricted (only when city maps to multiple states)
if "STATE_MODE" not in st.session_state:
    st.session_state.STATE_MODE = "all"  # "all" or "restricted"

# Controls whether CITY dropdown shows all cities or only cities in selected state
if "CITY_OPTIONS_MODE" not in st.session_state:
    st.session_state.CITY_OPTIONS_MODE = "all"  # "all" or "state"

def on_city_change():
    city = st.session_state.CITY

    # --- NEW: if All city, don't force any state ---
    if city == "All":
        st.session_state.STATE = "All"
        st.session_state.STATE_MODE = "all"
        return

    states = city_to_states.get(city, [])

    if len(states) == 1:
        st.session_state.STATE = states[0]
        st.session_state.STATE_MODE = "all"
    elif len(states) > 1:
        st.session_state.STATE_MODE = "restricted"
        if st.session_state.STATE not in states:
            st.session_state.STATE = states[0]
    else:
        st.session_state.STATE_MODE = "all"

def on_state_change():
    state = st.session_state.STATE

    # If All state, allow all cities and don't force a city 
    if state == "All":
        st.session_state.CITY_OPTIONS_MODE = "all"
        # optional: keep current city if it’s valid, otherwise set to All
        if st.session_state.CITY not in (["All"] + all_cities):
            st.session_state.CITY = "All"
        return

    # state picked -> restrict city list to that state's cities
    st.session_state.CITY_OPTIONS_MODE = "state"

    # once state is explicitly chosen, don't keep restricting the state list
    st.session_state.STATE_MODE = "all"

    cities = state_to_cities.get(state, [])
    # if current city isn't in that state, set to first city in that state
    if cities and st.session_state.CITY not in cities:
        st.session_state.CITY = cities[0]

# App Config 
st.set_page_config(page_title="AlloyTower Inc Real Estate Price Estimator", layout="wide")

init_state()
hide_default_streamlit_pages_nav()
render_sidebar()

require_auth()  # ✅ blocks access if not logged in

st.markdown( "<h1 style='text-align:center; color:#336699; margin:0;'>🏠 AlloyTower Inc Real Estate Price Estimator</h1>", unsafe_allow_html=True)
st.markdown( "<p style='text-align:center; margin:0; padding:0;'>Predict home prices with market average benchmark, confidence intervals and explainable ML.</p>", unsafe_allow_html=True)


# Feature Inputs 
st.header("📝 Input Property Details")
# CHANGE 1: MOVE CITY/STATE OUTSIDE THE FORM (callbacks allowed)
st.subheader("📍 Location")

loc_c1, loc_c2 = st.columns(2)

# CITY options depend on mode (but support STATE="All")
if st.session_state.get("CITY_OPTIONS_MODE", "all") == "state" and st.session_state.STATE != "All":
    city_options = state_to_cities.get(st.session_state.STATE, all_cities)
else:
    city_options = all_cities

# --- NEW: prepend "All" and keep selection valid ---
city_options = ["All"] + city_options
if st.session_state.CITY not in city_options:
    st.session_state.CITY = "All"

with loc_c1:
    st.selectbox("City", city_options, key="CITY", on_change=on_city_change)

selected_city = st.session_state.CITY

# STATE options depend on city, but support CITY="All"
if selected_city == "All":
    possible_states = ["All"] + all_states
    st.session_state.STATE_MODE = "all"  # ensure not stuck in restricted
else:
    possible_states = city_to_states.get(selected_city, all_states)
    possible_states = ["All"] + possible_states  # --- NEW: allow "All" even if city has multiple states ---

with loc_c2:
    if st.session_state.STATE_MODE == "restricted" and selected_city != "All" and len(possible_states) > 2:
        st.selectbox(
            "State (multiple matches for this city)",
            possible_states,
            key="STATE",
            on_change=on_state_change
        )
        st.caption("This city exists in multiple states — pick the correct one.")
    else:
        st.selectbox("State", ["All"] + all_states, key="STATE", on_change=on_state_change)

# CHANGE 2: define city/state variables AFTER the widgets
city = st.session_state.CITY
state = st.session_state.STATE

with st.form("input_form"):
    # Row 1
    c1, c2, c3 = st.columns(3)
    with c1:
        square_footage = st.number_input("Square Footage", min_value=100, value=1600, step=1)
    with c2:
        bedrooms = st.number_input("Bedrooms", min_value=0, value=3, step=1)
    with c3:
        bathrooms = st.number_input("Bathrooms", min_value=0, value=2, step=1)

    # Row 2
    c1, c2, c3 = st.columns(3)
    with c1:
        listed_date = st.date_input("Listing Date", datetime.today())
    with c2:
        latitude = st.number_input("Latitude", value=37.7749)
    with c3:
        longitude = st.number_input("Longitude", value=-122.4194)

    # Row 3 (City/State + Zip + PropertyType)
    c3, c4 = st.columns(2)

    # ZIPCODE
    with c3:
        zip_options = sorted(reference_averages["zipcode"].keys())
        zipcode = st.selectbox(
            "ZIP Code",
            zip_options,
            index=zip_options.index("94103") if "94103" in zip_options else 0
        )

    # PROPERTYTYPE
    with c4:
        propertytype = st.selectbox(
            "Property Type",
            ["Apartment", "Condo", "Manufactured", "Multi-Family", "Single Family", "Townhouse"]
        )

    # Unified reference selection
    ref_type = st.radio("Market Average Benchmark Reference Based On", ["ZIP Code", "Property Type"])

    submit = st.form_submit_button("📈 Predict Price")

# Feature Preparation Function 
def prepare_features_for_shap():
    df = pd.DataFrame([{
        "SQUAREFOOTAGE": square_footage,
        "BEDROOMS": bedrooms,
        "BATHROOMS": bathrooms,
        "LATITUDE": latitude,
        "LONGITUDE": longitude,
        "CITY": city,
        "STATE": state,
        "ZIPCODE": zipcode,
        "PROPERTYTYPE": propertytype,
        "LISTEDDATE": pd.to_datetime(listed_date)
    }])

    df["LISTING_YEAR"] = df["LISTEDDATE"].dt.year
    df["LISTING_MONTH"] = df["LISTEDDATE"].dt.month
    df["LISTING_DAY"] = df["LISTEDDATE"].dt.day
    df.drop(columns=["LISTEDDATE"], inplace=True)

    for col in ["ZIPCODE", "CITY", "STATE"]:
        freq_map = FREQ_MAPS.get(col, {})
        df[col] = df[col].map(freq_map).fillna(0)

    for col in FEATURE_COLUMNS:
        if col.startswith("PROPERTYTYPE_"):
            df[col] = 0
    prop_col = f"PROPERTYTYPE_{propertytype}"
    if prop_col in df.columns:
        df[prop_col] = 1

    df = df.reindex(columns=FEATURE_COLUMNS, fill_value=0)
    df.columns = df.columns.astype(str)
    return df

# Prediction Logic 
if submit:
    st.info("⏳ Making prediction...")

    payload = {
        "square_footage": square_footage,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "latitude": latitude,
        "longitude": longitude,
        "city": city,
        "state": state,
        "zipcode": zipcode,
        "propertytype": propertytype,
        "listed_date": listed_date.isoformat()
    }
    
    try:
        response = requests.post("https://kl8fjd4z-8000.uks1.devtunnels.ms/predict", json=payload) 
        result = response.json()

        pred = result["predicted_price"]
        ci = result["confidence_interval_90"]

        st.success("✅ Prediction completed!")

        # --- Unified reference logic ---
        if ref_type == "ZIP Code":
            reference_value = reference_averages["zipcode"].get(zipcode, pred)
            label = f"ZIP Code {zipcode}"
        else:
            reference_value = reference_averages["propertytype"].get(propertytype.lower(), pred)
            label = f"{propertytype} Average"

        delta = pred - reference_value
        st.subheader("📊 Market Reference Comparison")
        st.metric(label=f"{label} Avg Price", value=f"${reference_value:,.0f}", delta=f"${delta:,.0f}")

        # --- Estimated Price Display ---
        st.markdown(f"""
        <div style='background-color:#f2f9ff;padding:20px;border-radius:10px;border-left:6px solid #2a9df4'>
            <h3>🏷️ Estimated Price: <span style='color:#2a9df4;'>${pred:,.2f}</span></h3>
            <p><strong>90% Confidence Interval:</strong><br>
            <span style='font-size:16px;'>Lower: ${ci['lower_bound']:,.2f} | Upper: ${ci['upper_bound']:,.2f}</span></p>
        </div>
        """, unsafe_allow_html=True)

        # --- Gauge Chart ---
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=pred,
            title={'text': "Estimated Price (USD)"},
            delta={'reference': reference_value, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
            gauge={
                'axis': {'range': [ci['lower_bound'], ci['upper_bound']]},
                'bar': {'color': "#2a9df4"},
                'steps': [
                    {'range': [ci['lower_bound'], pred], 'color': "#b3d9ff"},
                    {'range': [pred, ci['upper_bound']], 'color': "#d1eaff"}
                ],
            }
        ))
        st.plotly_chart(fig, width='stretch')

        # --- SHAP Explanation ---
        if ENABLE_SHAP:
            if model is None:
                st.error("Model not loaded. SHAP explainability not available.")
            else:
                with st.expander("🔍 Show SHAP Feature Impact (Explainability)", expanded=False):
                    try:
                        explainer = load_explainer(model)

                        # Prepare input for SHAP
                        X = prepare_features_for_shap()
                        shap_values = explainer(X)

                        st.subheader("SHAP Feature Importance (Bar Plot)")
                        fig, ax = plt.subplots(figsize=(10, 6))
                        shap.plots.bar(shap_values, max_display=len(FEATURE_COLUMNS), show=False)
                        st.pyplot(fig)

                    except Exception as e:
                        st.error(f"SHAP Feature Importance plot failed: {e}")

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Failed to get prediction: {e}")
    except Exception as e:
        st.error(f"⚠️ Unexpected error: {str(e)}")

