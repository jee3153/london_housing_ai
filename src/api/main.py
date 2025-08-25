from fastapi import FastAPI
from pydantic import BaseModel
import mlflow.pyfunc
import pandas as pd
import numpy as np
from mlflow.tracking import MlflowClient

# Initialize MLflow client
client = MlflowClient(tracking_uri="http://mlflow:5000")

# Get the latest model version of PriceModel (not yet staged)
latest_versions = client.get_latest_versions("PriceModel", stages=["None"])
if not latest_versions:
    raise RuntimeError("No new model version found in registry. Train and log a model first.")

# Promote the most recent version to Production
latest_version = latest_versions[0].version
client.transition_model_version_stage(
    name="PriceModel",
    version=latest_version,
    stage="Production",
    archive_existing_versions=True,
)

print(f"Promoted PriceModel version {latest_version} to Production.")

# Always load the current Production model
model = mlflow.pyfunc.load_model("models:/PriceModel/Production")

app = FastAPI(title="London Housing Price Predictor")


# Define input schema using Pydantic
class HousingData(BaseModel):
    area_in_sqft: int
    no_bedrooms: int
    house_type: str
    location: str


@app.post("/predict")
def predict(data: HousingData):
    df = pd.DataFrame([data.model_dump()])
    preds = model.predict(df)
    
    # Handle log_target decoding if required (optional safeguard)
    try:
        predicted_price = float(np.expm1(preds[0]))
    except Exception:
        predicted_price = float(preds[0])
    
    return {"predicted_price": round(predicted_price, 2)}