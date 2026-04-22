import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from core.connection_manager import connect
from core.game_state import Computer, GameState, NodeType


@pytest.fixture
def state():
    s = GameState()
    s.computers["127.0.0.1"] = Computer(ip="127.0.0.1", name="Localhost", computer_type=NodeType.GATEWAY)
    s.player.localhost_ip = "127.0.0.1"

    # Pre-populate some computers
    s.computers["1.1.1.1"] = Computer(ip="1.1.1.1", name="Proxy1", computer_type=NodeType.PUBLIC_SERVER)
    s.computers["2.2.2.2"] = Computer(ip="2.2.2.2", name="Proxy2", computer_type=NodeType.PUBLIC_SERVER)
    s.computers["3.3.3.3"] = Computer(ip="3.3.3.3", name="Target", computer_type=NodeType.INTERNAL_SRV)

    return s

class TestManualRouting:
    def test_connect_uses_explicit_bounce_ips(self, state):
        # Case: Player manually picked 2.2.2.2 only
        result = connect(state, "3.3.3.3", bounce_ips=["2.2.2.2"])
        assert result["success"] is True

        # Connection nodes should be [Proxy2, Target]
        ips = [node.ip for node in state.connection.nodes]
        assert ips == ["2.2.2.2", "3.3.3.3"]
        assert result["bounce_count"] == 1

    def test_connect_uses_state_hops_if_none_provided(self, state):
        # Case: Player didn't provide IPs, should use state.bounce.hops
        state.bounce.hops = ["1.1.1.1"]
        result = connect(state, "3.3.3.3", bounce_ips=None)
        assert result["success"] is True

        ips = [node.ip for node in state.connection.nodes]
        assert "1.1.1.1" in ips
        assert "3.3.3.3" in ips

    def test_connect_ignores_internic_if_not_in_manual_list(self, state):
        # Even if InterNIC is in known_ips, if it's not in the manual list, it shouldn't be there.
        # This confirms "Manual Route Building" is truly manual.
        s = state
        s.computers["154.22.12.1"] = Computer(ip="154.22.12.1", name="InterNIC")

        connect(state, "3.3.3.3", bounce_ips=["1.1.1.1"])
        ips = [node.ip for node in state.connection.nodes]
        assert "154.22.12.1" not in ips
        assert ips == ["1.1.1.1", "3.3.3.3"]
