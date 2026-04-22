import pytest

from core import constants as C
from core.game_state import AccessLog, Computer, GameState, SecuritySystem
from core.world_sim import WorldSimulator


@pytest.fixture
def simulator():
    return WorldSimulator()

@pytest.fixture
def state():
    s = GameState()
    # Mock a target computer
    comp = Computer(
        ip="1.1.1.1",
        name="Target",
        security_systems=[
            SecuritySystem(security_type=C.SEC_TYPE_PROXY, is_active=False) # Disabled
        ],
        logs=[
            AccessLog(log_time="10", from_ip="1.2.3.4", subject="Breach", tick_created=10)
        ]
    )
    s.computers["1.1.1.1"] = comp
    s.clock.tick_count = 100
    return s

def test_computer_self_repairs_security(state, simulator):
    """Verify that computers re-enable disabled security over time."""
    comp = state.computers["1.1.1.1"]
    sec = comp.security_systems[0]
    assert sec.is_active is False

    # Tick world significantly (maintenance check every 50 ticks)
    # With 20% repair chance, 10 maintenance ticks (~500 world ticks) should be enough
    for _ in range(1000):
        state.clock.tick_count += 1
        simulator.tick(state)

    # Security should be back online
    assert sec.is_active is True

def test_computer_purges_old_logs(state, simulator):
    """Verify that computers delete logs older than the expiration threshold."""
    comp = state.computers["1.1.1.1"]
    assert len(comp.logs) == 1

    # Tick world past expiration (400 ticks)
    state.clock.tick_count = 600 # 600 - 10 = 590 > 400
    # Must hit a maintenance tick (multiple of 50)
    simulator.tick(state)

    # Old log should be deleted
    assert len([log_entry for log_entry in comp.logs if not log_entry.is_deleted]) == 0

def test_password_rotation(state, simulator):
    """Verify that admin passwords change after a breach or periodically."""
    comp = state.computers["1.1.1.1"]
    # Mark as breached (player knows password)
    state.player.known_passwords[comp.ip] = "initial"

    # Add password screen
    from core.game_state import ComputerScreen
    comp.screens.append(ComputerScreen(screen_type=1, data1="initial"))

    # Tick world significantly
    for _ in range(10000):
        state.clock.tick_count += 1
        simulator.tick(state)
        if comp.ip not in state.player.known_passwords:
            break

    # Password should have rotated (removed from known_passwords)
    assert comp.ip not in state.player.known_passwords
