import os

import mlflow
import pandas as pd
from sqlalchemy import text

from london_housing_ai.persistence import get_engine
from london_housing_ai.utils.create_files import generate_artifact_from_payload
from mlflow.tracking import MlflowClient
from mlflow.entities import RunStatus
from typing import Optional

engine = get_engine()
with engine.begin() as conn:
    latest_table_name = conn.execute(
        text("SELECT table_name FROM dataset_hashes ORDER BY inserted_at DESC LIMIT 1")
    ).scalar_one_or_none()

if latest_table_name is None:
    raise RuntimeError("No persisted dataset found in dataset_hashes.")

# Load the engineered dataset from Postgres
df = pd.read_sql(f"SELECT * FROM {latest_table_name}", engine)

# Export borough_price_trend: district -> median price
borough_trend = df.groupby("district")["price"].median().to_dict()

# Export district_yearly_medians: district_year -> median price
district_yearly = df.groupby(["district", "sold_year"])["price"].median().reset_index()
district_yearly_dict = {
    f"{row.district}_{int(row.sold_year)}": row.price
    for row in district_yearly.itertuples()
}

# Export avg_price_last_half: district -> most recent 6 month median
# Simplification: use last 6 months of training data per district
df["date"] = pd.to_datetime(df["date"])
cutoff = df["date"].max() - pd.DateOffset(months=6)
recent = df[df["date"] >= cutoff]
recent_median = recent.groupby("district")["price"].median().to_dict()

artifacts = {
    "borough_price_trend": borough_trend,
    "district_yearly_medians": district_yearly_dict,
    "avg_price_last_half": recent_median,
}

LOOKUP_TABLE_NAME = "lookup_tables.json"
lookup_table_path = generate_artifact_from_payload(LOOKUP_TABLE_NAME, artifacts)

experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "LondonHousingAI")
mlflow.set_experiment(experiment_name)

client = MlflowClient(tracking_uri=os.getenv("MLFLOW_TRACKING_URI"))
experiment = client.get_experiment_by_name(experiment_name)
if experiment is None:
    raise RuntimeError("Experiment not found")

finished_status = RunStatus.to_string(RunStatus.FINISHED)
runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    filter_string=f"attributes.status = '{finished_status}'",
    order_by=["start_time DESC"],
    max_results=1,
)
run_id = runs[0].info.run_id if runs else None

with mlflow.start_run(run_id=run_id):
    mlflow.log_artifact(str(lookup_table_path))

print(f"Exported {len(borough_trend)} districts")
print(f"Exported {len(district_yearly_dict)} district-year pairs")
