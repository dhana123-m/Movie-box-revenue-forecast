# 🎬 Movie Box Office Revenue Forecast

A full-stack college mini-project that predicts **worldwide box office revenue** for a movie using a **Deep Neural Network (TensorFlow / Keras)** trained on the real **TMDB 5000** dataset.

- **Frontend** — React 18 + TypeScript + Vite + Tailwind CSS + Recharts (dark cinematic UI)
- **Backend** — FastAPI + SQLAlchemy + SQLite, REST API with error envelopes
- **ML Pipeline** — feature engineering, DNN training, baseline comparison, evaluation artifacts
- **Extras** — single & batch (JSON/CSV) prediction, sensitivity explainability, retraining endpoint, analytics, movie explorer

---

## ✨ Features

| Area | Description |
|---|---|
| 🎯 **Revenue Forecast** | Form-driven prediction: budget, runtime, genres, release window, audience signals, cast & crew |
| 🔍 **Explainability** | Per-feature sensitivity analysis — *why* the model predicted this number |
| 📦 **Batch Prediction** | Predict many movies at once via JSON array or CSV upload |
| 📈 **Analytics** | Revenue by year, genre, release month, budget-vs-revenue scatter, top grossers |
| 🎞️ **Movie Explorer** | Search / filter / sort / paginate the 3,164-movie database |
| 🧠 **Model Hub** | Test metrics vs. baselines, training curves, dataset split, thresholds |
| ♻️ **Retraining** | One-click retrain from the UI (development only) |

---

## 🧠 The Model

