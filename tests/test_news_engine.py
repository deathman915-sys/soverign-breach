import pytest
import logging
from unittest import mock

from core.game_state import GameState, NewsItem
from core.news_engine import add_news, _TEMPLATES

@pytest.fixture
def state():
    return GameState()

def test_add_news_known_event(state):
    """Test add_news with a known event type and provided kwargs."""
    # Using 'arrest' template, requires 'agent_name'
    agent_name = "TestHacker99"
    news = add_news(state, "arrest", agent_name=agent_name)

    assert news is not None
    assert isinstance(news, NewsItem)
    assert news.category == "crime" # The category for arrest
    assert agent_name in news.headline or agent_name in news.body
    assert len(state.world.news) == 1
    assert state.world.news[0] == news

def test_add_news_missing_kwargs(state):
    """Test add_news when kwargs are missing, expecting it to use defaults."""
    # Using 'company_hack', requires 'company_name' which defaults to "TechCorp"
    news = add_news(state, "company_hack")

    assert news is not None
    assert news.category == "corporate"
    # TechCorp is the default company_name in _build_defaults
    assert "TechCorp" in news.headline or "TechCorp" in news.body

def test_add_news_unknown_event(state, caplog):
    """Test add_news with an unknown event type, expecting ambient fallback."""
    with caplog.at_level(logging.WARNING):
        news = add_news(state, "unknown_random_event")

    assert news is not None
    assert news.category == "general" # Ambient news category
    assert "Unknown news event_type: unknown_random_event" in caplog.text
    assert len(state.world.news) == 1

def test_add_news_safe_format_dict(state):
    """Test add_news when a template variable is completely missing from kwargs and defaults."""
    # We will temporarily inject a broken template to test _SafeFormatDict
    test_event_type = "test_broken_template"
    broken_template = {
        "headlines": ["Headline with missing {missing_variable}"],
        "bodies": ["Body with missing {missing_variable}"],
        "category": "test",
    }

    with mock.patch.dict(_TEMPLATES, {test_event_type: broken_template}):
        news = add_news(state, test_event_type)

    assert news is not None
    assert news.headline == "Headline with missing {missing_variable}"
    assert news.body == "Body with missing {missing_variable}"
