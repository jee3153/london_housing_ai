import os

import mlflow.pyfunc
import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mlflow.tracking import MlflowClient
from pydantic import BaseModel

from london_housing_ai.predict import transform_to_training_features
from london_housing_ai.utils.logger import get_logger
import json
from pathlib import Path

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

app = FastAPI(title="London Housing Price Predictor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define input schema using Pydantic
class HousingData(BaseModel):
    area_in_sqft: int
    no_bedrooms: int
    house_type: str
    location: str


@app.post("/predict")
def predict(data: HousingData):
    if not runs:
        raise HTTPException(status_code=503, detail="No trained runs available")

    run_id = runs[0].info.run_id

    # Load your MLflow model by run ID or local path
    model = mlflow.pyfunc.load_model(
        f"runs:/{run_id}/{os.getenv("MLFLOW_ARTIFACT_PATH")}"
    )

    # Step 1: Convert user input
    user_input = data.model_dump()

    # Step 2: Transform into training features
    features = transform_to_training_features(user_input)
    logger.info(features.to_dict(orient="records"))
    logger.info(features.dtypes)

    # Step 3: Predict
    try:
        preds = model.predict(features)
    except Exception as e:
        logger.exception(f"Prediction failed due to {e}")
        raise HTTPException(status_code=500, detail="Prediction failed")

    return {"predicted_price": round(float(np.expm1(preds[0])), 2)}


@app.get("/experiment_runs")
def get_runs():
    return runs


@app.get("/artifacts/data_quality")
def get_data_quality_artifacts():
    if not runs:
        return {"messege": "No artifacts available", "artifacts": []}
    last_run_id = runs[-1].info.run_id
    data_quality_file = [
        artifact_name.path
        for artifact_name in client.list_artifacts(last_run_id)
        if str(artifact_name.path).startswith("data_quality")
        and not artifact_name.is_dir
    ]
    if not data_quality_file:
        return {"message": "No data quality file available for this experiment run"}
    data_quality_file_name = data_quality_file[0]
    local_data_quality_file = client.download_artifacts(
        path=data_quality_file_name, run_id=last_run_id
    )
    logger.info(
        f"data quality file name = {data_quality_file_name}, local_data_quality_file = {local_data_quality_file}"
    )
    if not local_data_quality_file:
        return {
            "message": "No data quality file available to download for this experiment run"
        }

    response = {}
    try:
        with open(local_data_quality_file, "r") as f:
            response[data_quality_file_name] = json.load(f)
    except FileNotFoundError as err:
        raise FileNotFoundError(
            f"File at {local_data_quality_file} was not found. Error message: {err}"
        )
    except:
        # Fallback for non-JSON files
        with open(local_data_quality_file, "r") as f:
            response[data_quality_file_name] = f.read()
    return response
