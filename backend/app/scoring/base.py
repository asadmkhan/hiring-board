from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, Field

from app.models import Candidate, Job


@dataclass
class ScoreResult:
    score: int
    reason: str


class ScoringError(Exception):
    """The provider could not give a score. The message is safe to show to the user."""


class ModelAnswer(BaseModel):
    """What every model must return."""

    score: int = Field(description="Fit score from 0 to 100.")
    reason: str = Field(description="One short plain sentence a recruiter would say out loud. No dashes.")


def result_from(answer: ModelAnswer | None, provider_name: str) -> ScoreResult:
    if answer is None or not 0 <= answer.score <= 100 or not answer.reason.strip():
        raise ScoringError(f"{provider_name} returned an invalid answer.")
    return ScoreResult(score=answer.score, reason=answer.reason.strip())


class Scorer(Protocol):
    provider: str
    label: str
    model: str

    def score(self, job: Job, candidate: Candidate) -> ScoreResult: ...
