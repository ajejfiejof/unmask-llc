"""Integration tests for FastAPI endpoints."""

from fastapi.testclient import TestClient
from unmask_llc.api.app import app

client = TestClient(app)


def test_api_summary():
    response = client.get("/api/v1/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["metrics"]["total_properties"] > 0


def test_index_route():
    response = client.get("/")
    assert response.status_code == 200
    assert "UnmaskLLC" in response.text


def test_api_clusters():
    response = client.get("/api/v1/clusters")
    assert response.status_code == 200
    data = response.json()
    assert len(data["clusters"]) > 0


def test_api_search():
    response = client.get("/api/v1/search?q=Market")
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] > 0


def test_api_graph():
    clusters_res = client.get("/api/v1/clusters")
    first_cluster_id = clusters_res.json()["clusters"][0]["cluster_id"]

    response = client.get(f"/api/v1/graph/{first_cluster_id}")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
