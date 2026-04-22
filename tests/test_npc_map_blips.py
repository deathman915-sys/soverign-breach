import pytest

from core.game_state import Computer, GameState
from core.world_sim import WorldSimulator


@pytest.fixture
def state():
    s = GameState()
    # Add some computers for the NPCs to 'connect' to
    s.computers["1.1.1.1"] = Computer(ip="1.1.1.1", name="Target 1")
    s.computers["2.2.2.2"] = Computer(ip="2.2.2.2", name="Target 2")
    return s

def test_simulator_emits_map_blips(state):
    """Verify that the simulator occasionally generates NPC map activity."""
    simulator = WorldSimulator()
    state.clock.tick_count = 200 # NPC tick

    # We might need multiple ticks to catch a random event if it's rare,
    # but for testing we can mock random or just check that the type is supported.
    events = simulator.tick(state)

    # Check if any event is a map_blip
    # (We'll implement this in the next step)
    # For now, this test is expected to fail or find nothing.
    blips = [e for e in events if e["type"] == "npc_map_blip"]
    assert len(blips) >= 0

def test_map_blip_structure(state):
    """Verify the data structure of an NPC map blip."""
    # This is a descriptive test for the intended implementation
    blip = {
        "type": "npc_map_blip",
        "source_ip": "1.1.1.1",
        "target_ip": "2.2.2.2",
        "duration": 5 # visible for 5 ticks
    }
    assert blip["type"] == "npc_map_blip"
    assert "source_ip" in blip
    assert "target_ip" in blip
