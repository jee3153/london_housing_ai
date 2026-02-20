# London Housing API - Backend

FastAPI backend for housing price prediction.

## Features

- [x] Automated data loading and cleaning from CSV
- [x] Persist cleaned data to database (Postgres)
- [x] Feature engineering (postcode, house types, etc.)
- [x] Model training and evaluation
- [x] Experiment tracking with MLflow
- [x] Write dataframe into parquet files classified by sold_year
- [x] Store parque files to Google Cloud Storage
- [ ] Model versioning/registry
- [x] Model serving (API)
- [x] Docker/Cloud deployment
- [ ] Dashboard for data validation and model interpretability

## API Endpoints

### Health Check

```bash
curl http://localhost:7777/health
```

Response:

```json
{
  "status": "ok",
  "experiment_name": "LondonHousingAI",
  "mlflow_tracking_uri": "http://mlflow:5000",
  "latest_run_id": "0cbf545a66014505a698a5bf1ffd9ea0",
  "model_loaded": true,
  "transformer_loaded": true,
  "detail": null
}
```

### Get Model Performance

```bash
curl http://localhost:7777/mlflow/runs
```

Response:

```json
[
  {
    "data": {
      "metrics": {
        "train_rmse": 307295.5976804504,
        "train_mse": 94430584353.78523,
        "train_r2": 0.549071639784239,
        "validation_rmse": 341749.9735861974,
        "validation_mse": 116793044446.16664,
        "validation_r2": 0.4386297081718271,
        "test_rmse": 338625.6701904285,
        "test_mse": 114667344511.91685,
        "test_r2": 0.449057980372933
      },
      "params": {
        "loss_function": "MAE",
        "iterations": "4000",
        "depth": "8",
        "learning_rate": "0.05",
        "early_stopping_rounds": "200",
        "random_seed": "42",
        "model_class": "CatBoostRegressor",
        "log_target": "True",
        "raw_csv_sha256": "4440baedbd5aa47ca3dac76ef1aaa360c03b44e4a567a7d49047ef7f25e88f8d"
      },
      "tags": {
        "mlflow.user": "root",
        "mlflow.source.name": "/app/src/london_housing_ai/train_main.py",
        "mlflow.source.type": "LOCAL",
        "mlflow.runName": "london_housing_run"
      }
    },
    "info": {
      "artifact_uri": "file:///mlruns/6cb0c6846874447786ae03c306bbc05f/artifacts",
      "end_time": 1771583813443,
      "experiment_id": "1",
      "lifecycle_stage": "active",
      "run_id": "6cb0c6846874447786ae03c306bbc05f",
      "run_uuid": "6cb0c6846874447786ae03c306bbc05f",
      "start_time": 1771583735133,
      "status": "FINISHED",
      "user_id": "root"
    }
  },
  {
    "data": {
      "metrics": {
        "train_rmse": 307295.5976804504,
        "train_mse": 94430584353.78523,
        "train_r2": 0.549071639784239,
        "validation_rmse": 341749.9735861974,
        "validation_mse": 116793044446.16664,
        "validation_r2": 0.4386297081718271,
        "test_rmse": 338625.6701904285,
        "test_mse": 114667344511.91685,
        "test_r2": 0.449057980372933
      },
      "params": {
        "loss_function": "MAE",
        "iterations": "4000",
        "depth": "8",
        "learning_rate": "0.05",
        "early_stopping_rounds": "200",
        "random_seed": "42",
        "model_class": "CatBoostRegressor",
        "log_target": "True",
        "raw_csv_sha256": "4440baedbd5aa47ca3dac76ef1aaa360c03b44e4a567a7d49047ef7f25e88f8d"
      },
      "tags": {
        "mlflow.user": "root",
        "mlflow.source.name": "/app/src/london_housing_ai/train_main.py",
        "mlflow.source.type": "LOCAL",
        "mlflow.runName": "london_housing_run"
      }
    },
    "info": {
      "artifact_uri": "file:///mlruns/0cbf545a66014505a698a5bf1ffd9ea0/artifacts",
      "end_time": 1771580984264,
      "experiment_id": "1",
      "lifecycle_stage": "active",
      "run_id": "0cbf545a66014505a698a5bf1ffd9ea0",
      "run_uuid": "0cbf545a66014505a698a5bf1ffd9ea0",
      "start_time": 1771580792444,
      "status": "FINISHED",
      "user_id": "root"
    }
  },
  {
    "data": {
      "metrics": {},
      "params": {},
      "tags": {
        "mlflow.user": "root",
        "mlflow.source.name": "/app/src/london_housing_ai/scripts/export_lookup_tables.py",
        "mlflow.source.type": "LOCAL",
        "mlflow.runName": "export_lookup_tables"
      }
    },
    "info": {
      "artifact_uri": "file:///mlruns/fde3bf9cb6324477824c6f3725ca070c/artifacts",
      "end_time": 1771513107842,
      "experiment_id": "1",
      "lifecycle_stage": "active",
      "run_id": "fde3bf9cb6324477824c6f3725ca070c",
      "run_uuid": "fde3bf9cb6324477824c6f3725ca070c",
      "start_time": 1771513107794,
      "status": "FINISHED",
      "user_id": "root"
    }
  },
  {
    "data": {
      "metrics": {
        "train_rmse": 307295.5976804504,
        "train_mse": 94430584353.78523,
        "train_r2": 0.549071639784239,
        "validation_rmse": 341749.9735861974,
        "validation_mse": 116793044446.16664,
        "validation_r2": 0.4386297081718271,
        "test_rmse": 338625.6701904285,
        "test_mse": 114667344511.91685,
        "test_r2": 0.449057980372933
      },
      "params": {
        "loss_function": "MAE",
        "iterations": "4000",
        "depth": "8",
        "learning_rate": "0.05",
        "early_stopping_rounds": "200",
        "random_seed": "42",
        "model_class": "CatBoostRegressor",
        "raw_csv_sha256": "4440baedbd5aa47ca3dac76ef1aaa360c03b44e4a567a7d49047ef7f25e88f8d"
      },
      "tags": {
        "mlflow.user": "root",
        "mlflow.source.name": "/app/src/london_housing_ai/train_main.py",
        "mlflow.source.type": "LOCAL",
        "mlflow.runName": "london_housing_run"
      }
    },
    "info": {
      "artifact_uri": "file:///mlruns/014ba0d7caf1420b86d1240a2335dad2/artifacts",
      "end_time": 1771510117977,
      "experiment_id": "1",
      "lifecycle_stage": "active",
      "run_id": "014ba0d7caf1420b86d1240a2335dad2",
      "run_uuid": "014ba0d7caf1420b86d1240a2335dad2",
      "start_time": 1771510107305,
      "status": "FINISHED",
      "user_id": "root"
    }
  }
]
```

