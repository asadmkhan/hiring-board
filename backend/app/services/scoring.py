from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Application, LlmScore
from app.scoring.base import Scorer, ScoringError


def score_application(session: Session, application: Application, scorer: Scorer) -> tuple[LlmScore, bool]:
    """Return the stored score for this provider, or call the model once and store the result.

    The second value says whether the score came from the store.
    """
    existing = _stored_score(session, application, scorer.provider)
    if existing is not None:
        return existing, True

    result = scorer.score(application.job, application.candidate)
    row = LlmScore(
        application_id=application.application_id,
        provider=scorer.provider,
        model=scorer.model,
        score=result.score,
        reason=result.reason,
        scored_at=datetime.now().replace(microsecond=0),
    )
    session.add(row)
    try:
        session.commit()
    except IntegrityError as e:
        # Two clicks raced and the other one won. Hand back what it stored.
        session.rollback()
        winner = _stored_score(session, application, scorer.provider)
        if winner is None:
            raise ScoringError("The score could not be stored. Try again.") from e
        return winner, True
    return row, False


def _stored_score(session: Session, application: Application, provider: str) -> LlmScore | None:
    stmt = select(LlmScore).where(
        LlmScore.application_id == application.application_id,
        LlmScore.provider == provider,
    )
    return session.scalar(stmt)
