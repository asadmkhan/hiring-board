from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Application, Candidate, Job
from scripts.import_csv import load_csvs


def count_rows(session, model):
    return session.scalar(select(func.count()).select_from(model))


def test_loads_every_row(sqlite_engine):
    counts = load_csvs(sqlite_engine)

    assert counts == {"jobs": 40, "candidates": 400, "applications": 900}
    with Session(sqlite_engine) as session:
        assert count_rows(session, Job) == 40
        assert count_rows(session, Candidate) == 400
        assert count_rows(session, Application) == 900


def test_parses_values(sqlite_engine):
    load_csvs(sqlite_engine)

    with Session(sqlite_engine) as session:
        app = session.get(Application, "A0001")
        assert app.job_id == "J031"
        assert app.candidate_id == "C0214"
        assert app.created_at == datetime(2026, 5, 31, 9, 30)
        assert app.status_updated_at == datetime(2026, 6, 7, 9, 30)
        assert app.match_score == 0.83
        assert app.note is None


def test_new_applications_have_no_status_date(sqlite_engine):
    load_csvs(sqlite_engine)

    with Session(sqlite_engine) as session:
        new_rows = session.scalars(select(Application).where(Application.status == "new")).all()
        other_rows = session.scalars(select(Application).where(Application.status != "new")).all()

    assert len(new_rows) == 286
    assert all(row.status_updated_at is None for row in new_rows)
    assert all(row.status_updated_at is not None for row in other_rows)


def test_keeps_repeat_applications(sqlite_engine):
    load_csvs(sqlite_engine)

    repeated = (
        select(Application.candidate_id, Application.job_id)
        .group_by(Application.candidate_id, Application.job_id)
        .having(func.count() > 1)
    )
    with Session(sqlite_engine) as session:
        assert len(session.execute(repeated).all()) == 36


def test_load_twice_gives_same_result(sqlite_engine):
    load_csvs(sqlite_engine)
    counts = load_csvs(sqlite_engine)

    assert counts == {"jobs": 40, "candidates": 400, "applications": 900}
    with Session(sqlite_engine) as session:
        assert count_rows(session, Application) == 900
