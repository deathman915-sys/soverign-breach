"""
TDD tests for LogModifier (framing) functionality.
Phase 3 of porting Uplink log modification systems.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from core.game_state import GameState, Computer, NodeType, AccessLog
from core.remote_controller import RemoteController


@pytest.fixture
def server_with_logs():
    """A Computer with log entries."""
    comp = Computer(
        ip="10.0.0.50",
        name="Test Server",
        computer_type=NodeType.INTERNAL_SRV,
        hack_difficulty=50,
    )
    comp.add_log(AccessLog(
        log_time="14:30:00",
        from_ip="192.168.1.100",
        subject="ConnectionOpened",
    ))
    comp.add_log(AccessLog(
        log_time="14:31:00",
        from_ip="192.168.1.100",
        subject="PasswordSuccess",
    ))
    comp.add_log(AccessLog(
        log_time="14:32:00",
        from_ip="10.0.0.99",
        subject="FileAccess",
    ))
    return comp


@pytest.fixture
def rc(server_with_logs):
    s = GameState()
    s.computers["10.0.0.50"] = server_with_logs
    return RemoteController(s)


class TestLogModification:
    def test_modify_log_changes_from_ip(self, rc):
        """modify_log() should change the from_ip field."""
        comp = rc.state.computers["10.0.0.50"]
        assert comp.logs[0].from_ip == "192.168.1.100"

        result = rc.modify_log("10.0.0.50", 0, "10.0.0.200")
        assert result["success"] is True
        assert comp.logs[0].from_ip == "10.0.0.200"

    def test_modify_log_preserves_internal_backup(self, rc):
        """modify_log() should NOT change the internal backup log."""
        comp = rc.state.computers["10.0.0.50"]
        original_ip = comp.internal_logs[0].from_ip

        rc.modify_log("10.0.0.50", 0, "10.0.0.200")

        # Internal backup should still have the original IP
        assert comp.internal_logs[0].from_ip == original_ip

    def test_log_modified_detects_tampering(self, rc):
        """log_modified() should return True after modification."""
        comp = rc.state.computers["10.0.0.50"]
        assert comp.log_modified(0) is False

        rc.modify_log("10.0.0.50", 0, "10.0.0.200")

        assert comp.log_modified(0) is True
        assert comp.log_modified(1) is False  # Unmodified log

    def test_log_modified_invalid_index(self, rc):
        """log_modified() should return False for invalid index."""
        comp = rc.state.computers["10.0.0.50"]
        assert comp.log_modified(-1) is False
        assert comp.log_modified(999) is False

    def test_recover_log_restores_original(self, rc):
        """recover_log() should restore the original from_ip from internal backup."""
        comp = rc.state.computers["10.0.0.50"]
        original_ip = comp.internal_logs[0].from_ip

        rc.modify_log("10.0.0.50", 0, "10.0.0.200")
        assert comp.logs[0].from_ip == "10.0.0.200"

        comp.recover_log(0)
        assert comp.logs[0].from_ip == original_ip
        assert comp.log_modified(0) is False

    def test_recover_log_noop_when_not_modified(self, rc):
        """recover_log() should return False for unmodified logs."""
        comp = rc.state.computers["10.0.0.50"]
        result = comp.recover_log(0)
        assert result is False

    def test_modify_log_nonexistent_computer(self, rc):
        """modify_log() should fail for non-existent computer."""
        result = rc.modify_log("99.99.99.99", 0, "10.0.0.200")
        assert result["success"] is False
        assert "Computer not found" in result["error"]

    def test_modify_log_invalid_index(self, rc):
        """modify_log() should fail for invalid log index."""
        result = rc.modify_log("10.0.0.50", 999, "10.0.0.200")
        assert result["success"] is False
        assert "out of range" in result["error"]

    def test_modify_log_increases_suspicion(self, rc):
        """modify_log() should increase the suspicion level."""
        comp = rc.state.computers["10.0.0.50"]
        initial_suspicion = comp.logs[0].suspicion_level

        rc.modify_log("10.0.0.50", 0, "10.0.0.200")

        assert comp.logs[0].suspicion_level >= max(initial_suspicion, 1)


class TestLogScreenHTML:
    def test_log_screen_has_modify_button(self, rc):
        """Log screen HTML should have MODIFY buttons."""
        comp = rc.state.computers["10.0.0.50"]
        data = rc._render_log_screen(comp)
        assert 'onclick="modifyLogPrompt(0)"' in data["html"]
        assert 'onclick="modifyLogPrompt(1)"' in data["html"]

    def test_log_screen_has_log_data_script(self, rc):
        """Log screen HTML should include window._logData for JS access."""
        comp = rc.state.computers["10.0.0.50"]
        data = rc._render_log_screen(comp)
        assert 'window._logData' in data["html"]
        assert '"192.168.1.100"' in data["html"]

    def test_modified_log_shows_indicator(self, rc):
        """Modified logs should show [MODIFIED] indicator."""
        comp = rc.state.computers["10.0.0.50"]
        rc.modify_log("10.0.0.50", 0, "10.0.0.200")

        data = rc._render_log_screen(comp)
        assert "[MODIFIED]" in data["html"]

    def test_log_screen_empty(self, rc):
        """Log screen with no logs should show 'Empty'."""
        comp = rc.state.computers["10.0.0.50"]
        comp.logs.clear()
        comp.internal_logs.clear()

        data = rc._render_log_screen(comp)
        assert "Log buffer empty" in data["html"]
