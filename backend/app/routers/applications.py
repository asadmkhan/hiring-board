from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import queries
from app.db import get_session
from app.schemas import ApplicationFilters, ApplicationPage

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=ApplicationPage)
def list_applications(
    filters: Annotated[ApplicationFilters, Query()],
    session: Annotated[Session, Depends(get_session)],
):
    rows, total = queries.list_applications(session, filters)
    return ApplicationPage(items=rows, total=total, page=filters.page, page_size=filters.page_size)
