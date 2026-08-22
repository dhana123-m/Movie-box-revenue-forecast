"""Vercel Python runtime entrypoint for the FastAPI backend.

Vercel auto-detects an ASGI ``app`` inside ``api/*.py``. All requests are
routed here by ``vercel.json`` rewrites.

Serverless specifics handled below:

* Environment defaults are applied *before* importing ``app.main`` because
  settings are read once at import time. The SQLite database lives in /tmp
  (the only writable location) and is re-seeded on each cold start.
* Vercel does not reliably fire ASGI lifespan events, so ``ensure_initialized``
  (tables + model load + seed) is invoked explicitly at import; it is
  idempotent and guarded by a lock, so warm invocations skip it instantly.
"""

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Serverless-safe configuration defaults (dashboard env vars still win).
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/movie_box.db")
os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("ALLOW_RETRAIN", "false")
os.environ.setdefault(
    "CORS_ORIGINS",
    ",".join(
        [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "https://movie-box-office-frontend.onrender.com",
        ]
    ),
)

from app.main import app, ensure_initialized  # noqa: E402

ensure_initialized()
