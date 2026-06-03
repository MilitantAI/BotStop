from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from botstop.server.app import create_app
from botstop.settings import Settings


@pytest.fixture
def api_client(tmp_path: Path) -> TestClient:
    settings = Settings(
        secret="test-secret",
        storage_dir=tmp_path / "storage",
        ttl_seconds=300,
        host="127.0.0.1",
        port=8787,
        cors_origins=["*"],
        rate_limit_per_minute=1000,
        api_key=None,
    )
    return TestClient(create_app(settings))


def test_health(api_client: TestClient) -> None:
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_verify_and_refresh(api_client: TestClient) -> None:
    create = api_client.post("/v1/challenges")
    assert create.status_code == 200
    payload = create.json()
    challenge_id = payload["challenge_id"]
    assert payload["digit_length"] == 4
    assert payload["gif_url"].endswith("/animation.gif")

    gif = api_client.get(payload["gif_url"])
    assert gif.status_code == 200
    assert gif.headers["content-type"] == "image/gif"

    wrong = api_client.post(f"/v1/challenges/{challenge_id}/verify", json={"answer": "000000"})
    assert wrong.status_code == 200
    assert wrong.json()["ok"] is False

    refresh = api_client.post("/v1/challenges/refresh", json={"previous_id": challenge_id})
    assert refresh.status_code == 200
    new_id = refresh.json()["challenge_id"]
    assert new_id != challenge_id

    missing = api_client.get(f"/v1/challenges/{challenge_id}/animation.gif")
    assert missing.status_code == 404


def test_api_key_required(tmp_path: Path) -> None:
    settings = Settings(
        secret="test-secret",
        storage_dir=tmp_path / "storage",
        ttl_seconds=300,
        host="127.0.0.1",
        port=8787,
        cors_origins=["*"],
        rate_limit_per_minute=1000,
        api_key="secret-key",
    )
    client = TestClient(create_app(settings))
    denied = client.post("/v1/challenges")
    assert denied.status_code == 401

    allowed = client.post("/v1/challenges", headers={"X-API-Key": "secret-key"})
    assert allowed.status_code == 200
