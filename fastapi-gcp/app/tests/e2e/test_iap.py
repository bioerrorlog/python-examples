"""End-to-end tests against the deployed service behind IAP."""

import requests


def test_root(call):
    response = call("GET", "/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, FastAPI on GCP"}


def test_health(call):
    response = call("GET", "/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_echo(call):
    response = call("POST", "/echo", {"text": "hello"})
    assert response.status_code == 200
    assert response.json() == {"text": "hello"}


def test_request_without_token_is_rejected(service_url):
    response = requests.get(service_url, timeout=30)
    assert response.status_code in (401, 403)
