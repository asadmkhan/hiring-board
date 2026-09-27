from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.config import settings
from app.scoring.base import Scorer
from app.scoring.claude import ClaudeScorer
from app.scoring.mock import MockScorer
from app.scoring.ollama import OllamaScorer
from app.scoring.openai import OpenAIScorer


@lru_cache
def available_scorers() -> dict[str, Scorer]:
    scorers: list[Scorer] = [MockScorer()]
    claude_key = settings.anthropic_api_key.get_secret_value()
    if claude_key:
        scorers.append(ClaudeScorer(claude_key, settings.claude_model))
    openai_key = settings.openai_api_key.get_secret_value()
    if openai_key:
        scorers.append(OpenAIScorer(openai_key, settings.openai_model))
    if settings.ollama_url:
        scorers.append(OllamaScorer(settings.ollama_url, settings.ollama_model))
    return {scorer.provider: scorer for scorer in scorers}


ScorersDep = Annotated[dict[str, Scorer], Depends(available_scorers)]
