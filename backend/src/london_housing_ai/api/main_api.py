import mlflow.pyfunc
import os
import numpy as np
from fastapi import FastAPI
from mlflow.tracking import MlflowClient
from pydantic import BaseModel
from dotenv import load_dotenv

from london_housing_ai.predict import transform_to_training_features
from london_housing_ai.utils.logger import get_logger

load_dotenv()
logger = get_logger()

client = MlflowClient(tracking_uri=os.getenv("MLFLOW_TRACKING_URI"))
experiment = client.get_experiment_by_name("LondonHousingAI")
if experiment is None:
    raise RuntimeError("There is no experiment done for LondonHousingAI")

runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    filter_string="attributes.status = 'FINISHED'",
    order_by=["start_time DESC"],
    max_results=30,
)

if not runs:
    raise RuntimeError(
        "No MLflow runs found! train and log a model before starting the API."
    )
run_id = runs[0].info.run_id
# Load your MLflow model by run ID or local path
model = mlflow.pyfunc.load_model(f"runs:/{run_id}/{os.getenv("MLFLOW_MODEL_NAME")}")

app = FastAPI(title="London Housing Price Predictor")


# Define input schema using Pydantic
class HousingData(BaseModel):
    area_in_sqft: int
    no_bedrooms: int
    house_type: str
    location: str


@app.post("/predict")
def predict(data: HousingData):
    # Step 1: Convert user input
    user_input = data.model_dump()

    # Step 2: Transform into training features
    features = transform_to_training_features(user_input)
    logger.info(features.to_dict(orient="records"))
    logger.info(features.dtypes)
    # Step 3: Predict
    preds = model.predict(features)
    return {"predicted_price": round(float(np.expm1(preds[0])), 2)}


@app.get("/experiment_runs")
def get_runs():
    return runs