### Predict Price

```bash
curl -X POST http://localhost:7777/predict \
  -H "Content-Type: application/json" \
  -d '{"postcode":"SW1A 1AA","property_type":"F"}'
```

Response:

```json
{
  "predicted_price": 857346.67,
  "confidence_interval": [
    771612.0,
    943081.34
  ],
  "model_version": "london_housing_model:6cb0c684",
  "features_used": {
    "user_provided": [
      "is_leasehold",
      "is_new_build",
      "postcode",
      "property_type"
    ],
    "enriched": [
      "district",
      "borough_price_trend",
      "district_yearly_medians",
      "avg_price_last_half",
      "advanced_property_type",
      "property_type_and_tenure",
      "property_type_and_district",
      "sold_year",
      "sold_month",
      "date"
    ],
    "defaulted": []
  },
  "run_id": "6cb0c6846874447786ae03c306bbc05f"
}
```

## Request Schema

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| postcode | string | Yes | UK postcode (full or partial) | "SW1A 1AA" or "SW1A" |
| property_type | string | Yes | F=Flat, T=Terraced, S=Semi, D=Detached | "F" |
| is_new_build | string | No | Y/N flag for new build (defaults to "N") | "N" |
| is_leasehold | string | No | Y/N flag for leasehold (defaults to "N") | "N" |

## Local Development

### Setup

**Run only API only (Speedy Debugging purpose)

