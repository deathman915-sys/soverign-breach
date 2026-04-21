"""
Onlink-Clone: TDD tests for warning events and bank robbery

Warning events: When log suspicion reaches HIGH, the player gets a warning
that feds are investigating. Gives a window to delete logs before game over.

Bank robbery event: When player illegally transfers money, a 2-minute timer
starts. If logs aren't scrubbed, game over.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from core.game_state import (
    GameState,
    Computer,
    NodeType,
    AccessLog,
)
from core.world_generator import generate_world


class TestWarningEvents:
    def test_high_suspicion_triggers_warning(self, world):
        """When log suspicion reaches HIGH, a warning event should be emitted."""
        from core.log_suspicion import escalate_suspicion
        from core.warning_events import check_warnings

        log_entry = AccessLog(
            log_time="0",
            from_ip="127.0.0.1",
            from_name="Test",
            subject="authentication accepted",
        )
        world.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1", name="Target", computer_type=NodeType.INTERNAL_SRV
        )
        world.computers["10.0.0.1"].logs.append(log_entry)

        # Escalate to HIGH
        for _ in range(500):
            escalate_suspicion(world, 100)

        warnings = check_warnings(world)
        assert len(warnings) > 0
        assert warnings[0]["type"] == "warning"

    def test_warning_only_emitted_once(self, world):
        """Warning should only be emitted once per log."""
        from core.log_suspicion import escalate_suspicion
        from core.warning_events import check_warnings

        log_entry = AccessLog(
            log_time="0",
            from_ip="127.0.0.1",
            from_name="Test",
            subject="authentication accepted",
        )
        world.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1", name="Target", computer_type=NodeType.INTERNAL_SRV
        )
        world.computers["10.0.0.1"].logs.append(log_entry)

        for _ in range(500):
            escalate_suspicion(world, 100)

        w1 = check_warnings(world)
        w2 = check_warnings(world)
        # Second check should not emit another warning
        assert len(w2) <= len(w1)

    def test_deleted_log_no_warning(self, world):
        """Deleted logs should not trigger warnings."""
        from core.log_suspicion import escalate_suspicion
        from core.warning_events import check_warnings

        log_entry = AccessLog(
            log_time="0",
            from_ip="127.0.0.1",
            from_name="Test",
            subject="authentication accepted",
        )
        log_entry.is_deleted = True
        world.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1", name="Target", computer_type=NodeType.INTERNAL_SRV
        )
        world.computers["10.0.0.1"].logs.append(log_entry)

        for _ in range(500):
            escalate_suspicion(world, 100)

        warnings = check_warnings(world)
        assert len(warnings) == 0


class TestBankRobberyEvent:
    def test_illegal_transfer_starts_timer(self, world):
        """An illegal transfer should start a robbery timer."""
        from core.bank_robbery import record_illegal_transfer

        world._robbery_timers = []
        record_illegal_transfer(world, "10.0.0.1", "12345", 50000)
        assert len(world._robbery_timers) > 0

    def test_robbery_timer_expires(self, world):
        """If logs aren't deleted before timer expires, game over."""
        from core.bank_robbery import record_illegal_transfer, tick_robbery_timers

        world._robbery_timers = []
        record_illegal_transfer(world, "10.0.0.1", "12345", 50000)

        # Tick past the timer (default 120 seconds = 120 ticks at speed 1)
        events = tick_robbery_timers(world, 200)
        assert len(events) > 0
        assert events[0]["type"] == "bank_robbery_caught"

    def test_robbery_timer_cleared_by_deleting_logs(self, world):
        """Deleting the relevant logs should clear the robbery timer."""
        from core.bank_robbery import (
            record_illegal_transfer,
            tick_robbery_timers,
            clear_robbery_logs,
        )

        # Create the bank computer with a transfer log
        world.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1", name="Test Bank", computer_type=NodeType.INTERNAL_SRV
        )
        world.computers["10.0.0.1"].logs.append(
            AccessLog(
                log_time="0",
                from_ip="127.0.0.1",
                from_name="Test",
                subject="Money transfer of 50000c",
            )
        )

        world._robbery_timers = []
        record_illegal_transfer(world, "10.0.0.1", "12345", 50000)

        # Delete the transfer log
        for log in world.computers["10.0.0.1"].logs:
            log.is_deleted = True

        clear_robbery_logs(world)
        events = tick_robbery_timers(world, 200)
        # Should be cleared since logs are deleted
        assert len(events) == 0 or not any(
            e["type"] == "bank_robbery_caught" for e in events
        )


@pytest.fixture
def world():
    s = GameState()
    generate_world(s)
    s._robbery_timers = []
    return s
