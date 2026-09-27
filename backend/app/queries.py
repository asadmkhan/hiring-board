from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, contains_eager, joinedload, selectinload

from app.models import Application, Candidate, Job, LlmScore
from app.schemas import ApplicationFilters

SORT_COLUMNS = {
    "created_at": Application.created_at,
    "match_score": Application.match_score,
}


def list_applications(
    session: Session, filters: ApplicationFilters
) -> tuple[list[Application], int]:
    stmt = select(Application).join(Application.job).join(Application.candidate)
    if filters.status:
        stmt = stmt.where(Application.status == filters.status)
    if filters.country:
        stmt = stmt.where(Job.country == filters.country)
    if filters.job_family:
        stmt = stmt.where(Job.job_family == filters.job_family)
    if filters.q:
        pattern = f"%{escape_like(filters.q)}%"
        stmt = stmt.where(
            or_(
                Candidate.full_name.ilike(pattern, escape=LIKE_ESCAPE),
                Job.title.ilike(pattern, escape=LIKE_ESCAPE),
            )
        )

    total = session.scalar(select(func.count()).select_from(stmt.subquery()))

    # Second key keeps the order stable across pages when scores or dates tie.
    order_by = [SORT_COLUMNS[filters.sort], Application.application_id]
    if filters.order == "desc":
        order_by = [column.desc() for column in order_by]

    stmt = (
        stmt.options(
            contains_eager(Application.job), contains_eager(Application.candidate)
        )
        .order_by(*order_by)
        .offset((filters.page - 1) * filters.page_size)
        .limit(filters.page_size)
    )
    return list(session.scalars(stmt)), total


LIKE_ESCAPE = "\\"


def escape_like(text: str) -> str:
    """Make %, _ and backslash in the search text match themselves."""
    return text.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")


def get_application(session: Session, application_id: str) -> Application | None:
    stmt = (
        select(Application)
        .where(Application.application_id == application_id)
        .options(
            joinedload(Application.job),
            joinedload(Application.candidate),
            selectinload(Application.llm_scores),
        )
    )
    return session.scalar(stmt)


def distinct_job_values(session: Session) -> tuple[Sequence[str], Sequence[str]]:
    countries = session.scalars(
        select(Job.country).distinct().order_by(Job.country)
    ).all()
    families = session.scalars(
        select(Job.job_family).distinct().order_by(Job.job_family)
    ).all()
    return countries, families


def get_llm_score(
    session: Session, application_id: str, provider: str
) -> LlmScore | None:
    stmt = select(LlmScore).where(
        LlmScore.application_id == application_id, LlmScore.provider == provider
    )
    return session.scalar(stmt)
