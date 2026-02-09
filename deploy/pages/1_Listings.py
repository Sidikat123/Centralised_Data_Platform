import streamlit as st
import pandas as pd

# --- Load Dataset ---
@st.cache_data
def load_data():

    df = pd.read_csv("model/cleaned_data.csv")
    # Clean up string columns
    for col in ["CITY", "STATE", "COUNTY", "PROPERTYTYPE", "ZIPCODE", "LISTINGTYPE"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
    return df

df = load_data()

# --- UI Config ---
st.set_page_config(page_title="📋 Property Listings", layout="wide")
st.title("🏘️ Property Listings")

# --- Filters UI ---
with st.expander("🔍 Filter Properties", expanded=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        city = st.selectbox("City", ["All"] + sorted(df["CITY"].dropna().unique()))
        property_type = st.selectbox("Property Type", ["All"] + sorted(df["PROPERTYTYPE"].dropna().unique()))

    with col2:
        state = st.selectbox("State", ["All"] + sorted(df["STATE"].dropna().unique()))
        listing_type = st.selectbox("Listing Type", ["All"] + sorted(df["LISTINGTYPE"].dropna().unique()))

    with col3:
        county = st.selectbox("County", ["All"] + sorted(df["COUNTY"].dropna().unique()))
        zipcode = st.selectbox("ZIP Code", ["All"] + sorted(df["ZIPCODE"].dropna().astype(str).unique()))

    # --- Room Filters ---
    st.markdown("### 🛏️ Room & Area Filters")
    col4, col5 = st.columns(2)
    with col4:
        bedrooms = st.slider(
            "Bedrooms",
            min_value=int(df["BEDROOMS"].min()),
            max_value=int(df["BEDROOMS"].max()),
            value=(int(df["BEDROOMS"].min()), int(df["BEDROOMS"].max()))
        )
    with col5:
        bathrooms = st.slider(
            "Bathrooms",
            min_value=float(df["BATHROOMS"].min()),
            max_value=float(df["BATHROOMS"].max()),
            value=(float(df["BATHROOMS"].min()), float(df["BATHROOMS"].max()))
        )

    # --- Date Filter ---
    st.markdown("### 📅 Listed Date Filter (Optional)")
    listed_after = st.date_input("Listed After", value=None)

# --- Apply Filters ---
df_filtered = df.copy()

# Categorical Filters
if city != "All":
    df_filtered = df_filtered[df_filtered["CITY"] == city]
if property_type != "All":
    df_filtered = df_filtered[df_filtered["PROPERTYTYPE"] == property_type]
if state != "All":
    df_filtered = df_filtered[df_filtered["STATE"] == state]
if listing_type != "All":
    df_filtered = df_filtered[df_filtered["LISTINGTYPE"] == listing_type]
if county != "All":
    df_filtered = df_filtered[df_filtered["COUNTY"] == county]
if zipcode != "All":
    df_filtered = df_filtered[df_filtered["ZIPCODE"].astype(str) == zipcode]

# Numeric Filters
df_filtered = df_filtered[
    (df_filtered["BEDROOMS"].between(bedrooms[0], bedrooms[1])) &
    (df_filtered["BATHROOMS"].between(bathrooms[0], bathrooms[1]))
]

# Date Filter (if selected)
if listed_after:
    if "LISTEDDATE" in df_filtered.columns:
        df_filtered["LISTEDDATE"] = pd.to_datetime(df_filtered["LISTEDDATE"], errors='coerce', utc=True)
        listed_after = pd.to_datetime(listed_after, utc=True)
        df_filtered = df_filtered[df_filtered["LISTEDDATE"] >= listed_after]
    else:
        st.warning("⚠️ 'LISTEDDATE' column not found in dataset.")

# --- Display Results ---
st.markdown("## 📊 Filtered Listings")
if df_filtered.empty:
    st.warning("⚠️ No matching properties found.")
else:
    st.dataframe(df_filtered, width='stretch')
    st.markdown(f"🔢 **{len(df_filtered)}** properties shown")

