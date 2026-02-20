# London Housing Frontend

React + TypeScript dashboard for:
- Model performance visualization from MLflow runs
- Price prediction via backend API

## Requirements

- Node.js 20+
- `pnpm` (recommended package manager for this repo)

## Setup

```bash
cd frontend
pnpm install
```

## Run Locally

```bash
pnpm dev
```

App runs at `http://localhost:5173`.

## Environment Variables

Create `.env` (or `.env.local`) in `frontend/`:

```bash
VITE_API_URL=http://localhost:7777
```

If `VITE_API_URL` is not set, frontend falls back to `http://localhost:7777`.

## Scripts

- `pnpm dev`: start Vite dev server
- `pnpm build`: type-check + production build
- `pnpm preview`: preview production build
- `pnpm lint`: run ESLint

## API Contract Used by Frontend

- `GET /mlflow/runs`  
  Expected shape: array of runs with `data` and `info`:
  `[{ data: { metrics, params, tags }, info: { run_id, ... } }]`

- `POST /predict`  
  Returns `predicted_price`, `confidence_interval`, `model_version`, `features_used`, `run_id`.

## Troubleshooting

- If model cards are empty: verify backend `/mlflow/runs` returns numeric metrics (`validation_rmse`, `validation_r2`, `validation_mse`, `train_rmse`, `test_rmse`).
- If prediction button style looks wrong: clear browser cache and restart dev server.
- If API calls fail in devtools: verify `VITE_API_URL` and backend CORS settings.
