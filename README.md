# Minimal ML Platform: London Housing Data

A hands-on, end-to-end machine learning platform for tabular data, featuring automated data cleaning, feature engineering, experiment tracking, and model training on real-world London housing data.

## Motivation
While building a London Housing Price ML model, I noticed a lot of repetitive cycles of data cleaning, and frequent changes in data cleaning logic. Because ML model development always involves experimentation and trial-and-error, doing all of this cleaning manually is both time-consuming and inefficient.

This project addresses that pain by automating the data ingestion, cleaning, and feature engineering steps as part of a reproducible, maintainable workflow. My goal is to build out the infrastructure that supports ML experimentation and model serving—making the end-to-end process faster and easier to manage.

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
- [ ] Docker/Cloud deployment

## Setup: docker compose
1. compose up all components.
Change the args of train service in `./compose.yaml` to reflect your own dataset and configuration yaml file.
```bash
docker compose build
```

2. run train
to run train it requires cloud storage to store model artifacts and parquets
if google cloud storage buckets are not found, run:
```bash
gcloud storage buckets create gs://london-housing-ai-artifacts
gcloud storage buckets create gs://london-housing-ai-data-lake
```
runs training, log model to MLflow/artifacts
```bash
docker compose run train
```

3. up api service
```bash
docker compose up api
```

## Setup: Local machine
**Note:** It is recommended to use `docker-compose` for a simpler setup. See the `Setup: docker compose` section below. Use this when you need debugger.

1. Setup postgres
```bash
docker run -p 5432:5432 --name some-postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=password -e POSTGRES_DB=postgres -d postgres:16
```

2. Setup mlflow server
```bash
mlflow server \
  --backend-store-uri postgresql://postgres:password@localhost:5432/postgres \
  --default-artifact-root ./mlruns \
  --host 0.0.0.0
```

## Running test
⚠️ Ensure to locate in root path before running:
```bash
poetry run pytest -v -m "not gcs"
```

## Feature Extraction Workflow
When you add a new column extracted from features follow this workflow.
1. define extraction method which adds new column to data frame
2. add the new column to `cleaning.required_cols` and `train.cat_features` or `train.numeric_features` list to `ai_platform/src/configs/config_dataset2.yaml`

## Troubleshoot tips
If you are having failure for second compose up,
try deleting `/mlruns` directory, and run train again.

## Local terraform deployment
##### Before everything
remove any existing buckets
```bash
gsutil rm -r gs://london-housing-ai-artifacts
gsutil rm -r gs://london-housing-ai-data-lake
```

If buckets already exist:
```bash
terraform import google_storage_bucket.data_lake_bucket london-housing-ai-data-lake
terraform import google_storage_bucket.model_artifacts_bucket london-housing-ai-artifacts
```

Check whether:
- `terraform-network` already exists or not
- `london-housing-db-instance` already exists or not
- `terraform-instance` already exists or not
```bash
gcloud compute networks list
gcloud sql instances list
gcloud storage buckets list
gcloud compute instances list
```

If exists:
```bash
terraform import google_compute_network.vpc_network projects/abiding-sunset-333516/global/networks/terraform-network
terraform import module.database.google_sql_database_instance.postgres projects/abiding-sunset-333516/instances/london-housing-db-instance
terraform import google_compute_instance.vm_instance projects/abiding-sunset-333516/zones/us-central1-a/instances/terraform-instance
```

Verify import success:
```bash
terraform state list
```

Deploy
```bash
terraform init
terraform apply -var-file="terraform.tfvars" -auto-approve
```

Expose mlflow tracking uri
```bash
export MLFLOW_TRACKING_URI=$(terraform output -raw mlflow_tracking_uri)
```

Manual clean up
```bash
gcloud iam service-accounts delete mlflow-sa@abiding-sunset-333516.iam.gserviceaccount.com --quiet
gcloud sql instances delete london-housing-db-instance
gcloud storage rm -r gs://london-housing-ai-artifacts
gcloud storage rm -r gs://london-housing-ai-data-lake
gcloud compute networks delete london-housing-vpc
```

## Progress
🧩 Recap: What you already have

| Component	| Purpose |	Status |
|-----------|---------|--------|
| Postgres DB |	Used by MLflow as backend store (experiments, runs metadata)|	✅ Deployed |
| VPN + VPC | network	Networking & security isolation for your resources	| ✅ Deployed |
| VM instance	| Compute node to host MLflow, training jobs, or Airflow | ✅ Deployed |
| GCS buckets | One for parquet data (“silver” layer) and one for model artifacts	| ✅ Deployed |

### Distinction GCS bucket vs MLflow server
GCS buckets: hold raw and binary data
MLflow server: hold structured experiment tracking metadata e.g. run Ids, start/end time, model version num, parameters used, metrics, artifact URIs that point to GCS

-> MLflow server ties things together into a searchable experiment history with APIs and UI

## What is MLFlow?
it's a **tracking** and **model registry system**.

🟢 What MLflow does
| Layer | Description | Who uses it |
|-------|-------------|-------------|
| Tracking UI (frontend) | A simple web interface (usually on port `5000`) where you can browse experiment runs, metrics, and parameters. | Data scientists, ML engineers |
| Tracking API | A Python API (`mlflow.start_run`, `mlflow.log_param`, `mlflow.log_metric`, etc.) that your training code calls to log metadata. | Your training code |
| Artifact management | Keeps references (URIs) to models, datasets, plots, checkpoints stored in GCS or S3. | ML engineers |
| Model Registry | Lets you promote models from "staging" → "production" and keep version history. | ML + Ops teams |
| REST API | Programmatic interface for automation (CI/CD, retraining, deployment scripts). | DevOps, automation |

