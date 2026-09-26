from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import queries
from app.db import get_session
from app.models import Application
from app.schemas import (
    ApplicationDetail,
    ApplicationFilters,
    ApplicationPage,
    ApplicationUpdate,
    ApplicationLlmScore,
    LlmScoreRequest,
    LlmScoreResponse,
)
from app.scoring.base import ScoringError
from app.scoring.registry import ScorersDep
from app.services import applications as application_service
from app.services import scoring as scoring_service

router = APIRouter(prefix="/applications", tags=["applications"])

SessionDep = Annotated[Session, Depends(get_session)]


def application_or_404(application_id: str, session: SessionDep) -> Application:
    application = queries.get_application(session, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


ApplicationDep = Annotated[Application, Depends(application_or_404)]


@router.get("", response_model=ApplicationPage)
def list_applications(filters: Annotated[ApplicationFilters, Query()], session: SessionDep):
    rows, total = queries.list_applications(session, filters)
    return ApplicationPage(items=rows, total=total, page=filters.page, page_size=filters.page_size)


@router.get("/{application_id}", response_model=ApplicationDetail)
def get_application(application: ApplicationDep):
    return application


@router.patch("/{application_id}", response_model=ApplicationDetail)
def update_application(application: ApplicationDep, update: ApplicationUpdate, session: SessionDep):
    return application_service.update_application(session, application, update)


@router.post("/{application_id}/llm-score", response_model=LlmScoreResponse)
def llm_score(application: ApplicationDep, body: LlmScoreRequest, session: SessionDep, scorers: ScorersDep):
    scorer = scorers.get(body.provider)
    if scorer is None:
        raise HTTPException(status_code=502, detail=f"{body.provider} is not configured on this server")
    try:
        row, cached = scoring_service.score_application(session, application, scorer)
    except ScoringError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    return LlmScoreResponse(cached=cached, **ApplicationLlmScore.model_validate(row).model_dump())
