# 🎬 Movie Box Office Revenue Forecast

A full-stack web application that predicts **worldwide box-office revenue** for any movie using a **Deep Neural Network** (TensorFlow/Keras) trained on the **TMDB 5000** dataset — built as a college mini-project.

| Layer | Technology |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Recharts |
| **Backend** | FastAPI, SQLAlchemy, SQLite, Pydantic v2 |
| **ML Pipeline** | TensorFlow / Keras DNN, Scikit-learn, XGBoost, feature engineering |
| **Deployment** | Render (two-service blueprint: API + static site) |

---

## 🔗 Live Demo

| Service | URL |
|---|---|
| Frontend (React) | https://movie-box-office-frontend.onrender.com |
| Backend API (FastAPI) | https://movie-box-office-backend.onrender.com |

> The Render free tier sleeps after ~15 min idle. The first request after idle takes ~30–60 s to wake the service.

---

## ✨ Features

| Page / Area | Description |
|---|---|
| 🎯 **Forecast** | Form-driven single prediction — budget, runtime, genres, release window, cast & crew, audience signals |
| 📦 **Batch Prediction** | Predict many movies at once via JSON array or CSV upload |
| 🔍 **Explainability** | Per-feature sensitivity analysis — *why* the model predicted this number |
| 📈 **Analytics** | Revenue by year, genre, release month, budget-vs-revenue scatter, top grossers |
| 🎞️ **Movie Explorer** | Search / filter / sort / paginate the 3,164-movie database |
| 🧠 **Model Hub** | DNN vs baseline metrics, training curves, feature importance, dataset split info |
| ⚙️ **Settings** | System config, API base URL, feature list, retrain trigger (dev only) |
| ♻️ **Retraining** | One-click retrain from the UI (`ALLOW_RETRAIN=false` in production) |

---

## 🧠 The Model

### Task

Regression on **`log1p(revenue)`** — revenue spans five orders of magnitude so the log transform makes the target near-Gaussian and stabilises the regression.

### Architecture

```
Input (34 features)
  → Dense(512, ReLU) + BatchNorm + Dropout(0.35)
  → Dense(256, ReLU) + BatchNorm + Dropout(0.30)
  → Dense(128, ReLU) + BatchNorm + Dropout(0.25)
  → Dense(64,  ReLU) + BatchNorm + Dropout(0.20)
  → Dense(1,  linear)                         ← log1p(revenue)
```

| Hyper-parameter | Value |
|---|---|
| Optimizer | Adam (lr 1e-3) |
| LR schedule | ReduceLROnPlateau (patience 8, factor 0.5, min 1e-5) |
| Loss | Huber (delta = 1.0) |
| Metric | MAE |
| Regularisation | L2 1e-4 + Dropout (per layer) |
| Early stopping | Patience 25 on val loss |
| Epochs | Up to 300 (early stopped at ~84–109 in practice) |
| Batch size | 128 |

### Features (34)

**16 engineered numerics**

| Feature | Description |
|---|---|
| `budget_log` | `log1p(budget)` |
| `budget_per_runtime` | `budget / runtime` (spend intensity) |
| `runtime` | Runtime in minutes |
| `popularity` | TMDB popularity score |
| `vote_average` | Average user rating |
| `vote_count_log` | `log1p(vote_count)` (audience reach) |
| `release_year` | Calendar year |
| `release_month` | 1–12 |
| `release_quarter` | 1–4 |
| `release_weekday` | 0=Mon … 6=Sun |
| `genre_count` | Number of genres attached |
| `cast_size` | Number of lead actors |
| `cast_star_power` | Average rating of lead actors |
| `director_frequency` | How many films the director has in the dataset |
| `company_frequency` | How many films the production company has |
| `language_is_en` | 1 if English, else 0 |

**18 genre one-hot flags** — Drama, Comedy, Thriller, Action, Adventure, Romance, Crime, Science Fiction, Family, Horror, Fantasy, Mystery, Animation, History, War, Music, Western, Documentar

### Dataset

