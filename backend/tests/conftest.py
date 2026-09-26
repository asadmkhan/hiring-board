import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import Base, get_session
from app.main import app


@pytest.fixture
def sqlite_engine():
    # In-memory SQLite. StaticPool keeps every session on the same connection.
    engine = create_engine(
        "sqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    yield engine
    engine.dispose()


@pytest.fixture
def session(sqlite_engine):
    Base.metadata.create_all(sqlite_engine)
    with Session(sqlite_engine) as session:
        yield session


@pytest.fixture
def client(session):
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
