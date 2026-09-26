from datetime import datetime, timedelta

import pytest

from tests.seed import seed_data


@pytest.fixture(autouse=True)
def seed(session):
    seed_data(session)


def test_status_change_sets_date_and_is_saved(client):
    response = client.patch("/applications/A1", json={"status": "shortlisted"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "shortlisted"
    updated_at = datetime.fromisoformat(body["status_updated_at"])
    assert datetime.now() - updated_at < timedelta(minutes=1)

    assert client.get("/applications/A1").json()["status"] == "shortlisted"


def test_same_status_keeps_old_date(client):
    body = client.patch("/applications/A2", json={"status": "in_review"}).json()

    assert body["status"] == "in_review"
    assert body["status_updated_at"] == "2026-03-03T09:00:00"


def test_note_only_leaves_status_and_date(client):
    body = client.patch("/applications/A2", json={"note": "Call back Monday"}).json()

    assert body["note"] == "Call back Monday"
    assert body["status"] == "in_review"
    assert body["status_updated_at"] == "2026-03-03T09:00:00"


def test_status_and_note_together(client):
    body = client.patch("/applications/A1", json={"status": "rejected", "note": "No forklift licence"}).json()

    assert body["status"] == "rejected"
    assert body["note"] == "No forklift licence"
    assert body["status_updated_at"] is not None


def test_null_note_clears_it(client):
    client.patch("/applications/A1", json={"note": "temp"})

    body = client.patch("/applications/A1", json={"note": None}).json()

    assert body["note"] is None


@pytest.mark.parametrize(
    "payload",
    [{"status": "maybe"}, {}, {"staus": "new"}, {"note": "x" * 501}],
)
def test_bad_body_is_rejected(client, payload):
    assert client.patch("/applications/A1", json=payload).status_code == 422


def test_unknown_id_gives_404(client):
    response = client.patch("/applications/NOPE", json={"status": "hired"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Application not found"}
