from app.config import Settings


def test_frontend_origin_accepts_a_comma_separated_list():
    settings = Settings(frontend_origin=" http://localhost:8080/, http://localhost:5173 ,")

    assert settings.frontend_origins == ["http://localhost:8080", "http://localhost:5173"]
