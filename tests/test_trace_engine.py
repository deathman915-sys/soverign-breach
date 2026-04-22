import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest import mock

from core.game_state import GameState
from core.trace_engine import reset_trace


def test_reset_trace():
    state = GameState()
    state.connection = mock.Mock()
    state.connection.trace_active = True
    state.connection.trace_progress = 0.75
    state.connection.nodes = []

    reset_trace(state)

    assert state.connection.trace_active is False
    assert state.connection.trace_progress == 0.0
