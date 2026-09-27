from types import SimpleNamespace

import anthropic
import httpx2
import pytest
from pydantic import ValidationError

from app.scoring.base import ScoringError
from app.scoring.claude import ClaudeAnswer, ClaudeScorer
from app.scoring.mock import MockScorer
from app.scoring.prompt import build_prompt
from tests.seed import candidates, jobs

JOB = jobs()[0]  # Warehouse Associate, Logistics, junior, Hamburg DE
ANNA = candidates()[0]  # 3 years, prefers Logistics, Hamburg DE
BEN = candidates()[1]  # 6 years, prefers IT, Vienna AT


def test_prompt_has_the_facts_and_no_personal_data():
    prompt = build_prompt(JOB, ANNA)

    assert "Warehouse Associate, Logistics, junior, Hamburg (DE)" in prompt
    assert "3 years experience, prefers Logistics, based in Hamburg (DE)" in prompt
    assert "Anna" not in prompt
    assert "example.com" not in prompt


def test_mock_is_deterministic_and_in_range():
    scorer = MockScorer()

    first = scorer.score(JOB, ANNA)
    second = scorer.score(JOB, ANNA)

    assert first == second
    assert first.score == 100
    assert 0 <= scorer.score(JOB, BEN).score <= 100
    assert scorer.score(JOB, BEN).score < first.score


def test_mock_skips_the_experience_bonus_for_an_unknown_seniority():
    lead_job = jobs()[0]
    lead_job.seniority = "lead"

    result = MockScorer().score(lead_job, ANNA)

    assert result.score == 85
    assert "experience" not in result.reason


class FakeMessages:
    def __init__(self, answer=None, error=None):
        self.answer = answer
        self.error = error
        self.kwargs = None

    def parse(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return SimpleNamespace(parsed_output=self.answer)


def fake_client(**kwargs):
    return SimpleNamespace(messages=FakeMessages(**kwargs))


def claude_with(**kwargs) -> ClaudeScorer:
    return ClaudeScorer(
        api_key="test", model="claude-haiku-4-5", client=fake_client(**kwargs)
    )


def test_claude_scorer_uses_the_configured_model_and_returns_the_parsed_answer():
    scorer = claude_with(answer=ClaudeAnswer(score=82, reason=" Good fit. "))

    result = scorer.score(JOB, ANNA)

    assert result.score == 82
    assert result.reason == "Good fit."
    sent = scorer.client.messages.kwargs
    assert sent["model"] == "claude-haiku-4-5"
    assert sent["output_format"] is ClaudeAnswer
    assert "Anna" not in sent["messages"][0]["content"]


def test_claude_client_has_a_timeout_and_one_retry():
    scorer = ClaudeScorer(api_key="test", model="claude-haiku-4-5")

    assert scorer.client.timeout == 20.0
    assert scorer.client.max_retries == 1


@pytest.mark.parametrize(
    "answer",
    [
        ClaudeAnswer(score=140, reason="Too good."),
        ClaudeAnswer(score=-1, reason="Below zero."),
        ClaudeAnswer(score=60, reason="   "),
        None,
    ],
)
def test_claude_scorer_rejects_a_bad_answer(answer):
    with pytest.raises(ScoringError, match="invalid answer"):
        claude_with(answer=answer).score(JOB, ANNA)


def request():
    return httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def status_error(cls, status):
    response = httpx2.Response(status, request=request())
    return cls("boom", response=response, body=None)


def validation_error():
    try:
        ClaudeAnswer.model_validate({"score": "not a number", "reason": 1})
    except ValidationError as e:
        return e
    raise AssertionError("expected a validation error")


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (anthropic.APIConnectionError(request=request()), "Could not reach Claude"),
        (status_error(anthropic.AuthenticationError, 401), "rejected the API key"),
        (status_error(anthropic.RateLimitError, 429), "returned an error \\(429\\)"),
        (validation_error(), "invalid answer"),
        (anthropic.AnthropicError("something else"), "invalid answer"),
    ],
)
def test_claude_scorer_turns_every_failure_into_a_scoring_error(error, message):
    with pytest.raises(ScoringError, match=message):
        claude_with(error=error).score(JOB, ANNA)
