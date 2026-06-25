from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import store


@pytest.fixture(autouse=True)
def _reset():
    store.reset()
    yield
    store.reset()


@pytest.fixture
def client():
    return TestClient(app)


def _video(title="My Video", channel="Test Channel", **over):
    body = {
        "title": title,
        "channel": channel,
        "description": "hello",
        "tags": ["demo", "test"],
        "category": "Education",
        "duration_seconds": 120,
    }
    body.update(over)
    return body


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_upload_video(client):
    r = client.post("/videos", json=_video())
    assert r.status_code == 201
    data = r.json()
    assert len(data["video_id"]) == 11
    assert data["views"] == 0 and data["likes"] == 0
    assert data["visibility"] == "public"
    assert data["url"] == f"https://www.youtube.com/watch?v={data['video_id']}"
    assert data["thumbnail_url"].endswith(f"/vi/{data['video_id']}/hqdefault.jpg")


def test_get_video_roundtrip(client):
    vid = client.post("/videos", json=_video(title="Roundtrip")).json()["video_id"]
    r = client.get(f"/videos/{vid}")
    assert r.status_code == 200
    assert r.json()["title"] == "Roundtrip"


def test_get_missing_video_404(client):
    assert client.get("/videos/doesnotexist").status_code == 404


def test_validation_rejects_bad_duration(client):
    assert client.post("/videos", json=_video(duration_seconds=0)).status_code == 422
    assert client.post("/videos", json=_video(title="")).status_code == 422


def test_list_and_filter(client):
    client.post("/videos", json=_video(title="Cats", channel="A", tags=["pets"]))
    client.post("/videos", json=_video(title="Dogs", channel="B", tags=["pets"]))
    client.post("/videos", json=_video(title="Stocks", channel="A", tags=["finance"]))

    assert len(client.get("/videos").json()) == 3
    assert len(client.get("/videos", params={"channel": "A"}).json()) == 2
    titles = {v["title"] for v in client.get("/videos", params={"q": "Dog"}).json()}
    assert titles == {"Dogs"}


def test_list_invalid_visibility_422(client):
    assert client.get("/videos", params={"visibility": "secret"}).status_code == 422


def test_view_and_like_counters(client):
    vid = client.post("/videos", json=_video()).json()["video_id"]
    client.post(f"/videos/{vid}/view")
    client.post(f"/videos/{vid}/view")
    r = client.post(f"/videos/{vid}/like").json()
    assert r["views"] == 2 and r["likes"] == 1
    assert client.post("/videos/missing/view").status_code == 404


def test_seed(client):
    seeded = client.post("/videos/seed").json()
    assert len(seeded) == 4
    assert len(client.get("/videos").json()) == 4
