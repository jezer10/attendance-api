from datetime import datetime
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200

    data = r.json()
    print(data)

    # Validaciones de contenido
    assert data["status"] == "healthy"
    assert data["service"] == "attendance-api"

    # Validación de timestamp ISO 8601 (parseable)
    datetime.fromisoformat(data["timestamp"])
