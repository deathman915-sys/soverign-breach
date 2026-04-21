import pytest
from core.game_state import GameState, Computer, SecuritySystem
from core.connection_manager import disconnect
from core import constants as C

@pytest.fixture
def state():
    s = GameState()
    # Mock a target computer with security
    s.computers["1.1.1.1"] = Computer(
        ip="1.1.1.1",
        name="Target",
        security_systems=[
            SecuritySystem(security_type=1, level=1, is_active=True) # Proxy
        ]
    )
    # Establish connection
    s.connection.target_ip = "1.1.1.1"
    s.connection.is_active = True
    return s

def test_security_system_has_bypassed_flag():
    """Verify that SecuritySystem now has an is_bypassed flag, defaulting to False."""
    sec = SecuritySystem(security_type=1)
    assert hasattr(sec, "is_bypassed")
    assert sec.is_bypassed is False

def test_disconnect_resets_bypassed_state(state):
    """Verify that disconnecting from a server resets all its bypassed security systems."""
    comp = state.computers["1.1.1.1"]
    sec = comp.security_systems[0]
    
    # Manually bypass
    sec.is_bypassed = True
    assert sec.is_bypassed is True
    
    # Disconnect
    disconnect(state)
    
    # Verify reset
    assert sec.is_bypassed is False
    assert sec.is_active is True # Should still be 'active' but no longer bypassed

def test_encrypter_type_exists():
    """Verify that SECURITY_TYPE_ENCRYPTER (4) is defined."""
    # This should be added to core.game_state or core.constants
    # Current types: 1=proxy, 2=firewall, 3=monitor
    assert hasattr(C, "SECURITY_TYPE_ENCRYPTER") or hasattr(C, "SEC_TYPE_ENCRYPTER")
