from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_predict():
    r = client.post("/predict", json={"batch_size": 2})
    assert r.status_code == 200
    j = r.json()
    assert "predictions" in j
