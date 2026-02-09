from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
import pickle
import json
import os
import uvicorn
from datetime import date
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="AlloyTower Real Estate Pricing API",
    version="1.0"
)

# Load model and feature schema ONCE
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # deploy/
MODEL_PATH = os.path.join(BASE_DIR, "..", "model", "randomforest_tuned_model.pkl")
SCHEMA_PATH = os.path.join(BASE_DIR, "..", "model", "features_schema.json")
FREQ_MAP_PATH = os.path.join(BASE_DIR, "..", "model", "frequency_maps.json")  # must be saved during training
SHAP_EXPLAINER_PATH = os.path.join(BASE_DIR, "..", "model", "shap_explainer.pkl")
TREE_PREDS_PATH = os.path.join(BASE_DIR, "..", "model", "rf_tree_predictions.npy")
REF_PATH = os.path.join(BASE_DIR, "..", "model", "reference_averages.json")


if not os.path.exists(MODEL_PATH):
    raise RuntimeError("Model file not found")

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

# Load feature schema
with open(SCHEMA_PATH, "r") as f:
    FEATURE_COLUMNS = json.load(f)

# Load frequency maps 
with open(FREQ_MAP_PATH, "r") as f:
    FREQ_MAPS = json.load(f)

# Load SHAP explainer 
if not os.path.exists(SHAP_EXPLAINER_PATH):
    raise RuntimeError("SHAP explainer file not found")

with open(SHAP_EXPLAINER_PATH, "rb") as f:
    explainer = pickle.load(f)

# Load Tree-Level Predictions for Interval Estimation 
if not os.path.exists(TREE_PREDS_PATH):
    raise RuntimeError("Tree predictions file not found. Cannot compute prediction intervals.")

all_tree_preds = np.load(TREE_PREDS_PATH)  # shape: (n_samples_test, n_trees)

# Load reference averages (ZIPCODE and PROPERTYTYPE)
if not os.path.exists(REF_PATH):
    raise RuntimeError("reference_averages.json not found")

with open(REF_PATH, "r") as f:
    reference_averages = json.load(f)

# Request Schema
class PricingRequest(BaseModel):
    square_footage: float
    bedrooms: int
    bathrooms: float
    latitude: float
    longitude: float
    city: str
    state: str
    zipcode: str
    propertytype: str
    listed_date: date

# Feature Engineering
def prepare_features(request: PricingRequest) -> pd.DataFrame:
    df = pd.DataFrame([{
        "SQUAREFOOTAGE": request.square_footage,
        "BEDROOMS": request.bedrooms,
        "BATHROOMS": request.bathrooms,
        "LATITUDE": request.latitude,
        "LONGITUDE": request.longitude,
        "CITY": request.city,
        "STATE": request.state,
        "ZIPCODE": request.zipcode,
        "PROPERTYTYPE": request.propertytype,
        "LISTEDDATE": pd.to_datetime(request.listed_date)
    }])

    # Date Features
    df["LISTING_YEAR"] = df["LISTEDDATE"].dt.year
    df["LISTING_MONTH"] = df["LISTEDDATE"].dt.month
    df["LISTING_DAY"] = df["LISTEDDATE"].dt.day
    df.drop(columns=["LISTEDDATE"], inplace=True)

    # Frequency Encoding (ZIP / CITY / STATE)
    for col in ["ZIPCODE", "CITY", "STATE"]:
        freq_map = FREQ_MAPS.get(col, {})
        df[col] = df[col].map(freq_map).fillna(0)

    # One-Hot Encoding PROPERTYTYPE
    for col in FEATURE_COLUMNS:
        if col.startswith("PROPERTYTYPE_"):
            df[col] = 0

    prop_col = f"PROPERTYTYPE_{request.propertytype}"
    if prop_col in df.columns:
        df[prop_col] = 1

    # Align columns exactly to training schema
    df = df.reindex(columns=FEATURE_COLUMNS, fill_value=0)

    return df

# Prediction Endpoint
@app.post("/predict")
def predict_price(request: PricingRequest):
    try:
        X = prepare_features(request)

        # Get predictions from all trees
        tree_preds = np.stack([tree.predict(X.values)[0] for tree in model.estimators_])
       
        point_pred = tree_preds.mean()
        lower = np.percentile(tree_preds, 5)
        upper = np.percentile(tree_preds, 95)

        return {
            "predicted_price": round(float(point_pred), 2),
            "confidence_interval_90": {
                "lower_bound": round(float(lower), 2),
                "upper_bound": round(float(upper), 2)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run Locally 
if __name__ == "__main__":
    print(f"Server is on port {os.getenv('port', 3000)}")
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv('port', 3000)))



