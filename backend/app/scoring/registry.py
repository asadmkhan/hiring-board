from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.config import settings
from app.scoring.base import Scorer
from app.scoring.claude import ClaudeScorer
from app.scoring.mock import MockScorer


@lru_cache
def available_scorers() -> dict[str, Scorer]:
    scorers: dict[str, Scorer] = {"mock": MockScorer()}
    claude_key = settings.anthropic_api_key.get_secret_value()
    if claude_key:
        scorers["claude"] = ClaudeScorer(claude_key)
    return scorers


ScorersDep = Annotated[dict[str, Scorer], Depends(available_scorers)]
