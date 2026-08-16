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
- **Architecture**: `256 → 128 → 64 → 32` ReLU dense layers with **BatchNorm**, **Dropout (0.30/0.25/0.20/0.20)** and **L2 (1e-4)** regularization; final linear output.
- **Loss**: Huber (delta = 1.0) · **Optimizer**: Adam (lr 1e-3, ReduceLROnPlateau) · **Early stopping**: patience 25 on val loss.
- **Features (34)**: 16 engineered numerics (budget, runtime, popularity, rating, vote count, release timing, cast star power, director/studio track record, …) + **18 genre multi-hot** flags.
- **Dataset**: 3,165 cleaned movies from TMDB 5000 (budget>0, revenue>0, runtime 30–400, status=Released).
- **Data split**: 70 / 15 / 15 (stratified by revenue quartile).

### Test performance (held-out)

| Model | R² (log) | RMSE (log) |
|---|---|---|
| **Deep Neural Network** | **0.653** | 1.217 |
| Random Forest | 0.649 | 1.223 |
| XGBoost | 0.628 | 1.260 |
| Gradient Boosting | 0.619 | 1.275 |
| Linear Regression | 0.690 | 1.150 |

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
│   │   ├── model.py                # build_dnn / train_dnn
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
