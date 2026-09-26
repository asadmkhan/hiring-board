from datetime import datetime

import pytest

from app.models import Application, Candidate, Job


def jobs():
    return [
        Job(
            job_id="J1",
            title="Warehouse Associate",
            job_family="Logistics",
            seniority="junior",
            country="DE",
            city="Hamburg",
            created_at=datetime(2026, 1, 1, 9, 0),
        ),
        Job(
            job_id="J2",
            title="Backend Developer",
            job_family="IT",
            seniority="mid",
            country="AT",
            city="Vienna",
            created_at=datetime(2026, 1, 2, 9, 0),
        ),
        Job(
            job_id="J3",
            title="Nurse",
            job_family="Healthcare",
            seniority="senior",
            country="DE",
            city="Berlin",
            created_at=datetime(2026, 1, 3, 9, 0),
        ),
    ]


def candidates():
    return [
        Candidate(
            candidate_id="C1",
            full_name="Anna Adler",
            email="anna@example.com",
            country="DE",
            city="Hamburg",
            years_experience=3,
            preferred_job_family="Logistics",
        ),
        Candidate(
            candidate_id="C2",
            full_name="Ben Bauer",
            email="ben@example.com",
            country="AT",
            city="Vienna",
            years_experience=6,
            preferred_job_family="IT",
        ),
        Candidate(
            candidate_id="C3",
            full_name="Cara Conti",
            email="cara@example.com",
            country="DE",
            city="Berlin",
            years_experience=10,
            preferred_job_family="Healthcare",
        ),
    ]


def application(app_id, job_id, candidate_id, day, score, status, updated=None):
    return Application(
        application_id=app_id,
        job_id=job_id,
        candidate_id=candidate_id,
        created_at=datetime(2026, 3, day, 9, 0),
        source="job_board",
        match_score=score,
        match_band="medium",
        status=status,
        status_updated_at=updated,
    )


# Scores tie on 0.5 and 0.7, A5 and A6 share a date, C1 applied to J1 twice.
def applications():
    return [
        application("A1", "J1", "C1", 1, 0.5, "new"),
        application("A2", "J1", "C2", 2, 0.7, "in_review", datetime(2026, 3, 3, 9, 0)),
        application("A3", "J2", "C1", 3, 0.5, "new"),
        application(
            "A4", "J2", "C3", 4, 0.9, "shortlisted", datetime(2026, 3, 5, 9, 0)
        ),
        application("A5", "J3", "C2", 5, 0.3, "rejected", datetime(2026, 3, 6, 9, 0)),
        application("A6", "J3", "C3", 5, 0.5, "hired", datetime(2026, 3, 7, 9, 0)),
        application("A7", "J1", "C3", 6, 0.7, "new"),
        application("A8", "J1", "C1", 7, 0.1, "new"),
    ]


@pytest.fixture(autouse=True)
def seed(session):
    session.add_all(jobs() + candidates() + applications())
    session.commit()


def ids(response):
    return [item["application_id"] for item in response.json()["items"]]


def test_default_is_newest_first_with_stable_ties(client):
    response = client.get("/applications")

    assert response.status_code == 200
    assert ids(response) == ["A8", "A7", "A6", "A5", "A4", "A3", "A2", "A1"]
    assert response.json()["total"] == 8


def test_item_has_candidate_and_job(client):
    item = client.get("/applications").json()["items"][0]

    assert item["candidate"] == {"candidate_id": "C1", "full_name": "Anna Adler"}
    assert item["job"] == {
        "job_id": "J1",
        "title": "Warehouse Associate",
        "job_family": "Logistics",
        "country": "DE",
        "city": "Hamburg",
    }
    assert item["status"] == "new"
    assert item["status_updated_at"] is None


def test_filter_by_status(client):
    response = client.get("/applications", params={"status": "new"})

    assert ids(response) == ["A8", "A7", "A3", "A1"]
    assert response.json()["total"] == 4


def test_filter_by_job_country(client):
    response = client.get("/applications", params={"country": "AT"})

    assert ids(response) == ["A4", "A3"]


def test_filter_by_job_family(client):
    response = client.get("/applications", params={"job_family": "Healthcare"})

    assert ids(response) == ["A6", "A5"]


def test_filters_combine(client):
    response = client.get("/applications", params={"status": "new", "country": "DE"})

    assert ids(response) == ["A8", "A7", "A1"]
    assert response.json()["total"] == 3


def test_unknown_filter_value_gives_empty_page(client):
    response = client.get("/applications", params={"job_family": "Farming"})

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "page_size": 20}


def test_sort_by_score_desc_breaks_ties_by_id(client):
    response = client.get(
        "/applications", params={"sort": "match_score", "order": "desc"}
    )

    assert ids(response) == ["A4", "A7", "A2", "A6", "A3", "A1", "A5", "A8"]


def test_sort_by_score_asc(client):
    response = client.get(
        "/applications", params={"sort": "match_score", "order": "asc"}
    )

    assert ids(response) == ["A8", "A5", "A1", "A3", "A6", "A2", "A7", "A4"]


def test_paging_is_stable_across_pages(client):
    pages = [
        ids(
            client.get(
                "/applications",
                params={"sort": "match_score", "page": page, "page_size": 3},
            )
        )
        for page in (1, 2, 3, 4)
    ]

    assert pages == [["A4", "A7", "A2"], ["A6", "A3", "A1"], ["A5", "A8"], []]


def test_total_counts_all_matches_not_just_the_page(client):
    response = client.get("/applications", params={"status": "new", "page_size": 2})

    assert len(response.json()["items"]) == 2
    assert response.json()["total"] == 4
    assert response.json()["page_size"] == 2


@pytest.mark.parametrize(
    "params",
    [
        {"status": "maybe"},
        {"sort": "title"},
        {"order": "up"},
        {"page": 0},
        {"page_size": 0},
        {"page_size": 101},
    ],
)
def test_bad_values_are_rejected(client, params):
    assert client.get("/applications", params=params).status_code == 422