- **Source**: TMDB 5000 Movies + Credits
- **Cleaned rows**: 3,165 (budget > 0, revenue > 0, runtime 30–400 min, status = Released)
- **Split**: 70 / 15 / 15 (stratified by revenue quartile)
- **Preprocessing**: StandardScaler on numerics, one-hot on genres; `company_frequency`, `director_frequency`, `cast_star_power` are **fit on train only** then merged (no leakage)

### Test performance (held-out 476 movies)

| Model | R² (log) | RMSE (log) | MAE (revenue) |
|---|---|---|---|
| **Deep Neural Network** | **0.685** | 1.159 | $55.4 M |
| Linear Regression | 0.690 | 1.150 | $53.8 M |
| Random Forest | 0.651 | 1.221 | $51.3 M |
| Extra Trees | 0.636 | 1.246 | $51.5 M |
| XGBoost | 0.632 | 1.254 | $50.0 M |
| Gradient Boosting | 0.632 | 1.254 | $50.6 M |
| AdaBoost | 0.520 | 1.432 | $68.8 M |
| K-Nearest Neighbors | 0.490 | 1.475 | $66.3 M |
| Decision Tree | 0.228 | 1.815 | $76.2 M |

The DNN is the best **non-linear** model on log-space RMSE/MAE. It ties Linear Regression on R² while being more robust in the original revenue space — it does not overshoot blockbusters the way trees and the linear model do.

### Performance labels

Predicted revenue is classified against budget via a multiplier:

| Label | Revenue / Budget |
|---|---|
| `FLOP` | < 1.0× |
| `AVERAGE` | 1.0× – 2.0× |
| `HIT` | 2.0× – 4.0× |
| `SUPER_HIT` | 4.0× – 8.0× |
| `BLOCKBUSTER` | ≥ 8.0× |

> **Disclaimer**: Predictions are statistical estimates. Confidence reflects training accuracy + input completeness, not a probability of success. Use the 95% range, not the point estimate.

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Version |
|---|---|
| Python | **3.12** (required for TensorFlow 2.19+ wheels on Windows) |
| Node.js | ≥ 18 |
| Git | any recent version |

### 1. Clone the repository

```bash
git clone https://github.com/dhana123-m/Movie-box-revenue-forecast.git
cd Movie-box-revenue-forecast
```

### 2. Backend (FastAPI + LiteRT)

```bat
cd backend
py -3.12 -m venv .venv
.venv\Scripts\pip install --upgrade pip
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Or simply run `run_backend.bat` (uses a pre-existing `.venv`).

> `requirements.txt` holds the slim serve-time stack (LiteRT instead of
> TensorFlow); `requirements-dev.txt` adds TensorFlow, XGBoost and plotting
> for training/tuning/tests. Use `-dev` locally, plain for cloud deploys.

- **Swagger UI**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/api/health

> On first start the API auto-seeds the SQLite database from the committed processed CSV (`backend/data/processed/tmdb_5000_processed.csv`) and loads the trained model.

### 3. Frontend (React + Vite)

```bat
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the Vite dev proxy forwards all `/api` requests to the backend on port 8000.

### 4. Quick-start scripts

| Script | What it does |
|---|---|
| `run_backend.bat` | Starts the FastAPI backend on port 8000 |
| `run_frontend.bat` | Starts the Vite dev server on port 5173 |

### 5. Retraining the model (optional)

```bat
cd backend
.venv\Scripts\python training\train.py          :: full pipeline: feature eng → train → evaluate
.venv\Scripts\python training\hyperparameter_tuning.py  :: 11-trial grid search
```

Or click **Retrain** in the Settings page (requires `ALLOW_RETRAIN=true`, which is the default in development).

---

## 🖥️ Single-Port Production Mode

After building the frontend the FastAPI server also serves it on the **same port** — one origin, no CORS, no proxy:

```bat
cd frontend && npm run build
cd ..\backend
.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
:: open http://localhost:8000
```

FastAPI mounts `/assets` statically, returns `index.html` for any non-`/api` route (SPA fallback), and wraps every `/api/*` error in the standard envelope.