```bash
# Activate virtual environment
source .venv/bin/activate

cd backend

# If poetry is missing
pip3 install poetry

# Install dependencies
poetry install

# Set environment variables (optional)
export MLFLOW_TRACKING_URI=http://localhost:5000
export LOG_LEVEL=INFO

# Run API locally
PYTHONPATH=src poetry run uvicorn london_housing_ai.api.main_api:app --reload --port 7777
```

**Run all components (docker compose)**

```bash
source .venv/bin/activate
cd backend
docker compose down -v
docker compose build
docker compose up train mlflow postgres
```

**Training**

```bash
# If you want to run with GCP and it doesn't have buckets, run this:
gcloud storage buckets create gs://london-housing-ai-artifacts
gcloud storage buckets create gs://london-housing-ai-data-lake

# Train
docker compose run --rm --no-deps \
  -e MLFLOW_TRACKING_URI=http://mlflow:5000 \
  -e GOOGLE_APPLICATION_CREDENTIALS= \
  train

# Generate trand lookup table
docker compose run --rm --no-deps \
  -e MLFLOW_TRACKING_URI=http://mlflow:5000 \
  -e GOOGLE_APPLICATION_CREDENTIALS= \
  train python -m london_housing_ai.scripts.export_lookup_tables  
```

### Run Tests

```bash
poetry run pytest -v -m "not gcs"
```

### View API Docs

Visit <http://localhost:7777/docs> (Swagger UI)

## Deployment

### Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up
```

Railway will auto-detect Dockerfile and deploy.

### Environment Variables (Railway)

- `MLFLOW_TRACKING_URI`: MLflow server URL
- `PORT`: Auto-set by Railway (default: 8000)

## Architecture

### Feature Enrichment Pipeline

```
User Input: {postcode, property_type, is_new_build, is_leasehold}
    ↓
Postcode Resolver: SW1A 1AA -> Westminster (district)
    ↓
Lookup Tables (from training artifacts):
  - borough_price_trend[district]
  - district_yearly_medians[district + "_" + sold_year] (fallback: prior year/global median)
  - avg_price_last_half[district]
    ↓
Derived Features:
  - advanced_property_type = is_new_build + "_" + property_type
  - property_type_and_tenure = is_leasehold + "_" + property_type
  - property_type_and_district = district + "_" + property_type
  - sold_year, sold_month, date
    ↓
Model Input (13 features):
  [property_type, is_new_build, is_leasehold, district, sold_month,
   advanced_property_type, property_type_and_tenure, property_type_and_district,
   date, sold_year, borough_price_trend, district_yearly_medians, avg_price_last_half]
    ↓
CatBoost Model -> Predicted Price
```

### Model Loading

- Model loaded from MLflow on server startup
- Cached in memory for fast predictions (<50ms)
- Graceful fallback if MLflow unavailable (logs error, returns 503)

### Performance

- **Model inference:** ~20-50ms
- **Postcode enrichment:** ~50-100ms (cached after first lookup)
- **Total latency:** <200ms (target: <300ms)

## Troubleshooting

**Model not loading:**

- Check MLflow tracking URI is correct
- Verify model is registered in MLflow with name "housing_model"
- Check logs: `docker logs <container_id>`

**Postcode enrichment fails:**

- Postcode converting API may be rate-limited (429 error)
- Fallback: Returns None for enriched features, uses defaults

**High latency:**

- Check if aiohttp session is being reused (should be module-level singleton)
- Verify model is cached (not loading on every request)

**Troubleshoot for second compose up:**

- Try deleting `/mlruns` directory, and run train again.

## Tech Decisions

### Why CatBoost?

- Handles categorical features without manual encoding
- Less prone to overfitting than XGBoost
- Fast inference (<50ms for single prediction)

### Why FastAPI?

- Async support (non-blocking postcode enrichment)
- Auto-generated OpenAPI docs
- Type safety (Pydantic)

### Why MLflow?

- Model versioning (easy rollback)
- Experiment tracking (tracked 50+ runs)
- Model registry (production/staging separation)

## Contributing

Not accepting contributions (portfolio project), but feedback welcome!

## Feature Extraction Workflow

When you add a new column extracted from features follow this workflow.

1. define extraction method which adds new column to data frame
2. add the new column to `cleaning.required_cols` and `train.cat_features` or `train.numeric_features` list to `ai_platform/src/configs/config_dataset2.yaml`
