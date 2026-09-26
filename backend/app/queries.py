from sqlalchemy import func, select
from sqlalchemy.orm import Session, contains_eager

from app.models import Application, Job
from app.schemas import ApplicationFilters

SORT_COLUMNS = {
    "created_at": Application.created_at,
    "match_score": Application.match_score,
}


def list_applications(session: Session, filters: ApplicationFilters) -> tuple[list[Application], int]:
    stmt = select(Application).join(Application.job).join(Application.candidate)
    if filters.status:
        stmt = stmt.where(Application.status == filters.status)
    if filters.country:
        stmt = stmt.where(Job.country == filters.country)
    if filters.job_family:
        stmt = stmt.where(Job.job_family == filters.job_family)

    total = session.scalar(select(func.count()).select_from(stmt.subquery()))

    # Second key keeps the order stable across pages when scores or dates tie.
    order_by = [SORT_COLUMNS[filters.sort], Application.application_id]
    if filters.order == "desc":
        order_by = [column.desc() for column in order_by]

    stmt = (
        stmt.options(contains_eager(Application.job), contains_eager(Application.candidate))
        .order_by(*order_by)
        .offset((filters.page - 1) * filters.page_size)
        .limit(filters.page_size)
    )
    return list(session.scalars(stmt)), total
