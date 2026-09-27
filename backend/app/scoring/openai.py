import openai
from pydantic import ValidationError

from app.models import Candidate, Job
from app.schemas import LlmProviderId
from app.scoring.base import ModelAnswer, ScoreResult, ScoringError, result_from
from app.scoring.prompt import SYSTEM_PROMPT, build_prompt


class OpenAIScorer:
    provider = LlmProviderId.OPENAI
    label = "OpenAI"

    def __init__(self, api_key: str, model: str, client: openai.OpenAI | None = None):
        self.model = model
        self.client = client or openai.OpenAI(api_key=api_key, timeout=20.0, max_retries=1)

    def score(self, job: Job, candidate: Candidate) -> ScoreResult:
        try:
            response = self.client.responses.parse(
                model=self.model,
                instructions=SYSTEM_PROMPT,
                input=build_prompt(job, candidate),
                text_format=ModelAnswer,
                max_output_tokens=1024,
            )
        except openai.AuthenticationError as e:
            raise ScoringError("OpenAI rejected the API key.") from e
        except openai.APIConnectionError as e:
            raise ScoringError("Could not reach OpenAI.") from e
        except openai.APIStatusError as e:
            raise ScoringError(f"OpenAI returned an error ({e.status_code}).") from e
        except (openai.OpenAIError, ValidationError) as e:
            raise ScoringError("OpenAI returned an invalid answer.") from e

        return result_from(response.output_parsed, "OpenAI")
