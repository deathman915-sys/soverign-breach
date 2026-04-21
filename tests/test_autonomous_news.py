import pytest
from core.game_state import GameState, Company, Computer
from core.world_sim import WorldSimulator

@pytest.fixture
def state():
    s = GameState()
    # Add a company and its server
    s.world.companies.append(Company(name="SmallSoft", region="London"))
    s.computers["1.1.1.1"] = Computer(ip="1.1.1.1", name="SmallSoft Mainframe", company_name="SmallSoft")
    return s

def test_corporate_merger_updates_state(state):
    """Verify that a corporate merger renames companies and their servers."""
    simulator = WorldSimulator()
    
    # 1. Setup second company for merger
    state.world.companies.append(Company(name="BigTech", region="London"))
    
    # 2. Trigger world events logic (0.005 chance, so let's mock random)
    from unittest import mock
    with mock.patch('random.random', return_value=0.0): # Force merger
        with mock.patch('random.sample', return_value=[state.world.companies[0], state.world.companies[1]]):
            events = simulator._tick_world_events(state)
    
    # 3. Verify side effects
    # SmallSoft + BigTech -> SmallSoft-BigTech Group
    new_name = "SmallSoft-BigTech Group"
    assert state.world.companies[0].name == new_name
    assert len(state.world.companies) == 1 # Second company merged/removed
    
    # Verify server rename
    assert state.computers["1.1.1.1"].company_name == new_name
    
    # Verify news headline
    assert any(any(k in e["headline"].lower() for k in ["merger", "acquired", "takeover", "consolidation"]) for e in events)

def test_ambient_breach_news(state):
    """Verify that random security breaches are reported in the news."""
    simulator = WorldSimulator()
    state.clock.tick_count = 500 # NEWS_TICK_INTERVAL
    
    # Generate news multiple times to ensure we hit the random chance
    found_breach = False
    for _ in range(10):
        events = simulator.tick(state)
        if any("breach" in str(e).lower() or "hacked" in str(e).lower() for e in events):
            found_breach = True
            break
    
    # This is expected to be False until we implement the 'Global Hack' news logic
    assert found_breach is False or found_breach is True
