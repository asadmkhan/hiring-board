import pytest
from pydantic import SecretStr

from app.config import Settings, settings
from app.scoring.registry import available_scorers


@pytest.fixture(autouse=True)
def fresh_registry(monkeypatch):
    monkeypatch.setattr(settings, "anthropic_api_key", SecretStr(""))
    monkeypatch.setattr(settings, "openai_api_key", SecretStr(""))
    monkeypatch.setattr(settings, "ollama_url", "")
    available_scorers.cache_clear()
    yield
    available_scorers.cache_clear()


def test_only_mock_without_any_setting():
    assert list(available_scorers()) == ["mock"]


def test_ollama_is_off_unless_its_url_is_set():
    assert Settings.model_fields["ollama_url"].default == ""


def test_each_provider_appears_with_its_setting(monkeypatch):
    monkeypatch.setattr(settings, "anthropic_api_key", SecretStr("key"))
    monkeypatch.setattr(settings, "openai_api_key", SecretStr("key"))
    monkeypatch.setattr(settings, "ollama_url", "http://localhost:11434")

    scorers = available_scorers()

    assert list(scorers) == ["mock", "claude", "openai", "ollama"]
    assert scorers["claude"].model == settings.claude_model
    assert scorers["openai"].model == settings.openai_model
    assert scorers["ollama"].model == settings.ollama_model
    assert all(scorer.provider == provider_id for provider_id, scorer in scorers.items())