- **Task**: regression on `log1p(revenue)` (revenue is highly skewed).
- **Architecture**: `512 → 256 → 128 → 64` ReLU dense layers, each with **BatchNorm** and **Dropout (0.35/0.30/0.25/0.20)**, **L2 (1e-4)** regularization and a final linear output.
- **Loss**: Huber (delta = 1.0) · **Optimizer**: Adam (lr 1e-3, ReduceLROnPlateau) · **Early stopping**: patience 25 on val loss.
- **Features (34)**: 16 engineered numerics (budget, runtime, popularity, rating, vote count, release timing, cast star power, director/studio track record, …) + **18 genre multi-hot** flags.
- **Dataset**: 3,165 cleaned movies from TMDB 5000 (budget>0, revenue>0, runtime 30–400, status=Released).
- **Data split**: 70 / 15 / 15 (stratified by revenue quartile).
- The deployed hyper-parameters were selected by a bounded **grid search** (11 trials, validation MAE). See [ML experiments](#-ml-experiments).

### Test performance (held-out)

| Model | R² (log) | RMSE (log) |
|---|---|---|
| **Deep Neural Network** | **0.685** | 1.159 |
| Linear Regression | 0.690 | 1.150 |
| Random Forest | 0.651 | 1.221 |
| Extra Trees | 0.636 | 1.246 |
| XGBoost | 0.632 | 1.254 |
| Gradient Boosting | 0.632 | 1.254 |
| AdaBoost | 0.520 | 1.432 |
| K-Nearest Neighbors | 0.490 | 1.475 |
| Decision Tree | 0.228 | 1.815 |

The DNN is the best *non-linear* model on log-space RMSE/MAE and essentially ties Linear Regression on R² while being far more robust in the original revenue space (MAE **$55.4M** vs. the linear model's $53.8M — the DNN does not overshoot blockbusters the way trees and the linear model do).

### Performance labels

Predicted revenue is classified against the budget via a multiplier:

| Label | Revenue / Budget |
|---|---|
| `FLOP` | < 1.0x |
| `AVERAGE` | 1.0x – 2.0x |
| `HIT` | 2.0x – 4.0x |
| `SUPER_HIT` | 4.0x – 8.0x |
| `BLOCKBUSTER` | ≥ 8.0x |

> ⚠️ **Disclaimer**: Predictions are statistical estimates. Confidence reflects training accuracy + input completeness, not a probability of success. Use the 95% range, not the point estimate.

---

## 🔬 ML Experiments

Artifacts are generated under `backend/models/evaluation/` (CSV/JSON/PNG).

### Hyper-parameter tuning

`backend/training/hyperparameter_tuning.py` sweeps **11 configurations** over layer width/depth, dropout strength, L2 and learning rate, scoring each by validation MAE.

```bat
cd backend
.venv\Scripts\python training\hyperparameter_tuning.py
```

Top results (validation MAE, log-revenue, lower is better):

| Config | Dropout | lr | L2 | Val MAE |
|---|---|---|---|---|
| **512→256→128→64** ✅ | 0.35/0.30/0.25/0.20 | 1e-3 | 1e-4 | **0.7209** |
| 256→192→128→64→32 | 0.30/0.25/0.20/0.15/0.15 | 1e-3 | 1e-4 | 0.7319 |
| 256→128→64→32 | 0.30/0.25/0.20/0.20 | 3e-3 | 1e-4 | 0.7457 |
| 256→128→64→32 (baseline) | 0.30/0.25/0.20/0.20 | 1e-3 | 1e-4 | 0.7702 |

The winning configuration became the production default (`train.py`), lifting test R²(log) from **0.653 → 0.685** and cutting test MAE from **$66.2M → $55.4M**.

### Feature importance

Permutation importance on the held-out test set (drop in MAE when each feature is shuffled). Top inputs:

1. `vote_count_log` (audience reach)
2. `budget_log`
3. `budget_per_runtime` (spend intensity)
4. `popularity`
5. `release_year` + release-season features
6. Genre flags (`Family`, `Science Fiction`, `Romance`, `Documentary`…)

Visualised live on the **Model Performance** page.

### Baselines

Eight classical regressors compete with the DNN on the same split & feature matrix: Linear Regression, Random Forest, Gradient Boosting, XGBoost, Extra Trees, AdaBoost, K-Nearest Neighbors and Decision Tree.

---

## 🚀 Getting Started

### Prerequisites

- Python **3.12** (required for TensorFlow wheels on Windows)
- Node.js ≥ 18
- Git

### 1. Backend

```bat
:: from the repo root
cd backend
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python scripts\download_data.py   :: optional: re-download TMDB CSVs
.venv\Scripts\python training\train.py          :: optional: (re)train + evaluate
.venv\Scripts\python -m uvicorn app.main:app --port 8000
```

Or simply run `run_backend.bat` (uses a pre-existing `.venv`).

- API docs (Swagger): http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

On startup the API **auto-seeds the SQLite database** (`backend/movie_box.db`) from `data/processed/tmdb_5000_processed.csv` if empty, and loads the trained model.

### 2. Frontend

```bat
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the Vite proxy forwards `/api` to the backend on port 8000.

### 3. Ready-made scripts

| Script | What it does |
|---|---|
| `run_backend.bat` | Starts the FastAPI backend |
| `run_frontend.bat` | Starts the Vite dev server |

### 4. Single-port production mode (optional)

After `npm run build` the backend also serves the built frontend on the same
port, so the entire app lives on **one origin** — no CORS, no proxy:

```bat
cd frontend && npm run build
cd ..\backend
.venv\Scripts\python -m uvicorn app.main:app --port 8000
:: open http://localhost:8000
```

FastAPI mounts `/assets` statically, returns `index.html` for any non-`/api`
route (SPA routing) and keeps every `/api/*` endpoint on the error envelope.
Disable by setting `FRONTEND_DIST_PATH` to a non-existent folder in `backend/.env`.

### 5. Cloud deployment (Render, free)

The repo ships a [Render](https://render.com) blueprint (`render.yaml`) so the
whole stack — API **and** built frontend — deploys to one free URL:

1. Push this repository to GitHub (`git remote add origin <url>` + `git push`).
2. On Render: **Dashboard → New → Blueprint**, select the repo.
3. Render installs the backend, runs `npm run build` for the frontend, and
   starts `uvicorn` on the assigned `$PORT`. Open the generated URL.

Deployment facts:

- **No re-training on the server** — the trained model, preprocessor and
  training history are committed to git and loaded on boot.
- **No dataset downloads** — the processed CSV is committed; SQLite seeds from
  it automatically on first start.
- **One origin, no CORS** — FastAPI serves `frontend/dist` with SPA fallback.
- **SQLite is ephemeral** — data resets on redeploy (fine for a demo; the API
  reseeds automatically).
- **Retraining is disabled in production** (`ALLOW_RETRAIN=false`).
- Free-tier builds have 512 MB RAM; TensorFlow installs fine but if the build
  ever OOMs, bump the service to the paid `Starter` plan and redeploy.

---

## 📁 Project Structure

```
Movie-box-revenue-forecast/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, lifespan, CORS, routers
│   │   ├── config.py               # env-driven settings
│   │   ├── database.py             # SQLAlchemy engine/session
│   │   ├── models/                 # ORM models (Movie, Prediction, ModelMetadata)
│   │   ├── schemas/                # Pydantic request/response contracts
│   │   ├── ml/
│   │   │   ├── preprocessor.py     # shared feature pipeline (fit/transform/inverse)
│   │   │   ├── genres.py           # canonical genre vocabulary
│   │   │   ├── performance.py      # FLOP..BLOCKBUSTER classifier
│   │   │   └── explain.py          # perturbation-based sensitivity explainer
│   │   ├── services/               # model, prediction, analytics, db, training
│   │   ├── routes/                 # health, predict, analytics, movies, training
│   │   └── utils/                  # error envelope, formatting helpers
│   ├── training/
│   │   ├── feature_engineering.py  # raw CSV -> processed dataset
│   │   ├── model.py                # build_dnn / train_dnn (configurable)
│   │   ├── hyperparameter_tuning.py # DNN hyper-parameter grid search
│   │   ├── evaluate.py             # baselines + evaluation plots
│   │   └── train.py                # full pipeline entrypoint
│   ├── scripts/download_data.py    # downloads TMDB 5000 CSVs
│   ├── data/raw/                   # downloaded CSVs
│   ├── data/processed/             # cleaned dataset (3,165 movies)
│   ├── models/                     # model.keras, preprocessor.pkl, metrics.json, evaluation/
│   └── tests/                      # pytest suite
├── frontend/
│   └── src/
│       ├── services/api.ts         # typed API client
│       ├── hooks/useApi.ts         # data-fetching hook
│       ├── components/             # layout, charts, ui, forecast
│       ├── pages/                  # Dashboard, Forecast, Analytics, Explorer, Model, Settings
│       └── utils/format.ts         # currency/formatting helpers
├── notebooks/exploratory_analysis.ipynb
├── run_backend.bat
├── run_frontend.bat
└── README.md
```

---

## 🔌 API Overview

All responses use a consistent envelope:

```json
{ "success": true, "data": { ... }, "message": null, "error": null }
```

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Liveness + model & DB status |
| GET | `/api/model/info` | Model metadata, thresholds, dataset info |
| POST | `/api/predict` | Single prediction |
| POST | `/api/predict/batch` | Batch prediction from a JSON array |
| POST | `/api/predict/csv` | Batch prediction from an uploaded CSV |
| GET | `/api/analytics/overview` | Global stats |
| GET | `/api/analytics/genres` | Genre-level revenue stats |
| GET | `/api/analytics/yearly` | Per-year revenue (`?min_year=2000`) |
| GET | `/api/analytics/budget-vs-revenue` | Scatter data |
| GET | `/api/analytics/top-movies` | Highest grossing movies |
| GET | `/api/analytics/release-months` | Monthly release performance |
| GET | `/api/movies` | Explorer list (`q`, `genre`, `min_year`, `max_year`, `sort_by`, `page`…) |
| GET | `/api/movies/{id}` | Movie detail |
| GET | `/api/movies/filters/summary` | Dropdown options (genres, years, languages, companies, directors) |
| GET | `/api/training/metrics` | DNN + baseline metrics & training history |
| GET | `/api/training/status` | Retraining job status |
| POST | `/api/retrain` | Trigger retraining (dev only) |

### Single prediction request

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

### CSV format

Required columns: `title, budget, runtime`; optional: `genres` (pipe-separated `Action|Adventure`), `release_month`, `release_day`, `release_year`, `production_company`, `director`, `lead_actors` (pipe-separated), `rating`, `vote_count`, `popularity`, `language`. See `demo_movies.csv`.

---

## 🧪 Testing

```bat
:: backend
cd backend
.venv\Scripts\python -m pytest tests -q

:: frontend
cd frontend
npm test
npm run build   :: type-checks (tsc --noEmit) + production build
```

---

## ⚙️ Configuration

Copy `backend/.env.example` to `backend/.env` to override defaults (database URL, paths, training hyper-parameters, `ALLOW_RETRAIN`, `INR_PER_USD`, CORS origins…).

---

## 📚 Learning Notes (for the viva / report)

- **Why `log1p(revenue)`?** Box-office revenue spans ~5 orders of magnitude; the log transform makes the target near-Gaussian and stabilises the regression.
- **Why a DNN?** Tabular feature interactions (budget × genre × release window) are non-linear; the MLP captures them better than tree ensembles at equal feature engineering.
- **Why Huber loss?** Robust to the fat-tailed residuals that outliers like *Avatar* produce — a compromise between MSE and MAE.
- **Why BatchNorm + Dropout?** BatchNorm speeds convergence and stabilises training; Dropout prevents memorising the 3,165-row dataset.
- **Confidence heuristic** = `0.55 · R² + 0.45 · known-feature fraction` — a transparent, explainable proxy (not a calibrated probability).
- **Explainability** uses local input perturbation (±5% of feature std): the signed prediction change tells you which features push revenue up or down for *this* movie.

---

## 📄 License

For academic / demonstration purposes only. Dataset © TMDB; predictions are not investment advice.
