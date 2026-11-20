"""
API integration tests for WasteWiseAI.
Tests /healthz, /api/model/status, /api/scan/replay/frames, and replay step execution.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_healthz_endpoint():
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "WasteWiseAI"
    assert "model_status" in data


def test_model_status_endpoint():
    response = client.get("/api/model/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_mock" in data
    assert "classes" in data
    assert "target_latency_ms" in data


def test_list_replay_frames():
    response = client.get("/api/scan/replay/frames")
    assert response.status_code == 200
    data = response.json()
    assert "frames" in data
    assert len(data["frames"]) >= 1


def test_replay_step_execution():
    response = client.post("/api/scan/replay/step?frame_index=1")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "plate_state" in data
    assert "total_leftover_grams" in data
    assert "image_base64" in data

