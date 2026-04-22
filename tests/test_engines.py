"""Quick smoke test for the ported engines."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core import constants as C
from core.game_state import Computer, ComputerScreen, GameState
from core.security_engine import check_security_breaches
from core.task_engine import start_task, tick_task
from core.trace_engine import check_completed_traces, start_trace, tick_traces
from core.world_generator import generate_world


def test_world_gen():
    s = GameState()
    generate_world(s)
    assert len(s.computers) >= 29, f"Only {len(s.computers)} computers"
    assert len(s.world.companies) > 10
    assert len(s.world.people) > 20
    print(
        f"✓ World: {len(s.computers)} computers, {len(s.world.companies)} companies, {len(s.world.people)} people"
    )


def test_task_engine():
    s = GameState()
    # Add a simple computer with a password screen
    s.computers["10.0.0.1"] = Computer(
        ip="10.0.0.1",
        name="Test Server",
        hack_difficulty=5,
        screens=[ComputerScreen(screen_type=C.SCREEN_PASSWORDSCREEN, data1="abc123")],
    )
    from core.game_state import CPUCore

    s.gateway.cpus = [CPUCore(id=1, model="Standard", base_speed=60, speed=60)]

    data = start_task(s, "Password_Breaker", 1, "10.0.0.1")
    assert data["tool_name"] == "Password_Breaker"
    assert len(s.tasks) == 1

    # Tick until done
    for _ in range(500):
        r = tick_task(s, s.tasks[0], 1.0)
        if r["completed"]:
            break
    assert r["completed"], "Task did not complete in 500 ticks"
    print(
        f"✓ Task: Password_Breaker completed, revealed: {r['data']['extra'].get('revealed', '')}"
    )


def test_trace_engine():
    from core.game_state import Connection, ConnectionNode

    s = GameState()
    s.computers["10.0.0.1"] = Computer(ip="10.0.0.1", name="Target", trace_speed=5.0)
    s.connection = Connection(
        target_ip="10.0.0.1",
        is_active=True,
        nodes=[ConnectionNode(position=0, ip="10.0.0.1")],
    )
    start_trace(s)
    assert s.connection.trace_active

    for _ in range(100):
        tick_traces(s, 1.0)
    completions = check_completed_traces(s)
    assert len(completions) > 0, "Trace did not complete"
    print(f"✓ Trace: completed, progress={s.connection.trace_progress:.2f}")


def test_security_engine():
    from core.game_state import Connection, SecuritySystem

    s = GameState()
    s.computers["10.0.0.1"] = Computer(
        ip="10.0.0.1",
        name="Secured Server",
        security_systems=[SecuritySystem(security_type=3, level=1)],
    )
    s.connection = Connection(target_ip="10.0.0.1", is_active=True)
    events = check_security_breaches(s)
    assert len(events) > 0, "No security breach detected"
    assert s.connection.trace_active, "Trace not started by security"
    print(f"✓ Security: breach detected on {events[0]['computer_name']}")


def test_mission_negotiation():
    from core.mission_engine import accept_mission, generate_missions, negotiate_mission

    s = GameState()
    generate_world(s)
    missions = generate_missions(s, 1)
    assert len(missions) == 1
    mission = missions[0]
    original_payment = mission.payment

    # Negotiate (with retry due to random refusal - 20% refusal rate, 20 retries = ~99% success)
    for attempt in range(20):
        res = negotiate_mission(s, mission.id, 0.1)
        if res["success"]:
            break
    assert res["success"], f"Negotiation failed after 20 attempts: {res.get('msg')}"
    new_payment = res["new_payment"]
    assert new_payment > original_payment
    assert mission.payment == new_payment
    assert mission.is_negotiated is True

    # Accept mission
    res = accept_mission(s, mission.id)
    assert res["success"]
    # Verify mission is accepted and payment is updated
    assert mission.is_accepted is True
    assert mission.payment == new_payment
    print(
        f"✓ Mission negotiation: payment increased from {original_payment} to {new_payment}"
    )


if __name__ == "__main__":
    test_world_gen()
    test_task_engine()
    test_trace_engine()
    test_security_engine()
    test_mission_negotiation()
    print("\nAll engine tests passed! ✓")
