from app.models import Candidate, Job

SYSTEM_PROMPT = (
    "You score how well a candidate fits a job for a staffing agency. Be strict and concise. "
    "Give a score from 0 to 100 and a one-sentence reason."
)


# No name or email goes to the model.
def build_prompt(job: Job, candidate: Candidate) -> str:
    return (
        f"Job: {job.title}, {job.job_family}, {job.seniority}, {job.city} ({job.country}).\n"
        f"Candidate: {candidate.years_experience} years experience, "
        f"prefers {candidate.preferred_job_family}, based in {candidate.city} ({candidate.country}).\n"
        "Score the fit."
    )
