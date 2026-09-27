import pytest

pytestmark = pytest.mark.usefixtures("seeded")


def test_returns_application_with_candidate_and_job(client):
    response = client.get("/applications/A2")

    assert response.status_code == 200
    assert response.json() == {
        "application_id": "A2",
        "created_at": "2026-03-02T09:00:00",
        "source": "job_board",
        "match_score": 0.7,
        "match_band": "medium",
        "status": "in_review",
        "status_updated_at": "2026-03-03T09:00:00",
        "note": None,
        "llm_scores": [],
        "candidate": {
            "candidate_id": "C2",
            "full_name": "Ben Bauer",
            "email": "ben@example.com",
            "country": "AT",
            "city": "Vienna",
            "years_experience": 6,
            "preferred_job_family": "IT",
        },
        "job": {
            "job_id": "J1",
            "title": "Warehouse Associate",
            "job_family": "Logistics",
            "seniority": "junior",
            "country": "DE",
            "city": "Hamburg",
            "created_at": "2026-01-01T09:00:00",
        },
    }


def test_new_application_has_no_status_date(client):
    body = client.get("/applications/A1").json()

    assert body["status"] == "new"
    assert body["status_updated_at"] is None


def test_unknown_id_gives_404(client):
    response = client.get("/applications/NOPE")

    assert response.status_code == 404
    assert response.json() == {"detail": "Application not found"}
