from fastapi import FastAPI
from pydantic import BaseModel
import mlflow.pyfunc
import pandas as pd
import numpy as np
from mlflow.tracking import MlflowClient

client = MlflowClient(tracking_uri="http://mlflow:5000")
runs = client.search_runs(experiment_ids=["0"], filter_string="attributes.status = 'FINISHED'", order_by=["start_time DESC"], max_results=1)

if not runs:
    raise RuntimeError("No MLflow runs found! train and log a model before starting the API.")
run_id = runs[0].info.run_id
# Load your MLflow model by run ID or local path
model = mlflow.pyfunc.load_model(f"runs:/{run_id}/catboost_model")

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
    return {"predicted_price": round(np.expm1(preds[0]), 2)}
