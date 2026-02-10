import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from streamlit_shap import st_shap 
from huggingface_hub import hf_hub_download
import pickle
import json
import shap
import os
import joblib  


# Replace this with your actual Hugging Face repo
REPO_ID = "Sidikat123/Centralised-Data-Platform-Model"

# Download files from Hugging Face
try:
    model_path = hf_hub_download(repo_id=REPO_ID, filename="randomforest_tuned_model.pkl")
    shap_path = hf_hub_download(repo_id=REPO_ID, filename="shap_explainer.joblib")
    features_path = hf_hub_download(repo_id=REPO_ID, filename="features_schema.json")
    freq_map_path = hf_hub_download(repo_id=REPO_ID, filename="frequency_maps.json")
    ref_avg_path = hf_hub_download(repo_id=REPO_ID, filename="reference_averages.json")
except Exception as e:
    st.error(f"❌ Failed to load model/artifacts from Hugging Face: {e}")
    st.stop()


# Load model
with open(model_path, "rb") as f:
    model = pickle.load(f)  # or pickle.load(f) if you used pickle

# Load SHAP explainer
explainer = joblib.load(shap_path)

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

# App Config 
st.set_page_config(page_title="AlloyTower Inc Real Estate Price Estimator", layout="wide")

st.markdown("<h1 style='text-align: center; color:#336699;'>🏠 AlloyTower Inc Real Estate Price Estimator</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Predict home prices with confidence intervals and explainable ML.</p>", unsafe_allow_html=True)

# Sidebar Inputs 
st.sidebar.header("📝 Input Property Details")
with st.sidebar.form("input_form"):
    square_footage = st.number_input("Square Footage", min_value=100, value=1600, step=1)
    bedrooms = st.number_input("Bedrooms", min_value=0, value=3, step=1)
    bathrooms = st.number_input("Bathrooms", min_value=0, value=2, step=1)
    latitude = st.number_input("Latitude", value=37.7749)
    longitude = st.number_input("Longitude", value=-122.4194)
    city = st.selectbox("City", ["San Francisco", "Boston", "New York"])
    state = st.selectbox("State", ["CA", "MA", "NY"])

    zip_options = sorted(reference_averages["zipcode"].keys())
    zipcode = st.selectbox("ZIP Code", zip_options, index=zip_options.index("94103") if "94103" in zip_options else 0)

    propertytype = st.selectbox("Property Type", [
        "Apartment", "Condo", "Manufactured", "Multi-Family", "Single Family", "Townhouse"
    ])
    listed_date = st.date_input("Listing Date", datetime.today())

    # Unified reference selection
    ref_type = st.radio("Reference Based On", ["ZIP Code", "Property Type"])

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
        st.plotly_chart(fig, use_container_width=stretch)

        # --- SHAP Explanation ---
        with st.expander("🔍 Show SHAP Feature Impact (Explainability)", expanded=False):
            try:
                # Prepare features for SHAP
                X = prepare_features_for_shap()
                shap_values = explainer(X)

                st.subheader("SHAP Feature Importance (Bar Plot)")
                fig, ax = plt.subplots(figsize=(10, 6))
                shap.plots.bar(shap_values, max_display=len(FEATURE_COLUMNS), show=False)
                st.pyplot(fig)

            except Exception as e:
                st.error(f"SHAP waterfall plot failed: {e}")

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Failed to get prediction: {e}")
    except Exception as e:
        st.error(f"⚠️ Unexpected error: {str(e)}")
