"""
Sovereign Breach: Phase 27 TDD - UI Logic Resonance (FINAL CALIBRATION)
Tests the backend hooks for the newly forged UI features:
1. Record Alteration
2. Hardware Overclocking
3. Log Modification & Recovery
"""
import pytest

from core.game_state import AccessLog, Computer, CPUCore, GameState, Record
from core.hardware_engine import HardwareEngine
from core.remote_controller import RemoteController


@pytest.fixture
def state():
    s = GameState()
    s.player.balance = 10000
    # Setup a mock computer for remote ops
    c = Computer("1.1.1.1", "TEST_NODE")
    # Use real Record objects
    c.recordbank = [
        Record(name="VICTORIQUE", fields={"status": "ACTIVE", "clearance": "ALPHA"})
    ]
    s.computers["1.1.1.1"] = c
    return s

def test_record_alteration(state):
    rc = RemoteController(state)
    # Test altering a record field
    res = rc.alter_record("1.1.1.1", "VICTORIQUE", "status", "DISAVOWED")
    assert res["success"] is True
    assert state.computers["1.1.1.1"].recordbank[0].fields["status"] == "DISAVOWED"

def test_hardware_overclocking(state):
    # Test CPU Overclocking
    # Ensure gateway has CPUs (class is CPUCore)
    state.gateway.cpus = [CPUCore(id=0, base_speed=2.0)]

    success = HardwareEngine.set_cpu_overclock(state, 0, 2.5) # 250%
    assert success is True
    assert state.gateway.cpus[0].overclock == 2.5
    assert state.gateway.cpus[0].speed == 5.0 # 2.0 * 2.5

    # Test RAM Overclocking
    HardwareEngine.set_ram_overclock(state, 1.5) # 150%
    assert state.gateway.ram_overclock == 1.5

def test_log_manipulation_and_recovery(state):
    rc = RemoteController(state)
    # Setup a log (class is AccessLog)
    comp = state.computers["1.1.1.1"]
    comp.logs = [AccessLog("Login", "1.2.3.4")]
    # Internal backup is managed by comp.add_log, but we'll simulate it
    import copy
    comp.internal_logs = [copy.deepcopy(comp.logs[0])]

    # Modify log
    res = rc.modify_log("1.1.1.1", 0, "9.9.9.9", "Connection closed")
    assert res["success"] is True
    assert comp.logs[0].from_ip == "9.9.9.9"
    assert comp.logs[0].suspicion_level >= 1

    # Verify modification detected
    assert comp.log_modified(0) is True

    # Recover log
    # Note: recover_log is a method on the Computer class
    success = comp.recover_log(0)
    assert success is True
    assert comp.logs[0].from_ip == "1.2.3.4"
    assert comp.log_modified(0) is False
