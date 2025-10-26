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
pytest
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



