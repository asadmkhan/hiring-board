import httpx2

from app.models import Candidate, Job
from app.schemas import LlmProviderId
from app.scoring.base import ModelAnswer, ScoreResult, ScoringError, result_from
from app.scoring.prompt import SYSTEM_PROMPT, build_prompt


class OllamaScorer:
    provider = LlmProviderId.OLLAMA
    label = "Ollama (local)"

    def __init__(self, url: str, model: str, client: httpx2.Client | None = None):
        self.model = model
        # A stopped Ollama shows up within 2 seconds. A running local model may need a while to answer.
        timeout = httpx2.Timeout(connect=2.0, read=60.0, write=5.0, pool=5.0)
        self.client = client or httpx2.Client(base_url=url.rstrip("/"), timeout=timeout)

    def score(self, job: Job, candidate: Candidate) -> ScoreResult:
        body = {
            "model": self.model,
            "stream": False,
            "format": ModelAnswer.model_json_schema(),
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt(job, candidate)},
            ],
        }
        try:
            response = self.client.post("/api/chat", json=body)
        except (httpx2.ConnectError, httpx2.ConnectTimeout) as e:
            raise ScoringError("Ollama is not running on this machine.") from e
        except httpx2.TimeoutException as e:
            raise ScoringError("Ollama took too long to answer.") from e
        except httpx2.HTTPError as e:
            raise ScoringError("Could not talk to Ollama.") from e

        if response.status_code == 404:
            raise ScoringError(f"Ollama does not have the model {self.model}. Run: ollama pull {self.model}")
        if response.status_code >= 400:
            raise ScoringError(f"Ollama returned an error ({response.status_code}).")

        try:
            answer = ModelAnswer.model_validate_json(response.json()["message"]["content"])
        except (ValueError, KeyError, TypeError) as e:
            raise ScoringError("Ollama returned an invalid answer.") from e
        return result_from(answer, "Ollama")
