"""Small hand-made data set shared by the endpoint tests."""

from datetime import datetime

from app.models import Application, Candidate, Job


def jobs():
    return [
        Job(
            job_id="J1",
            title="Warehouse Associate",
            job_family="Logistics",
            seniority="junior",
            country="DE",
            city="Hamburg",
            created_at=datetime(2026, 1, 1, 9, 0),
        ),
        Job(
            job_id="J2",
            title="Backend Developer",
            job_family="IT",
            seniority="mid",
            country="AT",
            city="Vienna",
            created_at=datetime(2026, 1, 2, 9, 0),
        ),
        Job(
            job_id="J3",
            title="Nurse",
            job_family="Healthcare",
            seniority="senior",
            country="DE",
            city="Berlin",
            created_at=datetime(2026, 1, 3, 9, 0),
        ),
    ]


def candidates():
    return [
        Candidate(
            candidate_id="C1",
            full_name="Anna Adler",
            email="anna@example.com",
            country="DE",
            city="Hamburg",
            years_experience=3,
            preferred_job_family="Logistics",
        ),
        Candidate(
            candidate_id="C2",
            full_name="Ben Bauer",
            email="ben@example.com",
            country="AT",
            city="Vienna",
            years_experience=6,
            preferred_job_family="IT",
        ),
        Candidate(
            candidate_id="C3",
            full_name="Cara Conti",
            email="cara@example.com",
            country="DE",
            city="Berlin",
            years_experience=10,
            preferred_job_family="Healthcare",
        ),
    ]


def application(app_id, job_id, candidate_id, day, score, status, updated=None):
    return Application(
        application_id=app_id,
        job_id=job_id,
        candidate_id=candidate_id,
        created_at=datetime(2026, 3, day, 9, 0),
        source="job_board",
        match_score=score,
        match_band="medium",
        status=status,
        status_updated_at=updated,
    )


# Scores tie on 0.5 and 0.7, A5 and A6 share a date, C1 applied to J1 twice.
def applications():
    return [
        application("A1", "J1", "C1", 1, 0.5, "new"),
        application("A2", "J1", "C2", 2, 0.7, "in_review", datetime(2026, 3, 3, 9, 0)),
        application("A3", "J2", "C1", 3, 0.5, "new"),
        application(
            "A4", "J2", "C3", 4, 0.9, "shortlisted", datetime(2026, 3, 5, 9, 0)
        ),
        application("A5", "J3", "C2", 5, 0.3, "rejected", datetime(2026, 3, 6, 9, 0)),
        application("A6", "J3", "C3", 5, 0.5, "hired", datetime(2026, 3, 7, 9, 0)),
        application("A7", "J1", "C3", 6, 0.7, "new"),
        application("A8", "J1", "C1", 7, 0.1, "new"),
    ]


def seed_data(session):
    session.add_all(jobs() + candidates() + applications())
    session.commit()
