import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.recommender import engine
from api.index import app as vercel_app

@pytest.fixture(scope="module")
def client():
    # Load model artifacts for API testing
    engine.load_artifacts()
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def vercel_client():
    engine.load_artifacts()
    with TestClient(vercel_app) as c:
        yield c

def test_api_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["model_artifacts_loaded"] is True

def test_root_health_fallback(client):
    """Verify endpoint resolves even without /api prefix."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"

def test_cors_vercel_origin(client):
    """Verify CORS headers allow .vercel.app origins."""
    headers = {
        "Origin": "https://movie-recommendation-demo.vercel.app",
        "Access-Control-Request-Method": "GET",
    }
    res = client.options("/api/health", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "https://movie-recommendation-demo.vercel.app"

def test_vercel_serverless_path_rewrites(vercel_client):
    """Verify VercelServerlessApp normalizer handles internal rewrite paths."""
    # 1. Rewritten to /api/index.py with x-forwarded-uri
    res = vercel_client.get("/api/index.py", headers={"x-forwarded-uri": "/api/health"})
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    # 2. Rewritten to /api/index.py with x-matched-path
    res = vercel_client.get("/api/index.py", headers={"x-matched-path": "/api/health"})
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    # 3. Rewritten subpath /api/index.py/api/health
    res = vercel_client.get("/api/index.py/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_api_movies_search(client):
    res = client.get("/api/movies/search?q=dark+knight")
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    assert any("dark knight" in item["title"].lower() for item in data)

def test_api_movies_get_by_id(client):
    res = client.get("/api/movies/1")
    assert res.status_code == 200
    data = res.json()
    assert data["movieId"] == 1
    assert "Toy Story" in data["title"]

def test_api_recommend_single(client):
    res = client.post("/api/recommend/single", json={"query_or_id": "interstellar", "top_n": 5})
    assert res.status_code == 200
    data = res.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) == 5

def test_api_recommend_hybrid(client):
    res = client.post("/api/recommend/hybrid", json={
        "seeds": [
            {"query_or_id": "matrix", "rating": 5.0},
            {"query_or_id": "inception", "rating": 4.5}
        ],
        "top_n": 5
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["recommendations"]) == 5

def test_api_insights(client):
    res = client.get("/api/insights")
    assert res.status_code == 200
    data = res.json()
    assert data["total_movies"] == 9742
    assert data["unique_users"] == 610
