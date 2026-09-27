import pytest


@pytest.mark.usefixtures("seeded")
def test_filter_options_are_distinct_and_sorted(client):
    response = client.get("/filter-options")

    assert response.status_code == 200
    assert response.json() == {
        "countries": ["AT", "DE"],
        "job_families": ["Healthcare", "IT", "Logistics"],
    }


def test_filter_options_are_empty_without_jobs(client):
    response = client.get("/filter-options")

    assert response.status_code == 200
    assert response.json() == {"countries": [], "job_families": []}
