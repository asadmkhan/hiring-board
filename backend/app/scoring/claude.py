import anthropic
from pydantic import BaseModel, Field, ValidationError

from app.models import Candidate, Job
from app.schemas import LlmProviderId
from app.scoring.base import ScoreResult, ScoringError
from app.scoring.prompt import SYSTEM_PROMPT, build_prompt


class ClaudeAnswer(BaseModel):
    score: int = Field(description="Fit score from 0 to 100.")
    reason: str = Field(description="One sentence explaining the score.")


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
                output_format=ClaudeAnswer,
            )
        except anthropic.AuthenticationError as e:
            raise ScoringError("Claude rejected the API key.") from e
        except anthropic.APIConnectionError as e:
            raise ScoringError("Could not reach Claude.") from e
        except anthropic.APIStatusError as e:
            raise ScoringError(f"Claude returned an error ({e.status_code}).") from e
        except (anthropic.AnthropicError, ValidationError) as e:
            raise ScoringError("Claude returned an invalid answer.") from e

        answer = response.parsed_output
        if answer is None or not 0 <= answer.score <= 100 or not answer.reason.strip():
            raise ScoringError("Claude returned an invalid answer.")
        return ScoreResult(score=answer.score, reason=answer.reason.strip())
