"""
Onlink-Clone: Connection Manager Tests

Tests connection, disconnection, password authentication,
public access servers, bounce chains, and log creation.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from core.connection_manager import attempt_password, connect, disconnect
from core.game_state import Computer, ComputerScreen, GameState, NodeType


@pytest.fixture
def state():
    s = GameState()
    s.computers["127.0.0.1"] = Computer(
        ip="127.0.0.1", name="Localhost", computer_type=NodeType.GATEWAY
    )
    s.player.localhost_ip = "127.0.0.1"
    s.player.known_ips.append("127.0.0.1")
    return s


class TestConnect:
    def test_connect_to_known_ip(self, state):
        state.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1", name="Target", computer_type=NodeType.INTERNAL_SRV
        )
        result = connect(state, "10.0.0.1")
        assert result["success"] is True
        assert result["target_ip"] == "10.0.0.1"
        assert state.connection.is_active is True

    def test_connect_to_unknown_ip(self, state):
        result = connect(state, "99.99.99.99")
        assert result["success"] is False
        assert "Unknown IP" in result["error"]

    def test_connect_with_bounce(self, state):
        state.computers["1.1.1.1"] = Computer(
            ip="1.1.1.1", name="Proxy", computer_type=NodeType.PUBLIC_SERVER
        )
        state.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1", name="Target", computer_type=NodeType.INTERNAL_SRV
        )
        result = connect(state, "10.0.0.1", bounce_ips=["1.1.1.1"])
        assert result["success"] is True
        assert result["bounce_count"] == 1
        assert len(state.connection.nodes) == 2

    def test_connect_creates_log_on_target(self, state):
        state.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1", name="Target", computer_type=NodeType.INTERNAL_SRV
        )
        log_count_before = len(state.computers["10.0.0.1"].logs)
        connect(state, "10.0.0.1")
        assert len(state.computers["10.0.0.1"].logs) == log_count_before + 1

    def test_connect_creates_log_on_proxy(self, state):
        state.computers["1.1.1.1"] = Computer(
            ip="1.1.1.1", name="Proxy", computer_type=NodeType.PUBLIC_SERVER
        )
        state.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1", name="Target", computer_type=NodeType.INTERNAL_SRV
        )
        log_count_before = len(state.computers["1.1.1.1"].logs)
        connect(state, "10.0.0.1", bounce_ips=["1.1.1.1"])
        assert len(state.computers["1.1.1.1"].logs) == log_count_before + 1


class TestDisconnect:
    def test_disconnect_active(self, state):
        state.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1", name="Target", computer_type=NodeType.INTERNAL_SRV
        )
        connect(state, "10.0.0.1")
        result = disconnect(state)
        assert result["success"] is True
        assert state.connection.is_active is False

    def test_disconnect_not_connected(self, state):
        result = disconnect(state)
        assert result["success"] is False
        assert "Not connected" in result["error"]

    def test_disconnect_resets_trace(self, state):
        state.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1", name="Target", computer_type=NodeType.INTERNAL_SRV
        )
        connect(state, "10.0.0.1")
        state.connection.trace_active = True
        state.connection.trace_progress = 0.5
        disconnect(state)
        assert state.connection.trace_active is False
        assert state.connection.trace_progress == 0.0


class TestAttemptPassword:
    def test_correct_password(self, state):
        state.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1", name="Target", computer_type=NodeType.INTERNAL_SRV
        )
        state.computers["10.0.0.1"].accounts["admin"] = "secret"
        state.connection.target_ip = "10.0.0.1"
        state.connection.is_active = True
        result = attempt_password(state, "admin", "secret")
        assert result["success"] is True

    def test_wrong_password(self, state):
        state.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1", name="Target", computer_type=NodeType.INTERNAL_SRV
        )
        state.computers["10.0.0.1"].accounts["admin"] = "secret"
        state.connection.target_ip = "10.0.0.1"
        state.connection.is_active = True
        result = attempt_password(state, "admin", "wrong")
        assert result["success"] is False

    def test_wrong_username(self, state):
        state.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1", name="Target", computer_type=NodeType.INTERNAL_SRV
        )
        state.computers["10.0.0.1"].accounts["admin"] = "secret"
        state.connection.target_ip = "10.0.0.1"
        state.connection.is_active = True
        result = attempt_password(state, "root", "secret")
        assert result["success"] is False

    def test_not_connected(self, state):
        result = attempt_password(state, "admin", "secret")
        assert result["success"] is False

    def test_password_creates_auth_log(self, state):
        state.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1", name="Target", computer_type=NodeType.INTERNAL_SRV
        )
        state.computers["10.0.0.1"].accounts["admin"] = "secret"
        state.connection.target_ip = "10.0.0.1"
        state.connection.is_active = True
        attempt_password(state, "admin", "secret")
        logs = state.computers["10.0.0.1"].logs
        auth_logs = [log_entry for log_entry in logs if "authentication accepted" in log_entry.subject]
        assert len(auth_logs) == 1

    def test_fallback_to_screen_data1(self, state):
        state.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1",
            name="Target",
            computer_type=NodeType.INTERNAL_SRV,
            screens=[ComputerScreen(screen_type=1, data1="rose")],
        )
        state.connection.target_ip = "10.0.0.1"
        state.connection.is_active = True
        result = attempt_password(state, "admin", "rose")
        assert result["success"] is True


class TestPublicAccessServers:
    def test_public_server_has_no_accounts(self, state):
        """Public servers should not have password accounts."""
        state.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1",
            name="Public Server",
            computer_type=NodeType.PUBLIC_SERVER,
        )
        assert len(state.computers["10.0.0.1"].accounts) == 0

    def test_internal_server_has_accounts(self, state):
        """Internal servers should have password accounts."""
        state.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1",
            name="Internal Server",
            computer_type=NodeType.INTERNAL_SRV,
        )
        state.computers["10.0.0.1"].accounts["admin"] = "secret"
        assert len(state.computers["10.0.0.1"].accounts) > 0
