"""
Onlink-Clone: TDD tests for gateway nuke and neuromancer rating
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from core.game_state import GameState, VFSFile
from core.world_generator import generate_world


class TestGatewayNuke:
    def test_nuke_gateway(self, world):
        """Nuking the gateway should destroy all files and crash the system."""
        from core.gateway_nuke import nuke_gateway

        world.gateway.has_self_destruct = True
        world.vfs.files.append(VFSFile(filename="secret.dat", size_gq=2))
        result = nuke_gateway(world)
        assert result["success"] is True
        assert len(world.vfs.files) == 0
        assert world.gateway.is_melted is True

    def test_nuke_gateway_when_not_connected(self, world):
        """Can always nuke your own gateway."""
        from core.gateway_nuke import nuke_gateway

        world.gateway.has_self_destruct = True
        world.connection.is_active = False
        result = nuke_gateway(world)
        assert result["success"] is True

    def test_nuke_gateway_emits_event(self, world):
        """Nuking should emit a game_over event."""
        from core.gateway_nuke import nuke_gateway

        world.gateway.has_self_destruct = True
        result = nuke_gateway(world)
        assert "game_over" in result
        assert result["game_over"] is True


class TestNeuromancerRating:
    def test_neuromancer_rating_starts_at_default(self, world):
        """Player should start with a neuromancer rating."""
        assert world.player.neuromancer_rating >= 0

    def test_steal_file_increases_rating(self, world):
        """Stealing files should slightly increase neuromancer rating."""
        from core.neuromancer import adjust_neuromancer

        old = world.player.neuromancer_rating
        adjust_neuromancer(world, "steal_file", 1)
        assert world.player.neuromancer_rating >= old

    def test_trace_user_decreases_rating(self, world):
        """Tracing users should decrease neuromancer rating."""
        from core.neuromancer import adjust_neuromancer

        old = world.player.neuromancer_rating
        adjust_neuromancer(world, "trace_user", 1)
        assert world.player.neuromancer_rating < old

    def test_frame_user_decreases_rating(self, world):
        """Framing users should decrease neuromancer rating significantly."""
        from core.neuromancer import adjust_neuromancer

        old = world.player.neuromancer_rating
        adjust_neuromancer(world, "frame_user", 1)
        assert world.player.neuromancer_rating < old

    def test_neuromancer_rating_has_levels(self, world):
        """Neuromancer rating should have named levels."""
        from core.neuromancer import NEUROMANCER_LEVELS, get_neuromancer_level

        world.player.neuromancer_rating = 0
        level = get_neuromancer_level(world)
        assert level in NEUROMANCER_LEVELS.values() or level in NEUROMANCER_LEVELS

    def test_neuromancer_rating_bounded(self, world):
        """Rating should be bounded between min and max."""
        from core.neuromancer import adjust_neuromancer

        for _ in range(100):
            adjust_neuromancer(world, "steal_file", 1)
        assert world.player.neuromancer_rating <= 100

        for _ in range(200):
            adjust_neuromancer(world, "trace_user", 1)
        assert world.player.neuromancer_rating >= -100


@pytest.fixture
def world():
    s = GameState()
    generate_world(s)
    return s
