from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ApplicationStatus(StrEnum):
    NEW = "new"
    IN_REVIEW = "in_review"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    HIRED = "hired"


class ApplicationFilters(BaseModel):
    status: ApplicationStatus | None = Field(None, description="Application status.")
    country: str | None = Field(
        None, description="Job country code, see /filter-options."
    )
    job_family: str | None = Field(
        None, description="Job family, for example Logistics."
    )
    q: str | None = Field(
        None, max_length=100, description="Text to find in the candidate name or the job title."
    )
    sort: Literal["created_at", "match_score"] = Field(
        "created_at", description="Sort field."
    )
    order: Literal["asc", "desc"] = Field("desc", description="Sort direction.")
    page: int = Field(1, ge=1, description="Page number, starts at 1.")
    page_size: int = Field(20, ge=1, le=100, description="Rows per page, max 100.")

    @field_validator("q", mode="before")
    @classmethod
    def blank_search_means_no_search(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or None
        return value


class LlmProviderId(StrEnum):
    MOCK = "mock"
    CLAUDE = "claude"


class LlmProvider(BaseModel):
    id: LlmProviderId
    label: str
    model: str


class LlmScoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: LlmProviderId = Field(description="Which scorer to use.")


class ApplicationLlmScore(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: LlmProviderId
    model: str
    score: int
    reason: str
    scored_at: datetime


class LlmScoreResponse(ApplicationLlmScore):
    cached: bool = Field(
        description="True when the stored score was reused and no model was called."
    )


class ApplicationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ApplicationStatus | None = Field(None, description="New status.")
    note: str | None = Field(
        None, max_length=500, description="Short recruiter note. Null clears it."
    )

    @field_validator("note")
    @classmethod
    def blank_note_means_no_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def needs_at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("Send a status, a note, or both.")
        if "status" in self.model_fields_set and self.status is None:
            raise ValueError("Status cannot be null.")
        return self


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
    llm_scores: list[ApplicationLlmScore]


class ApplicationPage(BaseModel):
    items: list[ApplicationListItem]
    total: int
    page: int
    page_size: int


class FilterOptions(BaseModel):
    countries: list[str]
    job_families: list[str]
