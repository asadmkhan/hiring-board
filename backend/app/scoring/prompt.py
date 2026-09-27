from app.models import Candidate, Job

SYSTEM_PROMPT = (
    "You score how well a candidate fits a job for a staffing agency. Be strict and concise. "
    "Give a score from 0 to 100 and a one-sentence reason. "
    "Write the reason the way a recruiter would say it to a colleague: one short, plain sentence "
    "in everyday words, at most 25 words. No dashes, no semicolons, no lists of factors, "
    "no words like significant, substantial, misaligned or leverage."
)


# No name or email goes to the model.
def build_prompt(job: Job, candidate: Candidate) -> str:
    return (
        f"Job: {job.title}, {job.job_family}, {job.seniority}, {job.city} ({job.country}).\n"
        f"Candidate: {candidate.years_experience} years experience, "
        f"prefers {candidate.preferred_job_family}, based in {candidate.city} ({candidate.country}).\n"
        "Score the fit."
    )
