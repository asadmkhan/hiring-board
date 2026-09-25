from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Job(Base):
    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str]
    job_family: Mapped[str]
    seniority: Mapped[str]
    country: Mapped[str]
    city: Mapped[str]
    created_at: Mapped[datetime]


class Candidate(Base):
    __tablename__ = "candidates"

    candidate_id: Mapped[str] = mapped_column(primary_key=True)
    full_name: Mapped[str]
    email: Mapped[str]
    country: Mapped[str]
    city: Mapped[str]
    years_experience: Mapped[int]
    preferred_job_family: Mapped[str]


class Application(Base):
    __tablename__ = "applications"

    # Same candidate can apply to the same job more than once.
    application_id: Mapped[str] = mapped_column(primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.job_id"), index=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.candidate_id"), index=True)
    created_at: Mapped[datetime] = mapped_column(index=True)
    source: Mapped[str]
    match_score: Mapped[float] = mapped_column(index=True)
    match_band: Mapped[str]
    status: Mapped[str] = mapped_column(index=True)
    status_updated_at: Mapped[datetime | None]
    note: Mapped[str | None]


class LlmScore(Base):
    __tablename__ = "llm_scores"
    __table_args__ = (UniqueConstraint("application_id", "provider"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.application_id"))
    provider: Mapped[str]
    model: Mapped[str]
    score: Mapped[int]
    reason: Mapped[str]
    scored_at: Mapped[datetime]
