import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.recommender import engine

@pytest.fixture(scope="module")
def client():
    # Load model artifacts for API testing
    engine.load_artifacts()
    with TestClient(app) as c:
        yield c

def test_api_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["model_artifacts_loaded"] is True

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
