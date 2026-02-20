# London Housing ML Platform

> End-to-end ML system for predicting London housing prices. Built as part of interview prep to demonstrate production ML engineering skills.

## Motivation

While building a London Housing Price ML model, I noticed a lot of repetitive cycles of data cleaning, and frequent changes in data cleaning logic. Because ML model development always involves experimentation and trial-and-error, doing all of this cleaning manually is both time-consuming and inefficient.

This project addresses that pain by automating the data ingestion, cleaning, and feature engineering steps as part of a reproducible, maintainable workflow. My goal is to build out the infrastructure that supports ML experimentation and model serving—making the end-to-end process faster and easier to manage.

## 🚀 Live Demo

- **Frontend:** <https://your-app.vercel.app>
- **Backend API:** <https://your-api.railway.app>
- **API Docs:** <https://your-api.railway.app/docs> (FastAPI Swagger)

## 📊 Project Overview

Predict London housing prices based on:

- Property features (bedrooms, bathrooms, square footage)
- Location (postcode → borough → enriched features)
- Property type (flat, terraced, semi-detached, detached)

**Key Features:**

- Production-ready FastAPI backend with MLflow model serving
- Feature enrichment pipeline (postcode → borough, plus district-level market trend lookup features)
- React + TypeScript frontend with real-time predictions
- Deployed to Railway (backend) + Vercel (frontend)

## 🏗️ Architecture

```
User Input (React)
    ↓
FastAPI Backend
    ├─→ Postcode Service (enrich features)
    ├─→ MLflow Model Registry (load trained model)
    └─→ CatBoost Model (predict price)
    ↓
Prediction + Confidence Interval
```

[Add diagram here using Excalidraw or draw.io]

## 🛠️ Tech Stack

**Backend:**

- FastAPI (Python 3.11)
- CatBoost (regression model)
- MLflow (experiment tracking + model registry)
- Pydantic v2 (request/response validation)
- aiohttp (async postcode enrichment)

**Frontend:**

- React + TypeScript
- Tailwind CSS (styling)
- Vite (build tool)

**Data & Training:**

- Pandas (data cleaning)
- Postgres (storage)
- GCS (partitioned Parquet for reproducibility)

**Deployment:**

- Railway (backend)
- Vercel (frontend)
- Docker (containerization)

## 🚀 Quick Start

### Backend (Docker-first)

```bash
cd backend
docker compose up -d postgres mlflow

# 1) Train and log a model run to MLflow
docker compose run --rm --no-deps \
  -e MLFLOW_TRACKING_URI=http://mlflow:5000 \
  -e GOOGLE_APPLICATION_CREDENTIALS= \
  train

# 2) Export lookup tables and attach them to the latest finished run
docker compose run --rm --no-deps \
  -e MLFLOW_TRACKING_URI=http://mlflow:5000 \
  train python -m london_housing_ai.scripts.export_lookup_tables

# 3) Start API
docker compose up -d api

# 4) Verify
curl http://localhost:7777/health
curl -X POST http://localhost:7777/predict \
  -H "Content-Type: application/json" \
  -d '{"postcode":"SW1A 1AA","property_type":"F"}'
```

- API docs: <http://localhost:7777/docs>
- MLflow UI: <http://localhost:5001>

### Frontend

```bash
cd frontend
npm install
npm run dev
# Visit http://localhost:5173
```

See [backend/README.md](backend/README.md) for detailed API docs.

## 📁 Project Structure

```
london_housing_ai/
├── backend/           # FastAPI application
├── frontend/          # React application
├── notebooks/         # Data exploration (Jupyter)
├── data/             # Sample data
└── docs/             # Architecture diagrams
```

## 🎯 Key Engineering Decisions

### Train/Serve Consistency

**Problem:** The model trains on engineered trend and interaction features, but users only provide a small input payload.

**Solution:**

- API accepts minimal input (`postcode`, `property_type`, `is_new_build`, `is_leasehold`)
- Postcode is resolved to district at request time
- Trend lookup tables are exported from training data and attached as MLflow artifacts
- Serving transformer reconstructs the full model feature vector from user input + lookup artifacts

### Model Loading and Runtime

**Problem:** Loading model/lookup artifacts on every request increases latency and can cause fragile runtime behaviour.

**Solution:**

- Model and transformer are cached in memory per active run
- API loads lookup artifacts from MLflow using the same run ID as the model
- Health endpoint reports run availability plus model/transformer readiness
- Postcode resolution is async and isolated in a dedicated service

### Reproducibility and Traceability

**Problem:** Frequent changes in cleaning/feature logic make experiments hard to reproduce.

**Solution:**

- Persist engineered datasets to Postgres keyed by checksum
- Track params, metrics, and artifacts in MLflow for each run
- Attach lookup-table artifacts to trained runs so serving inputs are traceable to model versions

## 📈 Model Performance

- **Algorithm:** CatBoost Regressor
- **RMSE:** ~£30,000 (vs £80,000 with linear regression)
- **Features:** 15+ (location, property_type, size, derived features)
- **Training Data:** ~50,000 London property sales

## 🔮 Future Improvements

- [ ] Automated data ingestion (Airflow for scheduled retraining)
- [ ] A/B testing framework (gradual model rollout)
- [ ] Data drift monitoring (track feature distributions over time)
- [ ] Semantic caching (reduce inference costs)
- [ ] Mobile-responsive frontend
- [ ] Property comparison tool

## 📝 Interview Story

Built this to transition from pure backend (R3, Meta) to AI-adjacent roles. Key learning: **ML systems are 80% engineering** (data quality, serving, monitoring, reproducibility) and 20% ML theory. This aligns perfectly with my backend strengths.

**What I learned:**

- Train/serve skew is the hardest problem in production ML
- Feature engineering matters more than model choice (CatBoost vs linear: 60% RMSE reduction)
- MLflow is essential for reproducibility (tracked 50+ experiments)
- Production ML is backend engineering with a model in the middle

## 👤 Author

Jenny Yang - [LinkedIn](https://www.linkedin.com/in/jenny-yang-76b405167/) - [GitHub](https://github.com/jee3153)

## 📄 License

MIT
=======
# London Housing AI
A full-stack ML pipeline for predicting property prices in London.

### 🏗️ Architecture
- **Backend:** FastAPI (Python) serving ML predictions.
- **Frontend:** React (TypeScript) for data visualization.
- **Infra:** Terraform for GCS deployment & GitHub Actions for CI.

### 🧠 Key Features
- End-to-end data processing pipeline (Pandas/Scikit-Learn).
- Automated infrastructure as code.
- Containerized environment for consistent local development.
