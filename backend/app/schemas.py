from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ApplicationStatus(StrEnum):
    NEW = "new"
    IN_REVIEW = "in_review"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    HIRED = "hired"


class ApplicationFilters(BaseModel):
    status: ApplicationStatus | None = Field(None, description="Application status.")
    country: str | None = Field(None, description="Job country, DE or AT.")
    job_family: str | None = Field(None, description="Job family, for example Logistics.")
    sort: Literal["created_at", "match_score"] = Field("created_at", description="Sort field.")
    order: Literal["asc", "desc"] = Field("desc", description="Sort direction.")
    page: int = Field(1, ge=1, description="Page number, starts at 1.")
    page_size: int = Field(20, ge=1, le=100, description="Rows per page, max 100.")


class ApplicationCandidate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: str
    full_name: str
    email: str
    country: str
    city: str
    years_experience: int
    preferred_job_family: str


class ApplicationJob(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    title: str
    job_family: str
    seniority: str
    country: str
    city: str
    created_at: datetime


class ApplicationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: str
    created_at: datetime
    source: str
    match_score: float
    match_band: str
    status: ApplicationStatus
    status_updated_at: datetime | None
    candidate: ApplicationCandidate
    job: ApplicationJob


class ApplicationDetail(ApplicationListItem):
    note: str | None


class ApplicationPage(BaseModel):
    items: list[ApplicationListItem]
    total: int
    page: int
    page_size: int
