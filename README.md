# Minimal ML Platform: London Housing Data

A hands-on, end-to-end machine learning platform for tabular data, featuring automated data cleaning, feature engineering, experiment tracking, and model training on real-world London housing data.

## Motivation
While building a London Housing Price ML model, I noticed a lot of repetitive cycles of data cleaning, and frequent changes in data cleaning logic. Because ML model development always involves experimentation and trial-and-error, doing all of this cleaning manually is both time-consuming and inefficient.

This project addresses that pain by automating the data ingestion, cleaning, and feature engineering steps as part of a reproducible, maintainable workflow. My goal is to build out the infrastructure that supports ML experimentation and model serving—making the end-to-end process faster and easier to manage.

## Features
- [x] Automated data loading and cleaning from CSV
- [x] Persist cleaned data to database (SQLite)
- [x] Feature engineering (postcode, house types, etc.)
- [x] Model training and evaluation
- [x] Experiment tracking with MLflow
- [ ] Model versioning/registry
- [ ] Model serving (API)
- [ ] Docker/Cloud deployment

## Setup: Local machine
1. Setup postgres
```bash
docker run -p 5432:5432 -e POSTGRES_PASSWORD=password -d mypostgres
```

2. Setup mlflow server
```bash
mlflow server \
  --backend-store-uri postgresql://postgres:password@localhost:5432/mypostgres \
  --default-artifact-root ./mlruns \
  --host 0.0.0.0
```

## Setup: docker compose
1. compose up all components
```bash
docker compose build
```

2. run train
runs training, log model to MLflow/artifacts
```bash
docker compose run train
```

3. up api service
```bash
docker compose up api
```

## Troubleshoot tips
If you are having failure for second compose up,
try deleting `/mlruns` directory, and run train again.