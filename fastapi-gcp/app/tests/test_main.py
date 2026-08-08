from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_echo():
    response = client.post("/echo", json={"text": "hello"})
    assert response.status_code == 200
    assert response.json() == {"text": "hello"}


def test_echo_requires_text():
    response = client.post("/echo", json={})
    assert response.status_code == 422
