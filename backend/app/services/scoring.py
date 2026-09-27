from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import queries
from app.models import Application, LlmScore
from app.scoring.base import Scorer, ScoringError


def score_application(
    session: Session, application: Application, provider: str, scorer: Scorer | None
) -> tuple[LlmScore, bool]:
    """Return the stored score for this provider, or call the model once and store the result.

    The second value says whether the score came from the store.
    """
    existing = queries.get_llm_score(session, application.application_id, provider)
    if existing is not None:
        return existing, True
    if scorer is None:
        raise ScoringError(f"{provider} is not configured on this server")

    job, candidate = application.job, application.candidate
    # Let go of the database transaction while the model call runs.
    session.rollback()
    result = scorer.score(job, candidate)

    row = LlmScore(
        application_id=application.application_id,
        provider=provider,
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
        winner = queries.get_llm_score(session, application.application_id, provider)
        if winner is None:
            raise ScoringError("The score could not be stored. Try again.") from e
        return winner, True
    return row, False