Disable by setting `FRONTEND_DIST_PATH` to a non-existent folder in `backend/.env`.

---

## ☁️ Cloud Deployment (Render, free)

The repo ships a [Render Blueprint](https://render.com/docs/blueprint-spec) (`render.yaml`) that deploys **two separate services**:

| Service | Type | Description |
|---|---|---|
| `movie-box-office-backend` | Web (Python) | FastAPI + LiteRT (.tflite) API |
| `movie-box-office-frontend` | Static Site | React SPA that calls the API |

### Deploy steps

1. Push the repository to GitHub.
2. On Render: **Dashboard → New → Blueprint**, select the repo.
3. Render creates both services and wires them via `VITE_API_BASE_URL` / `CORS_ORIGINS`.
4. Open the frontend URL — the backend URL is the API base.

### Deployment facts

| Topic | Detail |
|---|---|
| **Model artifacts** | Committed to git; loaded on boot. No re-training on the server. |
| **Database** | SQLite on Render's ephemeral disk; auto-seeds from committed CSV. Resets on redeploy. |
| **CORS** | Backend allows the frontend origin via `CORS_ORIGINS`. Dev origins (`localhost:5173`) are always allowed. |
| **SPA routing** | Static site ships `frontend/public/_redirects` (`/* → /index.html`, LF-only enforced by `.gitattributes`). |
| **Retraining** | Disabled in production (`ALLOW_RETRAIN=false`). |
| **Build** | Slim serve-time stack (LiteRT, no TensorFlow) — installs in well under a minute on the free tier. |
| **Cold start** | Free-tier sleeps after ~15 min idle. First request takes ~30–60 s to wake. |

---

## 🐙 Frontend on GitHub Pages (free)

The React frontend also deploys to **GitHub Pages** via
`.github/workflows/deploy-frontend.yml`, calling the Render backend.

| Topic | Detail |
|---|---|
| Live URL | `https://dhana123-m.github.io/Movie-box-revenue-forecast/` |
| API base | `https://movie-box-office-forecast.onrender.com/api` (baked at build time) |
| SPA routing | `index.html` is copied to `404.html` so client-side routes work on deep links |
| Base path | Built with `VITE_BASE_PATH=/Movie-box-revenue-forecast/` for the project-site sub-path |
| CORS | The backend always allows the Pages origin (`EXTRA_CORS_ORIGINS` in `backend/app/main.py`) |

### One-time setup

1. Repo → **Settings → Pages** → **Build and deployment → Source: GitHub Actions**.
   *(Private repos need GitHub Pro — free via the Student Developer Pack.)*
2. Push to `main` (or run the workflow manually via **Actions → Deploy frontend → Run workflow**).
3. Open the URL above. The backend auto-deploys the matching CORS fix on Render.

---

## ▲ Cloud Deployment (Vercel, free)

The backend can also run on **Vercel** as a serverless Python function
(`backend/api/index.py` + `backend/vercel.json`).

### How it works

| Concern | Solution |
|---|---|
| Entry point | `api/index.py` exposes the FastASGI `app`; `vercel.json` rewrites every route to it |
| Lifespan events | Vercel may not fire them → `ensure_initialized()` (tables + model + seed) is idempotent and called at import; warm requests skip it instantly |
| Writable filesystem | Only `/tmp` is writable → `DATABASE_URL=sqlite:////tmp/movie_box.db`, re-seeded per cold start |
| Bundle size | Serving uses **LiteRT** (`ai-edge-litert`) on the committed 0.77 MB `.tflite` model instead of the ~600 MB TensorFlow wheel → the whole bundle stays well under the standard 500 MB function limit |
| Cold start | A few seconds; no TF import, tiny interpreter load (`maxDuration: 60` for safety) |
| Config defaults | Applied in `api/index.py` before settings load; dashboard env vars always win |

### Model serving: LiteRT vs TensorFlow

The trained Keras model is converted once with
`python scripts/convert_to_tflite.py` (requires `requirements-dev.txt`)
into `backend/models/revenue_model.tflite`, which is committed to git.
Parity against the `.keras` original is < 0.001 % on revenue predictions.
At runtime `ModelService` prefers LiteRT and falls back to TensorFlow/Keras
when only the `.keras` artifact + full TF are available (e.g. local dev).
Training dependencies live in `backend/requirements-dev.txt`.

### Deploy steps

1. Push this repository to GitHub.
2. On [vercel.com](https://vercel.com): **Add New → Project**, import the repo.
3. Configure the project:
   - **Root Directory**: `backend`
   - Framework Preset: **Other** (defaults are fine)
4. Deploy. The function builds from `backend/requirements.txt` and serves all
   routes under one URL (e.g. `https://<project>.vercel.app`).
5. Verify: open `https://<project>.vercel.app/api/health`.

### Notes

- Retraining is force-disabled (`ALLOW_RETRAIN=false`).
- To call the API from a browser app hosted elsewhere (Vercel frontend, Render,
  localhost), add that origin to the `CORS_ORIGINS` environment variable in the
  Vercel project settings, e.g.
  `https://your-frontend.vercel.app,http://localhost:5173`.
- SQLite is ephemeral per instance — fine for the demo dataset, not for
  production writes. Swap `DATABASE_URL` to Postgres for persistence.

---

## 📁 Project Structure

```
Movie-box-revenue-forecast/
│
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app: lifespan, CORS, routers, SPA mount
│   │   ├── config.py                # env-driven settings (pydantic-settings)
│   │   ├── database.py              # SQLAlchemy engine / session
│   │   ├── models/                  # ORM models (Movie, Prediction, ModelMetadata)
│   │   ├── schemas/                 # Pydantic request/response contracts
│   │   │   ├── predict.py           # PredictRequest, BatchPredictItem, PredictResponse
│   │   │   ├── movie.py             # MovieSummary, MovieDetail, MovieListResponse
│   │   │   └── analytics.py         # OverviewStats, GenreStat, YearlyStat …
│   │   ├── ml/
│   │   │   ├── preprocessor.py      # RevenuePreprocessor (fit/transform/inverse)
│   │   │   ├── genres.py            # canonical genre vocabulary
│   │   │   ├── performance.py       # FLOP … BLOCKBUSTER classifier
│   │   │   └── explain.py           # perturbation-based sensitivity explainer
│   │   ├── services/
│   │   │   ├── model_service.py     # singleton: loads Keras model + preprocessor
│   │   │   ├── prediction_service.py # single / batch / CSV prediction logic
│   │   │   ├── analytics_service.py # overview, genres, yearly, scatter, top-movies
│   │   │   ├── db_service.py        # seed_from_csv, CRUD helpers
│   │   │   └── training_service.py  # retrain trigger + status
│   │   ├── routes/
│   │   │   ├── health.py            # GET /api/health
│   │   │   ├── predict.py           # POST /api/predict, /batch, /csv
│   │   │   ├── analytics.py         # GET /api/analytics/*
│   │   │   ├── movies.py            # GET /api/movies, /movies/{id}, /filters/summary
│   │   │   ├── model_info.py        # GET /api/model/info
│   │   │   └── training.py          # GET/POST /api/training/*
│   │   └── utils/                   # error-envelope helpers, formatters
│   │
│   ├── training/
│   │   ├── feature_engineering.py   # raw CSV → cleaned/featured CSV
│   │   ├── model.py                 # build_dnn(), describe_architecture()
│   │   ├── train.py                 # full pipeline: feature eng → train → evaluate
│   │   ├── hyperparameter_tuning.py # 11-trial DNN grid search
│   │   └── evaluate.py              # baseline models + evaluation plots
│   │
│   ├── scripts/
│   │   ├── download_data.py          # downloads TMDB 5000 CSVs
│   │   └── convert_to_tflite.py      # .keras → .tflite + parity checks
│   ├── tests/                       # pytest suite (16 tests, isolated DB)
│   │   ├── conftest.py              # test fixtures: temp DB, TestClient
│   │   ├── test_ml.py               # model loading, predict, explain, thresholds
│   │   └── test_api.py              # endpoint integration tests
│   │
│   ├── data/
│   │   ├── raw/                     # tmdb_5000_movies.csv, credits.csv
│   │   └── processed/               # tmdb_5000_processed.csv (committed)
│   │
│   ├── models/                      # trained artifacts (committed to git)
│   │   ├── revenue_model.keras      # Keras DNN (~2.4 MB, training master copy)
│   │   ├── revenue_model.tflite     # LiteRT export (~0.8 MB, serving runtime)
│   │   ├── preprocessor.pkl         # fitted RevenuePreprocessor
│   │   ├── metrics.json             # test metrics (DNN + baselines)
│   │   ├── model_metadata.json      # training date, TF version, config
│   │   ├── feature_config.json      # feature names + numeric columns
│   │   └── evaluation/              # training_history.json, plots, tuning results
│   │
│   ├── api/index.py                 # Vercel serverless entrypoint
│   ├── vercel.json                  # Vercel routes/function config
│   ├── requirements.txt             # slim serve-time deps (Render/Vercel)
│   ├── requirements-dev.txt         # adds TensorFlow/training/test tooling
│   ├── .env.example
│   └── movie_box.db                 # SQLite (auto-created, not committed)
│
├── frontend/
│   ├── public/
│   │   └── _redirects               # SPA fallback (/* → /index.html, LF-only)
│   ├── src/
│   │   ├── services/api.ts          # typed API client (reads VITE_API_BASE_URL)
│   │   ├── hooks/useApi.ts          # data-fetching hook
│   │   ├── types/index.ts           # TypeScript interfaces
│   │   ├── components/
│   │   │   ├── layout/Layout.tsx    # sidebar, topbar, health badge
│   │   │   ├── charts/             # reusable Recharts wrappers
│   │   │   ├── forecast/           # PredictionForm + PredictionResultCard
│   │   │   └── ui/                 # Button, Card, Input, Badge, etc.
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── ForecastPage.tsx
│   │   │   ├── AnalyticsPage.tsx
│   │   │   ├── MovieExplorerPage.tsx
│   │   │   ├── ModelPerformancePage.tsx
│   │   │   └── SettingsPage.tsx
│   │   └── utils/format.ts         # currency / number formatters
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── package.json
│   └── .env.example
│
├── notebooks/
│   └── exploratory_analysis.ipynb   # Jupyter notebook: data exploration + visualisations
│
├── demo_movies.csv                  # 10 sample movies for CSV-batch testing
├── render.yaml                      # Render blueprint (backend + frontend)
├── .gitattributes                   # LF enforcement for _redirects
├── .gitignore
├── run_backend.bat                  # quick-start backend
├── run_frontend.bat                 # quick-start frontend
└── README.md
```

---

## 🔌 API Reference

All responses use a consistent envelope:

```json
{
  "success": true,
  "data": { ... },
  "message": null,
  "error": null
}
```

Errors:

```json
{
  "success": false,
  "data": null,
  "message": "Something went wrong.",
  "error": { "code": "VALIDATION_ERROR", "message": "...", "fields": { "budget": "..." } }
}
```

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness probe, model + DB status |
| `GET` | `/api/model/info` | Model metadata, thresholds, feature list, dataset info |
| `POST` | `/api/predict` | Single-movie prediction |
| `POST` | `/api/predict/batch` | Batch prediction from a JSON array |
| `POST` | `/api/predict/csv` | Batch prediction from an uploaded CSV file |
| `GET` | `/api/analytics/overview` | Global stats (total movies, avg budget/revenue, top genres) |
| `GET` | `/api/analytics/genres` | Per-genre revenue statistics |
| `GET` | `/api/analytics/yearly` | Per-year revenue (`?min_year=2000`) |
| `GET` | `/api/analytics/budget-vs-revenue` | Scatter data (`?limit=200`) |
| `GET` | `/api/analytics/top-movies` | Highest grossing films (`?limit=10`) |
| `GET` | `/api/analytics/release-months` | Monthly release performance |
| `GET` | `/api/analytics/genres-by-year` | Genre × year breakdown |
| `GET` | `/api/movies` | Explorer list (pagination + filters) |
| `GET` | `/api/movies/{id}` | Single movie detail |
| `GET` | `/api/movies/filters/summary` | Dropdown options for the explorer |
| `GET` | `/api/training/metrics` | DNN + all baseline metrics, training history, feature importance |
| `GET` | `/api/training/status` | Background retraining job status |
| `POST` | `/api/retrain` | Trigger retraining (dev only) |
| `GET` | `/docs` | Swagger UI (auto-generated) |

### Single prediction — request

```json
{
  "title": "Avatar 3",
  "budget": 250000000,
  "runtime": 192,
  "genres": ["Action", "Adventure", "Science Fiction"],
  "release_month": 12,
  "release_day": 18,
  "release_year": 2026,
  "production_company": "20th Century Fox",
  "director": "James Cameron",
  "lead_actors": ["Sam Worthington", "Zoe Saldana"],
  "rating": 8.2,
  "vote_count": 50000,
  "popularity": 150.0,
  "language": "en"
}
```

### Single prediction — response (abbreviated)

```json
{
  "success": true,
  "data": {
    "title": "Avatar 3",
    "predicted_revenue": 598234000,
    "predicted_revenue_inr": "₹4,965 Cr",
    "performance_category": "SUPER_HIT",
    "budget": 250000000,
    "revenue_budget_ratio": 2.39,
    "confidence_score": 82.7,
    "expected_range": { "low": 120000000, "high": 2400000000 },
    "model": "Deep Neural Network",
    "model_version": "1.0.0",
    "contributions": [
      { "feature": "vote_count_log", "contribution": 3.2, "direction": "positive" },
      { "feature": "budget_log", "contribution": 2.1, "direction": "positive" }
    ],
    "disclaimer": "Predictions are estimates based on historical patterns …"
  }
}
```

### Batch prediction — request

Send a plain JSON array (no wrapper):

```json
[
  { "title": "Movie A", "budget": 150000000, "runtime": 140, "genres": ["Action"], ... },
  { "title": "Movie B", "budget": 20000000, "runtime": 100, "genres": ["Drama"], ... }
]
```

### CSV format

| Column | Required | Notes |
|---|---|---|
| `title` | ✅ | |
| `budget` | ✅ | Positive number |
| `runtime` | ✅ | Minutes |
| `genres` | | Pipe-separated: `Action\|Adventure` |
| `release_month` | | 1–12 |
| `release_day` | | 1–31 |
| `release_year` | | e.g. 2026 |
| `production_company` | | Studio name |
| `director` | | |
| `lead_actors` | | Pipe-separated: `Tom Hardy\|Cillian Murphy` |
| `rating` | | 0.0–10.0 |
| `vote_count` | | |
| `popularity` | | TMDB popularity |
| `language` | | ISO 639-1 code (default: `en`) |

See `demo_movies.csv` (10 sample movies) for a ready-to-upload example.

---

## 🧪 Testing

### Backend — 16 tests

```bat
cd backend
.venv\Scripts\python -m pytest -q
```

Tests run against an isolated temporary SQLite database (created via `DATABASE_URL` env var in `conftest.py`).

| Test file | Coverage |
|---|---|
| `test_ml.py` | Model loading, single predict, batch predict, CSV predict, explain, thresholds, error handling |
| `test_api.py` | Health endpoint, analytics endpoints, movies CRUD, training metrics, schema validation |

### Frontend — 6 tests

```bat
cd frontend
npm test          # Vitest + jsdom
npm run build     # TypeScript check (tsc --noEmit) + production build
```

---

## ⚙️ Configuration

Copy `backend/.env.example` to `backend/.env` and edit as needed:

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | `development` or `production` |
| `DATABASE_URL` | `sqlite:///movie_box.db` | Database connection string |
| `MODEL_PATH` | `models/revenue_model.keras` | Path to the trained Keras model |
| `PREPROCESSOR_PATH` | `models/preprocessor.pkl` | Path to the fitted preprocessor |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Comma-separated allowed origins |
| `ALLOW_RETRAIN` | `true` | Enable the `/api/retrain` endpoint |
| `INR_PER_USD` | `83.0` | Exchange rate for ₹ display |
| `MAX_UPLOAD_BYTES` | `5242880` | Max CSV upload size (5 MB) |
| `LEARNING_RATE` | `0.001` | DNN learning rate |
| `EPOCHS` | `300` | Max training epochs |
| `BATCH_SIZE` | `128` | Training batch size |

For the **frontend**, copy `frontend/.env.example` to `frontend/.env`:

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | Backend API URL (e.g. `http://localhost:8000/api`). Leave blank for dev — the Vite proxy handles it. |

---

## 🔬 ML Experiments

All experiment artifacts are generated under `backend/models/evaluation/`.

### Hyper-parameter tuning

`backend/training/hyperparameter_tuning.py` sweeps **11 configurations** over layer width/depth, dropout strength, L2 and learning rate, scoring each by validation MAE.

```bat
cd backend
.venv\Scripts\python training\hyperparameter_tuning.py
```

Top results (validation MAE, lower is better):

| Config | Dropout | lr | L2 | Val MAE |
|---|---|---|---|---|
| **512 → 256 → 128 → 64** ✅ | 0.35 / 0.30 / 0.25 / 0.20 | 1e-3 | 1e-4 | **0.7209** |
| 256 → 192 → 128 → 64 → 32 | 0.30 / 0.25 / 0.20 / 0.15 / 0.15 | 1e-3 | 1e-4 | 0.7319 |
| 256 → 128 → 64 → 32 | 0.30 / 0.25 / 0.20 / 0.20 | 3e-3 | 1e-4 | 0.7457 |
| 256 → 128 → 64 → 32 (baseline) | 0.30 / 0.25 / 0.20 / 0.20 | 1e-3 | 1e-4 | 0.7702 |

The winning configuration became the production default, lifting test R²(log) from **0.653 → 0.685** and cutting test MAE from **$66.2 M → $55.4 M**.

### Feature importance

Permutation importance on the held-out test set (drop in MAE when each feature is shuffled):

1. `vote_count_log` — audience reach
2. `budget_log` — production scale
3. `budget_per_runtime` — spend intensity
4. `popularity` — pre-release buzz
5. `release_year` + release-season features
6. Genre flags: `Family`, `Science Fiction`, `Romance`, `Documentary` …

Visualised live on the **Model Performance** page.

### Baselines

Eight classical regressors compete with the DNN on the same split and feature matrix: Linear Regression, Random Forest, Gradient Boosting, XGBoost, Extra Trees, AdaBoost, K-Nearest Neighbors, Decision Tree.

---

## 📚 Learning Notes (viva / report)

| Question | Answer |
|---|---|
| **Why `log1p(revenue)`?** | Box-office revenue spans ~5 orders of magnitude; the log transform makes the target near-Gaussian and stabilises the regression. |
| **Why a DNN?** | Tabular feature interactions (budget × genre × release window) are non-linear; the MLP captures them better than tree ensembles with equal feature engineering. |
| **Why Huber loss?** | Robust to the fat-tailed residuals that outliers like *Avatar* produce — a compromise between MSE and MAE. |
| **Why BatchNorm + Dropout?** | BatchNorm speeds convergence and stabilises training; Dropout prevents memorising the 3,165-row dataset. |
| **Confidence heuristic** | `0.55 × R² + 0.45 × known-feature fraction` — a transparent, explainable proxy (not a calibrated probability). |
| **Explainability** | Local input perturbation (±5% of feature std): the signed prediction change tells you which features push revenue up or down for *this* movie. |
| **Why `budget_per_runtime`?** | Captures spend intensity — a $200 M film that runs 90 min is a very different proposition from one that runs 3 h. |
| **Why frequency features?** | `director_frequency` and `company_frequency` proxy for industry experience without requiring external databases. |

---

## 📄 License

For academic / demonstration purposes only. Dataset © TMDB; predictions are not investment advice.
