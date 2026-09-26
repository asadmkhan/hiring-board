from types import SimpleNamespace

import anthropic
import httpx2
import pytest

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


def test_claude_scorer_uses_haiku_and_returns_the_parsed_answer():
    client = fake_client(answer=ClaudeAnswer(score=82, reason=" Good fit. "))
    scorer = ClaudeScorer(api_key="test", client=client)

    result = scorer.score(JOB, ANNA)

    assert result.score == 82
    assert result.reason == "Good fit."
    sent = client.messages.kwargs
    assert sent["model"] == "claude-haiku-4-5"
    assert sent["output_format"] is ClaudeAnswer
    assert "Anna" not in sent["messages"][0]["content"]


def test_claude_scorer_rejects_a_score_out_of_range():
    client = fake_client(answer=ClaudeAnswer(score=140, reason="Too good."))

    with pytest.raises(ScoringError, match="invalid answer"):
        ClaudeScorer(api_key="test", client=client).score(JOB, ANNA)


def test_claude_scorer_turns_sdk_errors_into_scoring_errors():
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    client = fake_client(error=anthropic.APIConnectionError(request=request))

    with pytest.raises(ScoringError, match="Could not reach Claude"):
        ClaudeScorer(api_key="test", client=client).score(JOB, ANNA)
