import pytest

from core.game_state import GameState, Mission
from core.world_sim import WorldSimulator


@pytest.fixture
def state():
    s = GameState()
    # Add a sample unaccepted mission
    m = Mission(
        id=1,
        description="Steal research data",
        is_accepted=False,
        expiration_tick=100
    )
    s.missions.append(m)
    return s

def test_missions_have_expiration(state):
    """Verify that missions can store an expiration tick."""
    m = state.missions[0]
    assert hasattr(m, "expiration_tick")
    assert m.expiration_tick == 100

def test_rival_claims_mission_on_expiry(state):
    """Verify that a rival NPC claims an unaccepted mission when it expires."""
    simulator = WorldSimulator()
    state.clock.tick_count = 101 # Past expiration

    # We need to ensure the NPC tick logic runs
    # In world_sim.py, NPC_TICK_INTERVAL = 200
    # Let's force it by setting tick to a multiple of 200
    state.clock.tick_count = 200
    state.missions[0].expiration_tick = 150 # Expired

    events = simulator.tick(state)

    # Mission should be removed from the available pool or marked as claimed
    m = next((mi for mi in state.missions if mi.id == 1), None)

    # Standard logic: expired and unclaimed missions are removed or attributed to rivals
    # For high-fidelity, we want it attributed to a rival
    assert m is None or m.claimed_by is not None

    # A news event should be generated
    assert any(e["type"] == "npc_claimed_mission" or "completed by rival" in str(e).lower() for e in events)

def test_accepted_missions_do_not_expire(state):
    """Ensure that missions accepted by the player are protected from rival claiming."""
    simulator = WorldSimulator()
    state.missions[0].is_accepted = True
    state.missions[0].expiration_tick = 50
    state.clock.tick_count = 200

    simulator.tick(state)

    # Mission should still exist and be player-owned
    m = next((mi for mi in state.missions if mi.id == 1), None)
    assert m is not None
    assert m.is_accepted is True
    assert getattr(m, "claimed_by", None) is None
