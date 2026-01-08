from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200

    data = r.json()
    assert data["status"] == "healthy"
    assert data["service"] == "attendance-api"
    datetime.fromisoformat(data["timestamp"])
