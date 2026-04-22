"""
TDD tests for Full Arrest Flow (Phase 4).
Tests arrest consequences, disavowed flow, news generation, and jail time.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from core.event_scheduler import process_jail_time, trigger_arrest
from core.game_state import GameState, PersonStatus, VFSFile


@pytest.fixture
def arrested_state():
    """A GameState with a player that has been arrested."""
    state = GameState()
    state.player.balance = 10000
    state.player.uplink_rating = 5
    state.player.neuromancer_rating = 50
    state.player.credit_rating = 50
    state.vfs.files.append(VFSFile(filename="hacker_tool.exe", size_gq=4))
    state.gateway.heat = 50.0
    return state


class TestArrestConsequences:
    def test_balance_seized(self, arrested_state):
        """Arrest should seize 50% of balance."""
        trigger_arrest(arrested_state, reason="Test")
        assert arrested_state.player.balance == 5000

    def test_rating_reset(self, arrested_state):
        """Arrest should reset uplink rating to 1."""
        trigger_arrest(arrested_state, reason="Test")
        assert arrested_state.player.uplink_rating == 1

    def test_credit_rating_penalty(self, arrested_state):
        """Arrest should reduce credit rating."""
        initial = arrested_state.player.credit_rating
        trigger_arrest(arrested_state, reason="Test")
        assert arrested_state.player.credit_rating < initial
        assert arrested_state.player.credit_rating >= 1

    def test_vfs_wiped(self, arrested_state):
        """Arrest should wipe all VFS files."""
        assert len(arrested_state.vfs.files) > 0
        trigger_arrest(arrested_state, reason="Test")
        assert len(arrested_state.vfs.files) == 0

    def test_gateway_reset(self, arrested_state):
        """Arrest should reset gateway heat."""
        arrested_state.gateway.heat = 80.0
        trigger_arrest(arrested_state, reason="Test")
        assert arrested_state.gateway.heat == 25.0

    def test_simulation_paused(self, arrested_state):
        """Arrest should pause the simulation."""
        trigger_arrest(arrested_state, reason="Test")
        assert arrested_state.clock.speed_multiplier == 0

    def test_arrest_count_increments(self, arrested_state):
        """Arrest should increment arrest_count."""
        assert arrested_state.player.arrest_count == 0
        trigger_arrest(arrested_state, reason="Test")
        assert arrested_state.player.arrest_count == 1

    def test_news_generated(self, arrested_state):
        """Arrest should generate a news article."""
        initial_news_count = len(arrested_state.world.news)
        trigger_arrest(arrested_state, reason="Test")
        assert len(arrested_state.world.news) > initial_news_count
        # Check the news article has arrest-related content
        latest_news = arrested_state.world.news[-1]
        full_text = f"{latest_news.headline} {latest_news.body}".lower()
        assert "arrest" in full_text or "apprehend" in full_text, f"News article should mention arrest: {latest_news.headline}"


class TestJailTime:
    def test_jail_ticks_decrement(self, arrested_state):
        """Jail sentence ticks should decrement over time."""
        trigger_arrest(arrested_state, reason="Test")
        initial_ticks = arrested_state.player.jail_sentence_ticks
        assert initial_ticks > 0

        process_jail_time(arrested_state, ticks=100)
        assert arrested_state.player.jail_sentence_ticks == initial_ticks - 100
        assert arrested_state.player.is_arrested is True

    def test_jail_release(self, arrested_state):
        """Player should be released when jail ticks reach 0."""
        trigger_arrest(arrested_state, reason="Test")
        arrested_state.player.jail_sentence_ticks = 50

        result = process_jail_time(arrested_state, ticks=60)
        assert result is not None
        assert result["type"] == "released"
        assert arrested_state.player.is_arrested is False
        assert arrested_state.player.status == PersonStatus.NONE


class TestDisavowedFlow:
    def test_disavowed_after_max_arrests(self, arrested_state):
        """Player should be disavowed after ARREST_MAX_COUNT_BEFORE_DISAVOWED arrests."""
        from core import constants as C

        # Simulate multiple arrests
        for i in range(C.ARREST_MAX_COUNT_BEFORE_DISAVOWED):
            arrested_state.player.arrest_count = i
            arrested_state.player.is_arrested = False
            arrested_state.player.status = PersonStatus.NONE
            arrested_state.player.balance = 10000
            arrested_state.vfs.files = []
            trigger_arrest(arrested_state, reason=f"Arrest {i+1}")

        # After max arrests, player should be disavowed
        assert arrested_state.player.status == PersonStatus.DISAVOWED
        assert arrested_state.player.disavow_countdown_ticks > 0

    def test_disavow_countdown_decrements(self, arrested_state):
        """Disavow countdown should decrement after jail time finishes."""
        from core import constants as C

        arrested_state.player.arrest_count = C.ARREST_MAX_COUNT_BEFORE_DISAVOWED
        arrested_state.player.is_arrested = True
        arrested_state.player.status = PersonStatus.DISAVOWED
        arrested_state.player.jail_sentence_ticks = 10
        arrested_state.player.disavow_countdown_ticks = 60

        # Jail time finishes first
        result = process_jail_time(arrested_state, ticks=10)
        assert result is not None
        assert result["type"] == "disavow_countdown"
        assert arrested_state.player.disavow_countdown_ticks < 60

    def test_profile_deleted_on_countdown_expiry(self, arrested_state, tmp_path):
        """Profile should be deleted when disavow countdown expires."""
        from core import constants as C
        from core import persistence

        # Create a test profile file
        profile_dir = tmp_path / "profiles"
        profile_dir.mkdir()
        profile_file = profile_dir / "TESTER.json"
        profile_file.write_text('{"player": {"handle": "TESTER"}}')

        # Override PROFILES_DIR temporarily
        original_dir = persistence.PROFILES_DIR
        persistence.PROFILES_DIR = str(profile_dir)

        arrested_state.player.arrest_count = C.ARREST_MAX_COUNT_BEFORE_DISAVOWED
        arrested_state.player.is_arrested = True
        arrested_state.player.status = PersonStatus.DISAVOWED
        arrested_state.player.jail_sentence_ticks = 0
        arrested_state.player.disavow_countdown_ticks = 1
        arrested_state.player.handle = "TESTER"

        result = process_jail_time(arrested_state, ticks=1)
        assert result is not None
        assert result["type"] == "profile_deleted"
        assert not profile_file.exists()

        persistence.PROFILES_DIR = original_dir


class TestArrestUI:
    def test_arrest_result_dict(self, arrested_state):
        """trigger_arrest should return a structured result dict."""
        result = trigger_arrest(arrested_state, reason="Test Arrest")
        assert isinstance(result, dict)
        assert "type" in result
        assert result["type"] == "arrest"
        assert "reason" in result
        assert result["reason"] == "Test Arrest"
        assert "jail_ticks" in result
        assert "balance_remaining" in result
        assert "arrest_count" in result

    def test_disavowed_result_dict(self, arrested_state):
        """trigger_arrest should return disavowed type when max arrests reached."""
        from core import constants as C

        arrested_state.player.arrest_count = C.ARREST_MAX_COUNT_BEFORE_DISAVOWED - 1
        result = trigger_arrest(arrested_state, reason="Final Arrest")
        assert result["type"] == "disavowed"
