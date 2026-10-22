import pytest
from core.config import ConfigError, load_settings


def test_defaults_and_key():
    s = load_settings(env={"GROQ_API_KEY": "gsk_secret123"})
    assert s.model == "openai/gpt-oss-120b"
    assert s.base_url == "https://api.groq.com/openai/v1"
    assert s.price_in_per_m is None


def test_missing_key_raises():
    with pytest.raises(ConfigError):
        load_settings(env={})
    with pytest.raises(ConfigError):
        load_settings(env={"GROQ_API_KEY": "your_groq_api_key_here"})


def test_key_never_in_repr():
    s = load_settings(env={"GROQ_API_KEY": "gsk_secret123"})
    assert "gsk_secret123" not in repr(s) and "gsk_secret123" not in str(s)


def test_bad_number_raises():
    with pytest.raises(ConfigError):
        load_settings(env={"GROQ_API_KEY": "k", "LLM_PRICE_IN_PER_M": "abc"})
    with pytest.raises(ConfigError):
        load_settings(env={"GROQ_API_KEY": "k", "LLM_TEMPERATURE": "hot"})
