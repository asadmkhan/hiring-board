import anthropic
from pydantic import ValidationError

from app.models import Candidate, Job
from app.schemas import LlmProviderId
from app.scoring.base import ModelAnswer, ScoreResult, ScoringError, result_from
from app.scoring.prompt import SYSTEM_PROMPT, build_prompt


class ClaudeScorer:
    provider = LlmProviderId.CLAUDE
    label = "Claude"

    def __init__(
        self, api_key: str, model: str, client: anthropic.Anthropic | None = None
    ):
        self.model = model
        self.client = client or anthropic.Anthropic(
            api_key=api_key, timeout=20.0, max_retries=1
        )

    def score(self, job: Job, candidate: Candidate) -> ScoreResult:
        try:
            response = self.client.messages.parse(
                model=self.model,
                max_tokens=256,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": build_prompt(job, candidate)}],
                output_format=ModelAnswer,
            )
        except anthropic.AuthenticationError as e:
            raise ScoringError("Claude rejected the API key.") from e
        except anthropic.APIConnectionError as e:
            raise ScoringError("Could not reach Claude.") from e
        except anthropic.APIStatusError as e:
            raise ScoringError(f"Claude returned an error ({e.status_code}).") from e
        except (anthropic.AnthropicError, ValidationError) as e:
            raise ScoringError("Claude returned an invalid answer.") from e

        return result_from(response.parsed_output, "Claude")
