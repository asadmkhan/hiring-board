import json
from types import SimpleNamespace

import anthropic
import httpx2
import openai
import pytest
from pydantic import ValidationError

from app.scoring.base import ModelAnswer, ScoringError
from app.scoring.claude import ClaudeScorer
from app.scoring.mock import MockScorer
from app.scoring.ollama import OllamaScorer
from app.scoring.openai import OpenAIScorer
from app.scoring.prompt import build_prompt
from tests.seed import candidates, jobs

JOB = jobs()[0]  # Warehouse Associate, Logistics, junior, Hamburg DE
ANNA = candidates()[0]  # 3 years, prefers Logistics, Hamburg DE
BEN = candidates()[1]  # 6 years, prefers IT, Vienna AT

BAD_ANSWERS = [
    ModelAnswer(score=140, reason="Too good."),
    ModelAnswer(score=-1, reason="Below zero."),
    ModelAnswer(score=60, reason="   "),
    None,
]


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


def validation_error():
    try:
        ModelAnswer.model_validate({"score": "not a number", "reason": 1})
    except ValidationError as e:
        return e
    raise AssertionError("expected a validation error")


# Claude


class FakeClaudeMessages:
    def __init__(self, answer=None, error=None):
        self.answer = answer
        self.error = error
        self.kwargs = None

    def parse(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return SimpleNamespace(parsed_output=self.answer)


def claude_with(**kwargs) -> ClaudeScorer:
    client = SimpleNamespace(messages=FakeClaudeMessages(**kwargs))
    return ClaudeScorer(api_key="test", model="claude-haiku-4-5", client=client)


def test_claude_scorer_uses_the_configured_model_and_returns_the_parsed_answer():
    scorer = claude_with(answer=ModelAnswer(score=82, reason=" Good fit. "))

    result = scorer.score(JOB, ANNA)

    assert result.score == 82
    assert result.reason == "Good fit."
    sent = scorer.client.messages.kwargs
    assert sent["model"] == "claude-haiku-4-5"
    assert sent["output_format"] is ModelAnswer
    assert "Anna" not in sent["messages"][0]["content"]


def test_claude_client_has_a_timeout_and_one_retry():
    scorer = ClaudeScorer(api_key="test", model="claude-haiku-4-5")

    assert scorer.client.timeout == 20.0
    assert scorer.client.max_retries == 1


@pytest.mark.parametrize("answer", BAD_ANSWERS)
def test_claude_scorer_rejects_a_bad_answer(answer):
    with pytest.raises(ScoringError, match="invalid answer"):
        claude_with(answer=answer).score(JOB, ANNA)


def anthropic_request():
    return httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def anthropic_status_error(cls, status):
    response = httpx2.Response(status, request=anthropic_request())
    return cls("boom", response=response, body=None)


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (anthropic.APIConnectionError(request=anthropic_request()), "Could not reach Claude"),
        (anthropic_status_error(anthropic.AuthenticationError, 401), "rejected the API key"),
        (anthropic_status_error(anthropic.RateLimitError, 429), "returned an error \\(429\\)"),
        (validation_error(), "invalid answer"),
        (anthropic.AnthropicError("something else"), "invalid answer"),
    ],
)
def test_claude_scorer_turns_every_failure_into_a_scoring_error(error, message):
    with pytest.raises(ScoringError, match=message):
        claude_with(error=error).score(JOB, ANNA)


# OpenAI