🔴 What MLflow does not do

| ❌ | It doesn’t ingest raw data or run training jobs. That’s your own pipeline’s job (e.g., Airflow, Ray, custom scripts). |

| ❌ | It doesn’t schedule or orchestrate tasks (like Airflow or Prefect). |

| ❌ | It doesn’t deploy models to production (unless you integrate MLflow Models with tools like Seldon, BentoML, or Vertex AI). |

In bigger company where there are some user bases, they would have data pipeline. 
But since I don't have any production user input, nor production system, data will be pulled manually from Kaggle or Google dataset search, or govenment datasets. 
Hence, no datapipeline for this project.

## Big picture map of data flow
```pgsql
Users / Production Systems
          │
          ▼
    (Raw Events / Logs)
          │
          ▼
   ┌────────────────────────────────┐
   │        Data Pipeline           │
   │                                │
   │ 1. Ingest / Collect            │
   │ 2. Store in Data Lake/Warehouse│
   │ 3. Transform / Clean / Validate│
   │ 4. Build analytical tables     │
   └────────────────────────────────┘
          │
          ▼
   ┌────────────────────────────────┐
   │         ML Pipeline            │
   │                                │
   │ 1. Feature engineering         │
   │ 2. Model training & tuning     │
   │ 3. Model evaluation & registry │
   │ 4. Model deployment / serving  │
   └────────────────────────────────┘
          │
          ▼
   (Predictions → Products)
```

### 🧩 1. What is a Data Pipeline

A data pipeline is everything that ensures raw data gets ingested, cleaned, and made available for downstream use — not necessarily for ML only (could also be dashboards, BI, etc.).

**Scope:**
- From data source (e.g., app logs, API, sensors, CRM)
- To data warehouse or data lake (e.g., Snowflake, BigQuery, S3, GCS)
- Includes all ETL/ELT steps (Extract, Transform, Load)
- Includes data validation, quality checks, and partitioning/versioning

**Example technologies:**
- Ingestion: Kafka, Airbyte, Fivetran, Pub/Sub
- Transformation: dbt, Spark, Dataflow, Beam
- Storage: BigQuery, Snowflake, Delta Lake, GCS
- Orchestration: Airflow, Dagster, Prefect

**Output:**
Cleaned, reliable, analytics-ready data tables or Parquet files.

### 🧠 2. What is an ML Pipeline

An ML pipeline starts after the data pipeline ends.
It consumes the cleaned, transformed data from the warehouse or “feature store,” and focuses on model creation, evaluation, and deployment.

**Scope:**
- Reads data from data warehouse or data lake
- Splits into training/validation/test sets
- Performs feature engineering (scaling, encoding, etc.)
- Trains and evaluates models
- Logs metrics and artifacts (e.g., MLflow)
- Pushes final model to registry or serving endpoint

**Example technologies:**
- feature engineering: Pandas, Spark ML, Feast (Feature Store)
- Training: scikit-learn, XGBoost, TensorFlow, PyTorch
- Tracking: MLflow
- Orchestration: Airflow, Kubeflow, Vertex AI Pipelines
- Deployment: Docker, FastAPI, Cloud Run, Seldon

**Output:**
Versioned model artifacts and model registry entries.

#### Production ML Architecture Overview
```pgsql
         ┌──────────────────────────────┐
         │     User & External Data     │
         │ (apps, APIs, logs, Kaggle)   │
         └──────────────┬───────────────┘
                        │
                        ▼
          ┌───────────────────────────┐
          │      Ingestion Layer      │
          │  (Fivetran, Airbyte, etc) │
          └─────────────┬─────────────┘
                        │
                        ▼
         ┌───────────────────────────────┐
         │      Raw Data Storage         │
         │ (e.g., GCS “raw”, S3, bronze) │
         └──────────────┬────────────────┘
                        │
                        ▼
         ┌───────────────────────────────┐
         │   Data Cleaning & Transform   │
         │ (dbt / Spark / Ray / Pandas)  │
         └──────────────┬────────────────┘
                        │
                        ▼
         ┌───────────────────────────────┐
         │   Data Warehouse / Data Lake  │
         │ (BigQuery, Snowflake, GCS)    │
         └──────────────┬────────────────┘
                        │
                        ▼
     ┌─────────────────────────────────────┐
     │          ⛳ HAND-OFF POINT          │
     │  ("clean, versioned dataset ready") │
     └─────────────────────────────────────┘
                        │
                        ▼
        ┌──────────────────────────────┐
        │        ML Pipeline           │
        │  Feature Eng → Train → Eval  │
        │ (MLflow, sklearn, CatBoost)  │
        └───────────────┬──────────────┘
                        │
                        ▼
       ┌───────────────────────────────┐
       │        MLflow Tracking        │
       │  (metrics, params, artifacts) │
       │     backend=Postgres + GCS    │
       └────────────────┬──────────────┘
                        │
                        ▼
       ┌────────────────────────────────┐
       │     Model Registry / Serving   │
       │ (MLflow Model Registry, API)   │
       └────────────────────────────────┘
```