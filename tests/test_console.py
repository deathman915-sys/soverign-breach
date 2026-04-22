"""
Onlink-Clone: Remote Controller Console Tests

Tests console command execution on remote computers.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from core import constants as C
from core.game_state import Computer, ComputerScreen, DataFile, GameState, NodeType
from core.remote_controller import RemoteController


@pytest.fixture
def state():
    s = GameState()
    s.computers["10.0.0.1"] = Computer(
        ip="10.0.0.1",
        name="Target",
        computer_type=NodeType.INTERNAL_SRV,
        screens=[
            ComputerScreen(screen_type=C.SCREEN_MENUSCREEN),
            ComputerScreen(screen_type=C.SCREEN_CONSOLESCREEN),
        ],
        files=[
            DataFile(filename="secret.dat", size=5, file_type=1),
            DataFile(filename="readme.txt", size=2, file_type=1),
        ],
    )
    return s


class TestConsoleCommand:
    def test_ls_command(self, state):
        rc = RemoteController(state)
        result = rc.execute_console_command("10.0.0.1", "ls")
        assert result["success"] is True
        assert len(result["output"]) > 0

    def test_cd_command(self, state):
        rc = RemoteController(state)
        result = rc.execute_console_command("10.0.0.1", "cd /data")
        assert result["success"] is True
        assert result["cwd"] == "/data"

    def test_cd_up(self, state):
        rc = RemoteController(state)
        rc.execute_console_command("10.0.0.1", "cd /data")
        result = rc.execute_console_command("10.0.0.1", "cd ..")
        assert result["success"] is True
        assert result["cwd"] == "/"

    def test_delete_file(self, state):
        rc = RemoteController(state)
        file_count_before = len(state.computers["10.0.0.1"].files)
        result = rc.execute_console_command("10.0.0.1", "delete secret.dat")
        assert result["success"] is True
        assert len(state.computers["10.0.0.1"].files) == file_count_before - 1

    def test_delete_nonexistent(self, state):
        rc = RemoteController(state)
        result = rc.execute_console_command("10.0.0.1", "delete ghost.dat")
        assert result["success"] is False

    def test_shutdown(self, state):
        rc = RemoteController(state)
        result = rc.execute_console_command("10.0.0.1", "shutdown")
        assert result["success"] is True
        assert state.computers["10.0.0.1"].is_running is False

    def test_unknown_command(self, state):
        rc = RemoteController(state)
        result = rc.execute_console_command("10.0.0.1", "foobar")
        assert result["success"] is False

    def test_computer_not_found(self, state):
        rc = RemoteController(state)
        result = rc.execute_console_command("99.99.99.99", "ls")
        assert result["success"] is False

    def test_computer_without_console(self, state):
        state.computers["10.0.0.2"] = Computer(
            ip="10.0.0.2",
            name="No Console",
            computer_type=NodeType.INTERNAL_SRV,
            screens=[ComputerScreen(screen_type=C.SCREEN_MENUSCREEN)],
        )
        rc = RemoteController(state)
        result = rc.execute_console_command("10.0.0.2", "ls")
        assert result["success"] is False


class TestRemoteStateConsole:
    def test_has_console_flag(self, state):
        rc = RemoteController(state)
        res = rc.get_remote_state("10.0.0.1")
        assert res["server"]["has_console"] is True

    def test_no_console_flag(self, state):
        state.computers["10.0.0.2"] = Computer(
            ip="10.0.0.2",
            name="No Console",
            computer_type=NodeType.INTERNAL_SRV,
            screens=[ComputerScreen(screen_type=C.SCREEN_MENUSCREEN)],
        )
        rc = RemoteController(state)
        res = rc.get_remote_state("10.0.0.2")
        assert res["server"]["has_console"] is False
