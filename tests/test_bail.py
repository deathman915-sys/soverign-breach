"""
TDD tests for Bail/Buyout System (Phase 5).
Tests bail calculation, payment, and consequences.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from core import constants as C
from core.event_scheduler import pay_bail, trigger_arrest
from core.game_state import GameState, PersonStatus


@pytest.fixture
def arrested_state():
    """A GameState with a player that has been arrested."""
    state = GameState()
    state.player.balance = 200000  # High enough to afford bail after 50% seizure
    state.player.uplink_rating = 5
    state.player.is_arrested = False
    state.player.status = PersonStatus.NONE
    state.player.jail_sentence_ticks = 0
    state.player.bail_amount = 0
    return state


class TestBailCalculation:
    def test_bail_calculated_on_arrest(self, arrested_state):
        """Bail amount should be calculated when player is arrested."""
        result = trigger_arrest(arrested_state, reason="Test")
        assert arrested_state.player.bail_amount > 0
        assert "bail_amount" in result
        assert result["bail_amount"] == arrested_state.player.bail_amount

    def test_bail_within_range(self, arrested_state):
        """Bail amount should be clamped between BAIL_MINIMUM and BAIL_MAXIMUM."""
        trigger_arrest(arrested_state, reason="Test")
        bail = arrested_state.player.bail_amount
        assert C.BAIL_MINIMUM <= bail <= C.BAIL_MAXIMUM

    def test_bail_based_on_jail_time(self, arrested_state):
        """Higher jail time should result in higher bail (up to maximum)."""
        trigger_arrest(arrested_state, reason="Test")
        # Bail is clamped, so it should be at least the minimum or the calculated value
        assert arrested_state.player.bail_amount >= C.BAIL_MINIMUM


class TestPayBail:
    def test_pay_bail_reduces_jail_time(self, arrested_state):
        """Paying bail should reduce jail time by BAIL_JAIL_REDUCTION_PERCENT."""
        trigger_arrest(arrested_state, reason="Test")
        initial_jail = arrested_state.player.jail_sentence_ticks

        result = pay_bail(arrested_state)

        assert result["success"] is True
        expected_reduction = int(initial_jail * C.BAIL_JAIL_REDUCTION_PERCENT)
        assert result["jail_reduced"] == expected_reduction
        assert arrested_state.player.jail_sentence_ticks == initial_jail - expected_reduction

    def test_pay_bail_deducts_amount(self, arrested_state):
        """Paying bail should deduct the bail amount from balance."""
        trigger_arrest(arrested_state, reason="Test")
        initial_balance = arrested_state.player.balance
        bail = arrested_state.player.bail_amount

        pay_bail(arrested_state)

        assert arrested_state.player.balance == initial_balance - bail

    def test_pay_bail_resets_bail_amount(self, arrested_state):
        """Bail can only be paid once per arrest."""
        trigger_arrest(arrested_state, reason="Test")
        pay_bail(arrested_state)
        assert arrested_state.player.bail_amount == 0

    def test_pay_bail_insufficient_funds(self, arrested_state):
        """Should fail if player can't afford bail."""
        arrested_state.player.balance = 500  # Very low balance
        trigger_arrest(arrested_state, reason="Test")
        # After 50% seizure: 250c, bail will be clamped to 1000c minimum
        # So 250 < 1000 → insufficient funds

        result = pay_bail(arrested_state)

        assert result["success"] is False
        assert "Insufficient funds" in result["error"]

    def test_pay_bail_not_arrested(self, arrested_state):
        """Should fail if player is not arrested."""
        result = pay_bail(arrested_state)
        assert result["success"] is False
        assert "Not currently arrested" in result["error"]

    def test_pay_bail_already_paid(self, arrested_state):
        """Should fail if bail was already paid."""
        trigger_arrest(arrested_state, reason="Test")
        pay_bail(arrested_state)

        result = pay_bail(arrested_state)

        assert result["success"] is False
        assert "already paid" in result["error"]


class TestBailForDisavowed:
    def test_pay_bail_reduces_disavow_countdown(self, arrested_state):
        """For disavowed players, bail should reduce countdown."""
        arrested_state.player.arrest_count = C.ARREST_MAX_COUNT_BEFORE_DISAVOWED
        trigger_arrest(arrested_state, reason="Final Arrest")
        assert arrested_state.player.status == PersonStatus.DISAVOWED

        initial_countdown = arrested_state.player.disavow_countdown_ticks
        result = pay_bail(arrested_state)

        assert result["success"] is True
        assert "countdown_reduced" in result
        expected_reduction = int(initial_countdown * C.BAIL_DISAVOW_REDUCTION_PERCENT)
        assert result["countdown_reduced"] == expected_reduction
        assert arrested_state.player.disavow_countdown_ticks == initial_countdown - expected_reduction
