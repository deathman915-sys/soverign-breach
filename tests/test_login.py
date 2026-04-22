"""
Onlink-Clone: Login/Startup Screen Tests

Tests login functionality without importing web_main (which starts eel).
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.game_state import GameState


def test_set_player_profile():
    """Test that set_player_profile updates player state."""
    s = GameState()
    assert s.player.name == "Agent"
    assert s.player.handle == "AGENT"

    s.player.name = "TestAgent"
    s.player.handle = "TESTY"

    assert s.player.name == "TestAgent"
    assert s.player.handle == "TESTY"


def test_login_screen_html():
    """Ensure login screen HTML is present."""
    html_path = os.path.join(os.path.dirname(__file__), "..", "web", "index.html")
    with open(html_path, "r") as f:
        content = f.read()
    assert 'id="login-screen"' in content
    assert 'id="login-proceed"' in content
    assert 'id="login-name"' in content
    assert 'id="login-code"' in content


def test_player_defaults():
    """Verify player state defaults match expected starting values."""
    s = GameState()
    assert s.player.balance == 3000
    assert s.player.uplink_rating == 1
    assert s.player.localhost_ip == "127.0.0.1"
    assert len(s.player.known_ips) == 0
    assert len(s.player.known_passwords) == 0


def test_player_known_ips_tracking():
    """Test that known IPs can be added and checked."""
    s = GameState()
    s.player.known_ips.append("1.1.1.1")
    assert "1.1.1.1" in s.player.known_ips
    assert "2.2.2.2" not in s.player.known_ips


def test_player_password_tracking():
    """Test that known passwords are tracked per IP."""
    s = GameState()
    s.player.known_passwords["10.0.0.1"] = "secret"
    assert s.player.known_passwords["10.0.0.1"] == "secret"
    assert "10.0.0.2" not in s.player.known_passwords


def test_profile_persistence(tmp_path):
    """Test saving and loading a profile to/from disk."""
    from core.game_state import CPUCore, GameState
    from core.persistence import load_profile, save_profile

    s = GameState()
    s.player.name = "PersistentAgent"
    s.player.handle = "PERSIST"
    s.player.balance = 99999

    # Modify hardware
    s.gateway.cpus = [CPUCore(id=1, model="SuperCPU", base_speed=100, speed=100, health=80.0)]

    # Save to a temporary file
    save_file = os.path.join(tmp_path, "PERSIST.json")
    save_profile(s, save_file)

    assert os.path.exists(save_file)

    # Load into a new state
    new_s = GameState()
    load_profile(new_s, save_file)

    assert new_s.player.name == "PersistentAgent"
    assert new_s.player.balance == 99999
    assert len(new_s.gateway.cpus) == 1
    assert new_s.gateway.cpus[0].model == "SuperCPU"
    assert new_s.gateway.cpus[0].health == 80.0
