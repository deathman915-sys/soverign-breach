"""
Onlink-Clone: TDD tests for trace speed modifiers

In Uplink, trace speed is modified by:
- Having an account on target: 0.7x
- Admin access on target: 1.0x (normal)
- Mainframe routing: 1.3x
- Bank admin access: 1.6x
- No account at all: 0.1x (very slow trace)
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from core.game_state import BankAccount, Computer, GameState, NodeType
from core.world_generator import generate_world


class TestTraceSpeedModifiers:
    def test_base_trace_speed(self, world):
        """Trace speed should have a base value."""
        from core.trace_engine import calculate_trace_speed

        world.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1",
            name="Target",
            computer_type=NodeType.INTERNAL_SRV,
            trace_speed=10,
        )
        speed = calculate_trace_speed(world, "10.0.0.1")
        assert speed > 0

    def test_no_account_slows_trace(self, world):
        """Having no account should slow the trace significantly (0.1x)."""
        from core.trace_engine import calculate_trace_speed

        world.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1",
            name="Target",
            computer_type=NodeType.INTERNAL_SRV,
            trace_speed=10,
        )
        # No account, no known password
        speed = calculate_trace_speed(world, "10.0.0.1")
        # Should be much slower than base
        base_speed = world.computers["10.0.0.1"].trace_speed
        assert speed < base_speed

    def test_known_password_speeds_trace(self, world):
        """Having a known password should speed up trace (0.7x)."""
        from core.trace_engine import calculate_trace_speed

        world.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1",
            name="Target",
            computer_type=NodeType.INTERNAL_SRV,
            trace_speed=10,
        )
        world.player.known_passwords["10.0.0.1"] = "secret"
        speed = calculate_trace_speed(world, "10.0.0.1")
        base_speed = world.computers["10.0.0.1"].trace_speed
        # Should be faster than no-account but slower than admin
        assert speed > base_speed * 0.05
        assert speed <= base_speed

    def test_admin_access_normal_speed(self, world):
        """Admin access should give normal trace speed (1.0x)."""
        from core.trace_engine import calculate_trace_speed

        world.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1",
            name="Target",
            computer_type=NodeType.INTERNAL_SRV,
            trace_speed=10,
        )
        world.player.known_passwords["10.0.0.1"] = "admin"
        world.computers["10.0.0.1"].accounts["admin"] = "admin"
        speed = calculate_trace_speed(world, "10.0.0.1")
        base_speed = world.computers["10.0.0.1"].trace_speed
        assert speed >= base_speed

    def test_bank_admin_faster_trace(self, world):
        """Bank admin access should give faster trace (1.6x)."""
        from core.trace_engine import calculate_trace_speed

        world.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1",
            name="Test Bank",
            computer_type=NodeType.INTERNAL_SRV,
            trace_speed=10,
        )
        world.player.known_passwords["10.0.0.1"] = "admin"
        world.computers["10.0.0.1"].accounts["admin"] = "admin"
        world.bank_accounts.append(
            BankAccount(
                id=1,
                bank_ip="10.0.0.1",
                account_number="12345",
                balance=0,
                loan_amount=0,
            )
        )
        speed = calculate_trace_speed(world, "10.0.0.1")
        base_speed = world.computers["10.0.0.1"].trace_speed
        assert speed > base_speed


@pytest.fixture
def world():
    s = GameState()
    generate_world(s)
    return s
