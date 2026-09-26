import pytest

from tests.seed import seed_data


@pytest.fixture(autouse=True)
def seed(session):
    seed_data(session)


def ids(response):
    return [item["application_id"] for item in response.json()["items"]]


def test_default_is_newest_first_with_stable_ties(client):
    response = client.get("/applications")

    assert response.status_code == 200
    assert ids(response) == ["A8", "A7", "A6", "A5", "A4", "A3", "A2", "A1"]
    assert response.json()["total"] == 8


def test_item_has_candidate_and_job(client):
    item = client.get("/applications").json()["items"][0]

    assert item["candidate"] == {
        "candidate_id": "C1",
        "full_name": "Anna Adler",
        "email": "anna@example.com",
        "country": "DE",
        "city": "Hamburg",
        "years_experience": 3,
        "preferred_job_family": "Logistics",
    }
    assert item["job"] == {
        "job_id": "J1",
        "title": "Warehouse Associate",
        "job_family": "Logistics",
        "seniority": "junior",
        "country": "DE",
        "city": "Hamburg",
        "created_at": "2026-01-01T09:00:00",
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
