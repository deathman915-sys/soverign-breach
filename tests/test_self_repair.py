import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from core.game_state import Computer, GameState, NodeType
from core.security_engine import recover_compromised_systems


@pytest.fixture
def state():
    s = GameState()
    # Create a server
    s.computers["10.0.0.1"] = Computer(
        ip="10.0.0.1",
        name="Target Server",
        computer_type=NodeType.INTERNAL_SRV
    )
    s.computers["10.0.0.1"].accounts["admin"] = "original_pw"
    return s

class TestSelfRepair:
    def test_admin_password_rotates_after_hack(self, state):
        comp = state.computers["10.0.0.1"]

        # 1. Simulate a hack by adding it to a "compromised" list in state
        # We'll use state.world.metadata or a new field if we want to be clean.
        # For now, let's assume the engine tracks compromised IPs in a dict.
        if not hasattr(state, "compromised_ips"):
            state.compromised_ips = {} # ip -> tick_hacked

        state.compromised_ips["10.0.0.1"] = 100
        state.clock.tick_count = 100

        # 2. Run recovery at tick 100 (too early)
        recover_compromised_systems(state)
        assert comp.accounts["admin"] == "original_pw"

        # 3. Advance time by 10,000 ticks (approx 2.7 hours at 1Hz)
        state.clock.tick_count = 10101
        recover_compromised_systems(state)

        # 4. Password should have changed
        assert comp.accounts["admin"] != "original_pw"
        assert "10.0.0.1" not in state.compromised_ips

    def test_security_systems_reenable(self, state):
        from core.game_state import SecuritySystem
        comp = state.computers["10.0.0.1"]
        comp.security_systems = [SecuritySystem(security_type=3, level=1, is_active=False)]

        if not hasattr(state, "compromised_ips"):
            state.compromised_ips = {}
        state.compromised_ips["10.0.0.1"] = 100
        state.clock.tick_count = 10500 # Faster recovery for security systems

        recover_compromised_systems(state)
        assert comp.security_systems[0].is_active is True
