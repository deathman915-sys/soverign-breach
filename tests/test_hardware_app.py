
from core.game_state import GameState, CPUCore
from core.apps.hardware import HardwareApp

def test_hardware_app_returns_all_high_fidelity_fields():
    state = GameState()
    state.gateway.cpus = [CPUCore(id=1, health=95.0, overclock=1.2)]
    state.gateway.psu_capacity = 750.0
    state.gateway.storage_overclock = 1.5
    
    app = HardwareApp(state)
    data = app.init()
    
    # Missing fields in current implementation based on audit
    assert "storage_overclock" in data
    assert "psu_capacity" in data
    assert "cpus" in data
    assert data["cpus"][0]["health"] == 95.0
    assert data["cpus"][0]["overclock"] == 1.2
    assert "power_draw" in data
    assert "heat" in data
    assert "max_heat" in data
    assert "ram_health" in data
    assert "storage_health" in data
