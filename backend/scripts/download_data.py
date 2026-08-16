"""Download the real TMDB 5000 datasets used by this project.

Run from the backend directory:

    python scripts/download_data.py

Sources (publicly available mirrors of the Kaggle "TMDB 5000 Movie Dataset"):
  movies : https://huggingface.co/datasets/johnidouglas/tmdb_5000_movies.csv
  credits: https://raw.githubusercontent.com/harshitcodes/tmdb_movie_data_analysis/
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BACKEND_DIR / "data" / "raw"

SOURCES = {
    "tmdb_5000_movies.csv": (
        "https://gist.githubusercontent.com/cicerojmm/f95a54d4f76de3c84415d0f703aa7e3c/raw/tmdb_5000_movies.csv"
    ),
    "tmdb_5000_credits.csv": (
        "https://raw.githubusercontent.com/harshitcodes/tmdb_movie_data_analysis/"
        "master/tmdb-5000-movie-dataset/tmdb_5000_credits.csv"
    ),
}


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for filename, url in SOURCES.items():
        target = RAW_DIR / filename
        if target.exists() and target.stat().st_size > 1_000_000:
            print(f"[skip] {filename} already exists ({target.stat().st_size:,} bytes).")
            continue
        print(f"[get]  {filename} <- {url}")
        try:
            urllib.request.urlretrieve(url, target)
        except Exception as exc:
            print(f"[error] Failed to download {filename}: {exc}")
            return 1
        print(f"[ok]   {filename} ({target.stat().st_size:,} bytes).")
    print("Download complete. Files are in:", RAW_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
