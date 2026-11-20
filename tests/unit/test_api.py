import pytest
from pydantic import ValidationError

from nyayasetu.config import Settings

pytestmark = pytest.mark.unit


def test_health_is_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "git_sha": "dev"}


def test_health_reports_configured_git_sha(client):
    client.app.state.settings.git_sha = "abc123"

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "git_sha": "abc123"}


def test_ready_when_database_is_available(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": True},
    }


def test_list_documents(client):
    response = client.get("/v1/documents")
    body = response.json()

    assert response.status_code == 200
    assert body["total"] == 3
    assert len(body["items"]) == 3


def test_list_documents_paginates(client):
    response = client.get("/v1/documents", params={"limit": 2, "offset": 0})
    body = response.json()

    assert response.status_code == 200
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["items"][0]["id"] == "001"


def test_list_documents_second_page(client):
    response = client.get("/v1/documents", params={"limit": 2, "offset": 2})
    body = response.json()

    assert response.status_code == 200
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == "003"


def test_search_documents(client):
    response = client.get("/v1/documents", params={"q": "beta"})
    assert response.status_code == 200
    assert [doc["id"] for doc in response.json()["items"]] == ["002"]


def test_filter_documents(client):
    response = client.get("/v1/documents", params={"kind": "circular"})
    body = response.json()

    assert response.status_code == 200
    assert body["total"] == 2
    assert [doc["id"] for doc in body["items"]] == ["002", "003"]


def test_search_and_filter_documents(client):
    response = client.get(
        "/v1/documents",
        params={"q": "beta", "kind": "circular"},
    )
    assert [doc["id"] for doc in response.json()["items"]] == ["002"]


def test_get_document_found(client):
    response = client.get("/v1/documents/001")
    assert response.status_code == 200
    assert response.json()["title"] == "Alpha guideline"


def test_missing_document_is_problem_details(client):
    response = client.get("/v1/documents/999")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["status"] == 404
    assert response.json()["title"] == "Not Found"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]


def test_bad_limit_is_422(client):
    response = client.get("/v1/documents", params={"limit": 0})
    assert response.status_code == 422


def test_limit_above_maximum_is_422(client):
    response = client.get("/v1/documents", params={"limit": 101})
    assert response.status_code == 422


def test_invalid_filter_name_is_400(client):
    response = client.get("/v1/documents?123invalid=test")
    assert response.status_code == 400


def test_negative_offset_is_422(client):
    response = client.get("/v1/documents", params={"offset": -1})
    assert response.status_code == 422


def test_request_id_is_echoed(client):
    response = client.get("/health", headers={"X-Request-ID": "abc123"})
    assert response.headers["X-Request-ID"] == "abc123"


def test_settings_require_app_env(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
