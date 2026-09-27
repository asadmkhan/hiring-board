from fastapi import APIRouter

from app.schemas import LlmProvider
from app.scoring.registry import ScorersDep

router = APIRouter(tags=["scoring"])


@router.get("/llm-providers", response_model=list[LlmProvider])
def list_providers(scorers: ScorersDep):
    return [
        LlmProvider(id=s.provider, label=s.label, model=s.model)
        for s in scorers.values()
    ]
