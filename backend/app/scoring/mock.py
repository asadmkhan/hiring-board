from app.models import Candidate, Job
from app.schemas import LlmProviderId
from app.scoring.base import ScoreResult

YEARS_NEEDED = {"junior": 0, "mid": 3, "senior": 7}


class MockScorer:
    """Deterministic stand-in for a model."""

    provider = LlmProviderId.MOCK
    label = "Mock (no model call)"
    model = "mock-rules-v1"

    def score(self, job: Job, candidate: Candidate) -> ScoreResult:
        score = 50
        matches = []
        if candidate.preferred_job_family == job.job_family:
            score += 20
            matches.append("prefers this job family")
        if candidate.country == job.country:
            score += 15
            matches.append("same country")
        years_needed = YEARS_NEEDED.get(job.seniority)
        if years_needed is not None and candidate.years_experience >= years_needed:
            score += 15
            matches.append(f"enough experience for a {job.seniority} role")
        reason = (
            "Mock score: "
            + (", ".join(matches) if matches else "no strong match")
            + "."
        )
        return ScoreResult(score=score, reason=reason)
