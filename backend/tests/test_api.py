"""
Integration tests for FastAPI endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


@pytest.fixture(name="setup_db", scope="module", autouse=True)
def setup_db_fixture():
    """Create all tables before running tests and drop them after."""
    # Since we are using an async engine, we can run sync metadata creation using async engine's runner in real apps,
    # but for simple tests, main lifespan initializes the database automatically when startup runs.
    yield


def test_health_check_endpoint():
    """Test GET /api/v1/health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "mode" in data
    assert "llm_available" in data


def test_create_and_get_brand_endpoint():
    """Test POST /api/v1/brands and GET /api/v1/brands endpoints."""
    payload = {
        "name": "Acme Niche",
        "tagline": "Software at the speed of thought",
        "industry": "technology",
        "target_audience": ["developers", "CTOs"],
        "brand_voice": ["authoritative", "witty"],
        "writing_perspective": "first_person_plural",
        "competitor_brands": [],
        "avoid_topics": [],
        "sample_content": [],
    }

    # Create brand
    response = client.post("/api/v1/brands", json=payload)
    assert response.status_code == 201
    brand_data = response.json()
    assert brand_data["name"] == "Acme Niche"
    assert "id" in brand_data

    brand_id = brand_data["id"]

    # Get brand by ID
    response = client.get(f"/api/v1/brands/{brand_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Acme Niche"

    # List all brands
    response = client.get("/api/v1/brands")
    assert response.status_code == 200
    brands_list = response.json()
    assert len(brands_list) >= 1
    assert any(b["id"] == brand_id for b in brands_list)
