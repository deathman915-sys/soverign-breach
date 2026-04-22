import pytest

from core import constants as C
from core.apps.tutorial import TutorialApp
from core.game_state import Computer, GameState, RunningTask


@pytest.fixture
def state():
    s = GameState()
    # Mock InterNIC
    s.computers[C.IP_INTERNIC] = Computer(ip=C.IP_INTERNIC, name="InterNIC")
    return s

@pytest.fixture
def app(state):
    return TutorialApp(state)

def test_tutorial_init(app):
    data = app.init()
    assert data["internic_ip"] == C.IP_INTERNIC

def test_verify_step_1_connect_internic(app, state):
    # Before connection
    assert app.verify_step(1) is False

    # Connect to InterNIC
    state.connection.target_ip = C.IP_INTERNIC
    state.connection.is_active = True
    assert app.verify_step(1) is True

def test_verify_step_2_browse_links(app, state):
    state.connection.target_ip = C.IP_INTERNIC
    state.connection.is_active = True

    # Before navigating to links
    assert app.verify_step(2) is False

    # Navigate to links
    state.connection._current_screen = C.SCREEN_LINKSSCREEN
    assert app.verify_step(2) is True

def test_verify_step_3_bounce(app, state):
    # No hops
    assert app.verify_step(3) is False

    # Add a hop
    state.bounce.hops = [state.player.localhost_ip, C.IP_INTERNIC]
    assert app.verify_step(3) is True

def test_verify_step_4_start_cracking(app, state):
    # No tasks
    assert app.verify_step(4) is False

    # Start Password Breaker
    state.tasks.append(RunningTask(task_id=1, tool_name="Password_Breaker", is_active=True))
    assert app.verify_step(4) is True

def test_verify_step_5_wipe_logs(app, state):
    # No tasks
    assert app.verify_step(5) is False

    # Start Log Deleter
    state.tasks.append(RunningTask(task_id=2, tool_name="Log_Deleter", is_active=True))
    assert app.verify_step(5) is True
