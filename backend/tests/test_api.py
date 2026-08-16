"""End-to-end API tests using FastAPI's TestClient (isolated database)."""

import io


def _post(client, path, payload):
    r = client.post(path, json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def test_health(client):
    r = client.get("/api/health")
    body = r.json()
    assert body["success"] is True
    assert body["data"]["status"] == "healthy"
    assert body["data"]["model_ready"] is True


def test_model_info(client):
    body = client.get("/api/model/info").json()
    data = body["data"]
    assert body["success"] is True
    assert data["feature_count"] == 34
    assert "BLOCKBUSTER" in data["performance_thresholds"]
    assert data["dataset"]["rows_used"] > 3000


def test_predict_returns_full_contract(client):
    payload = {
        "title": "Pytest Movie",
        "budget": 100_000_000,
        "runtime": 130,
        "genres": ["Action", "Science Fiction"],
        "release_month": 7,
        "release_day": 18,
        "production_company": "Warner Bros.",
        "director": "Christopher Nolan",
        "lead_actors": ["Leonardo DiCaprio", "Cillian Murphy"],
        "rating": 8.0,
        "vote_count": 20000,
        "popularity": 90.0,
        "language": "en",
    }
    body = _post(client, "/api/predict", payload)["data"]
    assert body["predicted_revenue"] >= 0
    assert body["predicted_revenue_usd"].startswith("$")
    assert body["performance_category"] in {"FLOP", "AVERAGE", "HIT", "SUPER_HIT", "BLOCKBUSTER"}
    assert 0 <= body["confidence_score"] <= 100
    assert body["expected_range"]["lower"] <= body["predicted_revenue"] <= body["expected_range"]["upper"]
    assert body["contributions"], "expected at least one feature contribution"
    assert "disclaimer" in body


def test_predict_validation_errors(client):
    r = client.post(
        "/api/predict",
        json={"title": "Bad", "budget": -5, "runtime": 10, "genres": []},
    )
    assert r.status_code == 422  # envelope carries the error (not an HTTP 500)
    body = r.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "budget" in (body["error"]["fields"] or {})


def test_predict_batch_payload(client):
    body = _post(
        client,
        "/api/predict/batch",
        [
            {"title": "A", "budget": 50_000_000, "runtime": 120, "genres": ["Action"]},
            {"title": "B", "budget": 200_000_000, "runtime": 150, "genres": ["Drama"]},
        ],
    )["data"]
    assert body["total_rows"] == 2
    assert body["successful"] == 2
    assert body["failed"] == 0
    for res in body["results"]:
        assert res["title"] in {"A", "B"}
        assert res["predicted_revenue_usd"]
        assert res["performance_category"]


def test_predict_csv_upload(client):
    csv = (
        "title,budget,runtime,genres,release_month,production_company,director,lead_actors,rating\n"
        'Alpha,60000000,118,"Action|Adventure",7,Universal Pictures,Steven Spielberg,"Tom Hanks",7.2\n'
        'Beta,150000000,140,"Drama|History",11,Paramount Pictures,Christopher Nolan,"Leonardo DiCaprio",8.1\n'
    )
    r = client.post("/api/predict/csv", files={"file": ("movies.csv", io.BytesIO(csv.encode()), "text/csv")})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total_rows"] == 2
    assert data["successful"] == 2
    assert data["failed"] == 0


def test_predict_csv_bad_row_is_row_error(client):
    csv = "title,budget,runtime\nGood,100000,120\nBad,-5,0\n"
    r = client.post("/api/predict/csv", files={"file": ("movies.csv", io.BytesIO(csv.encode()), "text/csv")})
    data = r.json()["data"]
    assert data["successful"] == 1
    assert data["failed"] == 1
    assert any(res["status"] == "error" for res in data["results"])


def test_analytics_endpoints(client):
    overview = client.get("/api/analytics/overview").json()["data"]
    assert overview["total_movies"] > 3000
    assert overview["highest_revenue_movie"] == "Avatar"

    genres = client.get("/api/analytics/genres").json()["data"]
    assert len(genres) >= 18
    assert all(g["avg_revenue"] >= 0 for g in genres)

    yearly = client.get("/api/analytics/yearly?min_year=2000").json()["data"]
    assert yearly and all(y["year"] >= 2000 for y in yearly)

    scatter = client.get("/api/analytics/budget-vs-revenue?limit=20").json()["data"]
    assert len(scatter) == 20

    top = client.get("/api/analytics/top-movies?limit=5").json()["data"]
    assert top[0]["title"] == "Avatar"

    months = client.get("/api/analytics/release-months").json()["data"]
    assert len(months) == 12
    assert months[0]["label"] == "January"


def test_movies_explorer(client):
    data = client.get("/api/movies?page=1&per_page=5&sort_by=revenue").json()["data"]
    assert data["total"] > 3000
    assert data["total_pages"] == data["total"] // data["per_page"] + 1
    assert data["items"][0]["title"] == "Avatar"
    assert isinstance(data["items"][0]["genres"], list)

    filtered = client.get("/api/movies?genre=Horror&min_year=2010").json()["data"]
    for item in filtered["items"]:
        assert item["primary_genre"] == "Horror"

    detail = client.get("/api/movies/1").json()["data"]
    assert detail["title"] == "Avatar"

    summary = client.get("/api/movies/filters/summary").json()["data"]
    assert "Action" in summary["genres"]
    assert summary["year_min"] is not None
    assert summary["companies"] and summary["directors"]


def test_training_metrics_endpoint(client):
    body = client.get("/api/training/metrics").json()
    data = body["data"]
    assert body["success"] is True
    assert data["metrics"]["dnn"]["r2_log"] > 0.5
    assert data["training_history"]["epochs"] > 0

    status = client.get("/api/training/status").json()["data"]
    assert status["status"] in {"idle", "running", "completed"}