class FakeResponses:
    def __init__(self, answer=None, error=None):
        self.answer = answer
        self.error = error
        self.kwargs = None

    def parse(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return SimpleNamespace(output_parsed=self.answer)


def openai_with(**kwargs) -> OpenAIScorer:
    client = SimpleNamespace(responses=FakeResponses(**kwargs))
    return OpenAIScorer(api_key="test", model="gpt-6-luna", client=client)


def test_openai_scorer_uses_the_configured_model_and_returns_the_parsed_answer():
    scorer = openai_with(answer=ModelAnswer(score=64, reason=" Fair fit. "))

    result = scorer.score(JOB, ANNA)

    assert result.score == 64
    assert result.reason == "Fair fit."
    sent = scorer.client.responses.kwargs
    assert sent["model"] == "gpt-6-luna"
    assert sent["text_format"] is ModelAnswer
    assert "Anna" not in sent["input"]


def test_openai_client_has_a_timeout_and_one_retry():
    scorer = OpenAIScorer(api_key="test", model="gpt-6-luna")

    assert scorer.client.timeout == 20.0
    assert scorer.client.max_retries == 1


@pytest.mark.parametrize("answer", BAD_ANSWERS)
def test_openai_scorer_rejects_a_bad_answer(answer):
    with pytest.raises(ScoringError, match="invalid answer"):
        openai_with(answer=answer).score(JOB, ANNA)


def openai_request():
    return httpx2.Request("POST", "https://api.openai.com/v1/responses")


def openai_status_error(cls, status):
    response = httpx2.Response(status, request=openai_request())
    return cls("boom", response=response, body=None)


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (openai.APIConnectionError(request=openai_request()), "Could not reach OpenAI"),
        (openai_status_error(openai.AuthenticationError, 401), "rejected the API key"),
        (openai_status_error(openai.RateLimitError, 429), "returned an error \\(429\\)"),
        (openai_status_error(openai.InternalServerError, 500), "returned an error \\(500\\)"),
        (openai.APITimeoutError(request=openai_request()), "Could not reach OpenAI"),
        (validation_error(), "invalid answer"),
        (openai.OpenAIError("something else"), "invalid answer"),
    ],
)
def test_openai_scorer_turns_every_failure_into_a_scoring_error(error, message):
    with pytest.raises(ScoringError, match=message):
        openai_with(error=error).score(JOB, ANNA)


# Ollama


def ollama_with(handler) -> OllamaScorer:
    client = httpx2.Client(base_url="http://ollama.test", transport=httpx2.MockTransport(handler))
    return OllamaScorer(url="http://ollama.test", model="llama3.2:3b", client=client)


def ollama_reply(content: str, status: int = 200):
    def handler(request: httpx2.Request) -> httpx2.Response:
        handler.body = json.loads(request.content)
        return httpx2.Response(status, json={"message": {"role": "assistant", "content": content}})

    return handler


def test_ollama_scorer_sends_the_schema_and_returns_the_answer():
    handler = ollama_reply(json.dumps({"score": 71, "reason": " Decent match. "}))
    scorer = ollama_with(handler)

    result = scorer.score(JOB, ANNA)

    assert result.score == 71
    assert result.reason == "Decent match."
    assert handler.body["model"] == "llama3.2:3b"
    assert handler.body["stream"] is False
    assert handler.body["format"]["properties"].keys() == {"score", "reason"}
    assert "Anna" not in handler.body["messages"][1]["content"]


def test_ollama_client_fails_fast_when_not_running():
    scorer = OllamaScorer(url="http://localhost:11434", model="llama3.2:3b")

    assert scorer.client.timeout.connect == 2.0
    assert scorer.client.timeout.read == 60.0


@pytest.mark.parametrize(
    ("content", "status", "message"),
    [
        ("not json", 200, "invalid answer"),
        (json.dumps({"score": 140, "reason": "Too good."}), 200, "invalid answer"),
        (json.dumps({"score": 60, "reason": ""}), 200, "invalid answer"),
        ("{}", 404, "does not have the model llama3.2:3b"),
        ("{}", 500, "returned an error \\(500\\)"),
    ],
)
def test_ollama_scorer_turns_bad_replies_into_scoring_errors(content, status, message):
    with pytest.raises(ScoringError, match=message):
        ollama_with(ollama_reply(content, status)).score(JOB, ANNA)


@pytest.mark.parametrize(
    "response",
    [
        httpx2.Response(200, text="<html>not json</html>"),
        httpx2.Response(200, json={}),
        httpx2.Response(200, json={"message": {"role": "assistant"}}),
    ],
)
def test_ollama_scorer_rejects_a_reply_with_the_wrong_shape(response):
    with pytest.raises(ScoringError, match="invalid answer"):
        ollama_with(lambda request: response).score(JOB, ANNA)



@pytest.mark.parametrize(
    ("error", "message"),
    [
        (httpx2.ConnectError, "Ollama is not running on this machine"),
        (httpx2.ConnectTimeout, "Ollama is not running on this machine"),
        (httpx2.ReadTimeout, "took too long"),
        (httpx2.RemoteProtocolError, "Could not talk to Ollama"),
    ],
)
def test_ollama_scorer_reports_connection_problems(error, message):
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise error("boom", request=request)

    with pytest.raises(ScoringError, match=message):
        ollama_with(handler).score(JOB, ANNA)
