"""Tests for the FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from cyber_soc_env.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthCheck:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestCoreEndpoints:
    def test_list_tasks(self, client):
        response = client.get("/tasks")
        assert response.status_code == 200
        tasks = response.json()["tasks"]
        assert len(tasks) == 3
        # Fast check task1 exists
        assert any(t["task_id"] == "task1" for t in tasks)

    def test_grader_get(self, client):
        response = client.get("/grader?task_id=task1&episode_id=123")
        assert response.status_code == 200
        data = response.json()
        assert 0.0 <= data["score"] <= 1.0
        assert "passed" in data

    def test_baseline_get(self, client):
        response = client.get("/baseline")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["started", "already_running"]
