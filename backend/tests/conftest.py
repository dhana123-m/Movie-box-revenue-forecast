"""Shared pytest fixtures.

An isolated SQLite database is created for the API tests so the real
``backend/movie_box.db`` is never touched.
"""

import os
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import pytest

_hold = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_hold.name}"


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def model_service():
    from app.services.model_service import get_model_service

    service = get_model_service()
    service.load()
    return service
