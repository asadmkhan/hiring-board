"""Wipe the database and load the three CSV files. Run from backend/:

    uv run python -m scripts.import_csv
"""

import csv
from datetime import datetime
from pathlib import Path

from sqlalchemy import insert
from sqlalchemy.engine import Engine

from app.db import Base, engine
from app.models import Application, Candidate, Job

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_datetime(value: str) -> datetime | None:
    return datetime.strptime(value, "%Y-%m-%d %H:%M") if value else None


def load_csvs(db_engine: Engine, data_dir: Path = DATA_DIR) -> dict[str, int]:
    jobs = read_rows(data_dir / "jobs.csv")
    candidates = read_rows(data_dir / "candidates.csv")
    applications = read_rows(data_dir / "applications.csv")

    for row in jobs:
        row["created_at"] = parse_datetime(row["created_at"])
    for row in candidates:
        row["years_experience"] = int(row["years_experience"])
    for row in applications:
        row["created_at"] = parse_datetime(row["created_at"])
        row["status_updated_at"] = parse_datetime(row["status_updated_at"])
        row["match_score"] = float(row["match_score"])

    Base.metadata.drop_all(db_engine)
    Base.metadata.create_all(db_engine)
    with db_engine.begin() as conn:
        conn.execute(insert(Job), jobs)
        conn.execute(insert(Candidate), candidates)
        conn.execute(insert(Application), applications)

    return {"jobs": len(jobs), "candidates": len(candidates), "applications": len(applications)}


if __name__ == "__main__":
    counts = load_csvs(engine)
    print(", ".join(f"{n} {table}" for table, n in counts.items()))
