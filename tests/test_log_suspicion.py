"""
Onlink-Clone: TDD tests for log suspicion escalation

In Uplink, logs escalate through suspicion levels:
NOTSUSPICIOUS -> SUSPICIOUS -> SUSPICIOUSANDNOTICED -> UNDERINVESTIGATION
This gives the player a window to delete logs before being traced.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from core.game_state import AccessLog, Computer, GameState, NodeType
from core.world_generator import generate_world

# Suspicion levels
SUSPICION_NONE = 0
SUSPICION_LOW = 1
SUSPICION_MEDIUM = 2
SUSPICION_HIGH = 3


class TestLogSuspicion:
    def test_access_log_has_suspicion_level(self, world):
        """AccessLog should have a suspicion_level field."""
        log = AccessLog(
            log_time="0",
            from_ip="127.0.0.1",
            from_name="Test",
            subject="Connection established",
        )
        assert hasattr(log, "suspicion_level")

    def test_new_log_starts_not_suspicious(self, world):
        """New logs should start at suspicion level 0."""
        log = AccessLog(
            log_time="0",
            from_ip="127.0.0.1",
            from_name="Test",
            subject="Connection established",
        )
        assert log.suspicion_level == SUSPICION_NONE

    def test_suspicion_escalates_over_time(self, world):
        """Logs should escalate suspicion each tick."""
        from core.log_suspicion import escalate_suspicion

        log = AccessLog(
            log_time="0",
            from_ip="127.0.0.1",
            from_name="Test",
            subject="authentication accepted",
        )
        world.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1", name="Target", computer_type=NodeType.INTERNAL_SRV
        )
        world.computers["10.0.0.1"].logs.append(log)

        # Escalate many ticks
        for _ in range(100):
            escalate_suspicion(world, 100)

        # Should have escalated
        assert log.suspicion_level > SUSPICION_NONE

    def test_escalation_triggers_investigation(self, world):
        """High suspicion logs should trigger investigation events."""
        from core.log_suspicion import escalate_suspicion

        log = AccessLog(
            log_time="0",
            from_ip="127.0.0.1",
            from_name="Test",
            subject="authentication accepted",
        )
        world.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1", name="Target", computer_type=NodeType.INTERNAL_SRV
        )
        world.computers["10.0.0.1"].logs.append(log)

        # Escalate to maximum
        for _ in range(500):
            escalate_suspicion(world, 100)

        assert log.suspicion_level >= SUSPICION_HIGH

    def test_deleted_logs_stop_escalating(self, world):
        """Deleted logs should not escalate."""
        from core.log_suspicion import escalate_suspicion

        log = AccessLog(
            log_time="0",
            from_ip="127.0.0.1",
            from_name="Test",
            subject="authentication accepted",
        )
        log.is_deleted = True
        world.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1", name="Target", computer_type=NodeType.INTERNAL_SRV
        )
        world.computers["10.0.0.1"].logs.append(log)

        old_level = log.suspicion_level
        for _ in range(100):
            escalate_suspicion(world, 100)

        assert log.suspicion_level == old_level

    def test_authentication_logs_escalate_faster(self, world):
        """Auth logs should escalate faster than regular connection logs."""
        from core.log_suspicion import escalate_suspicion

        auth_log = AccessLog(
            log_time="0",
            from_ip="127.0.0.1",
            from_name="Test",
            subject="authentication accepted",
        )
        conn_log = AccessLog(
            log_time="0",
            from_ip="127.0.0.1",
            from_name="Test",
            subject="Connection from 127.0.0.1",
        )
        world.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1", name="Target", computer_type=NodeType.INTERNAL_SRV
        )
        world.computers["10.0.0.1"].logs.append(auth_log)
        world.computers["10.0.0.1"].logs.append(conn_log)

        for _ in range(50):
            escalate_suspicion(world, 100)

        # Auth log should be more suspicious
        assert auth_log.suspicion_level >= conn_log.suspicion_level


@pytest.fixture
def world():
    s = GameState()
    generate_world(s)
    return s
