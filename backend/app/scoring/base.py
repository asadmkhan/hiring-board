from dataclasses import dataclass
from typing import Protocol

from app.models import Candidate, Job


@dataclass
class ScoreResult:
    score: int
    reason: str


class ScoringError(Exception):
    """The provider could not give a score. The message is safe to show to the user."""


class Scorer(Protocol):
    provider: str
    label: str
    model: str

    def score(self, job: Job, candidate: Candidate) -> ScoreResult: ...
