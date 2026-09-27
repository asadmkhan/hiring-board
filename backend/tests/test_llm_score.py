import pytest

from app.main import app
from app.scoring.base import ScoreResult, ScoringError
from app.scoring.registry import available_scorers

pytestmark = pytest.mark.usefixtures("seeded")


class CountingScorer:
    provider = "mock"
    label = "Counting"
    model = "counting-v1"

    def __init__(self):
        self.calls = 0

    def score(self, job, candidate):
        self.calls += 1
        return ScoreResult(score=77, reason="Counting reason.")


class FailingScorer:
    provider = "claude"
    label = "Failing"
    model = "failing-v1"

    def score(self, job, candidate):
        raise ScoringError("Claude is down")


@pytest.fixture
def scorers(client):
    fakes = {"mock": CountingScorer(), "claude": FailingScorer()}
    app.dependency_overrides[available_scorers] = lambda: fakes
    yield fakes
    app.dependency_overrides.pop(available_scorers, None)


def test_first_call_scores_and_stores(client, scorers):
    response = client.post("/applications/A1/llm-score", json={"provider": "mock"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert body["model"] == "counting-v1"
    assert body["score"] == 77
    assert body["reason"] == "Counting reason."
    assert body["cached"] is False
    assert scorers["mock"].calls == 1


def test_second_call_reuses_the_stored_score(client, scorers):
    first = client.post("/applications/A1/llm-score", json={"provider": "mock"}).json()
    second = client.post("/applications/A1/llm-score", json={"provider": "mock"}).json()

    assert second["cached"] is True
    assert second["score"] == first["score"]
    assert second["scored_at"] == first["scored_at"]
    assert scorers["mock"].calls == 1


def test_detail_shows_stored_scores(client, scorers):
    client.post("/applications/A1/llm-score", json={"provider": "mock"})

    detail = client.get("/applications/A1").json()

    assert len(detail["llm_scores"]) == 1
    assert detail["llm_scores"][0]["provider"] == "mock"
    assert detail["llm_scores"][0]["score"] == 77
    assert "cached" not in detail["llm_scores"][0]


def test_failed_provider_gives_502_and_stores_nothing(client, scorers):
    response = client.post("/applications/A1/llm-score", json={"provider": "claude"})

    assert response.status_code == 502
    assert response.json() == {"detail": "Claude is down"}
    assert client.get("/applications/A1").json()["llm_scores"] == []


def test_provider_without_config_gives_502(client):
    app.dependency_overrides[available_scorers] = lambda: {"mock": CountingScorer()}
    try:
        response = client.post(
            "/applications/A1/llm-score", json={"provider": "claude"}
        )
    finally:
        app.dependency_overrides.pop(available_scorers, None)

    assert response.status_code == 502
    assert response.json() == {"detail": "claude is not configured on this server"}


def test_stored_score_is_returned_even_when_the_provider_is_gone(client, scorers):
    client.post("/applications/A1/llm-score", json={"provider": "mock"})
    app.dependency_overrides[available_scorers] = lambda: {}
    try:
        response = client.post("/applications/A1/llm-score", json={"provider": "mock"})
    finally:
        app.dependency_overrides.pop(available_scorers, None)

    assert response.status_code == 200
    assert response.json()["cached"] is True


def test_each_provider_gets_its_own_row(client, scorers):
    scorers["claude"] = CountingScorer()
    scorers["claude"].provider = "claude"

    client.post("/applications/A1/llm-score", json={"provider": "mock"})
    client.post("/applications/A1/llm-score", json={"provider": "claude"})

    providers = [
        row["provider"] for row in client.get("/applications/A1").json()["llm_scores"]
    ]
    assert sorted(providers) == ["claude", "mock"]


@pytest.mark.parametrize(
    "payload", [{"provider": "gpt9"}, {}, {"provider": "mock", "extra": 1}]
)
def test_bad_body_is_rejected(client, scorers, payload):
    assert client.post("/applications/A1/llm-score", json=payload).status_code == 422


def test_unknown_application_gives_404(client, scorers):
    response = client.post("/applications/NOPE/llm-score", json={"provider": "mock"})

    assert response.status_code == 404


def test_providers_endpoint_lists_what_is_configured(client, scorers):
    response = client.get("/llm-providers")

    assert response.status_code == 200
    assert response.json() == [
        {"id": "mock", "label": "Counting", "model": "counting-v1"},
        {"id": "claude", "label": "Failing", "model": "failing-v1"},
    ]
