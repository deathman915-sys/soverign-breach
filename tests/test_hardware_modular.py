import pytest

from core.game_state import GameState
from core.store_engine import buy_gateway


@pytest.fixture
def state():
    s = GameState()
    s.player.balance = 50000
    return s

def test_gateway_has_modular_components(state):
    """Verify that the gateway uses modular components for CPU, Modem, and Memory."""
    # Uplink Protocol: CPU count is distinct from Gateway model
    assert hasattr(state.gateway, "cpus")
    assert isinstance(state.gateway.cpus, list)
    assert len(state.gateway.cpus) > 0

    # Modem and Memory should be upgradeable objects or values that persist independently
    assert hasattr(state.gateway, "modem_speed")
    assert hasattr(state.gateway, "memory_gq") # Memory for tools (GQ)
    assert hasattr(state.gateway, "storage_gq") # Storage for files (GQ)

def test_purchase_individual_cpu(state):
    """Verify that we can buy a CPU upgrade without resetting the entire gateway."""
    from core.store_engine import buy_cpu

    initial_modem = state.gateway.modem_speed
    initial_memory = state.gateway.memory_gq

    # Buy 100GHz CPU
    res = buy_cpu(state, cpu_index=0, model="CPU ( 100 Ghz )")
    assert res["success"] is True
    assert state.gateway.cpus[0].base_speed == 100

    # Modem and Memory must remain unchanged
    assert state.gateway.modem_speed == initial_modem
    assert state.gateway.memory_gq == initial_memory

def test_memory_vs_storage_separation(state):
    """Verify that Memory (tool capacity) is separate from VFS Storage (file capacity)."""

    # Starting state
    assert state.gateway.storage_gq == 24
    assert state.vfs.total_memory_gq == 24

    # Upgrade gateway
    buy_gateway(state, "Gateway BETA")

    # VFS should sync with storage_gq
    assert state.gateway.storage_gq == 32
    assert state.vfs.total_memory_gq == 32

    # Memory (RAM) should be distinct
    assert state.gateway.memory_gq == 8 # 32 // 4 heuristic
