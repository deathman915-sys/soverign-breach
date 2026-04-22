"""
Onlink-Clone: TDD tests for high-impact low-effort features

1. Nuke gateway (requires Self Destruct addon)
2. Neuromancer rating in HUD
3. Bounce chain management UI
4. Task management app (Python backend)
5. Overclocking controls
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from core.game_state import Computer, GameState, NodeType, RunningTask, VFSFile
from core.world_generator import generate_world


# ======================================================================
# Nuke Gateway (requires Self Destruct addon)
# ======================================================================
class TestNukeGateway:
    def test_nuke_requires_self_destruct(self, world):
        """Nuke gateway should require Self Destruct addon."""
        from core.gateway_nuke import nuke_gateway

        world.gateway.has_self_destruct = False
        result = nuke_gateway(world)
        assert result["success"] is False
        assert "Self Destruct" in result.get("error", "")

    def test_nuke_with_self_destruct(self, world):
        """Nuke gateway should work when Self Destruct addon is installed."""
        from core.gateway_nuke import nuke_gateway

        world.gateway.has_self_destruct = True
        world.vfs.files.append(VFSFile(filename="secret.dat", size_gq=2))
        result = nuke_gateway(world)
        assert result["success"] is True
        assert len(world.vfs.files) == 0
        assert world.gateway.is_melted is True

    def test_nuke_is_in_app_registry(self):
        """Nuke gateway should be exposed as an app function."""
        from core.apps.tasks import TasksApp

        app = TasksApp(None)
        funcs = app.expose_functions()
        assert "nuke_gateway" in funcs


# ======================================================================
# Neuromancer Rating in HUD
# ======================================================================
class TestNeuromancerHUD:
    def test_game_state_includes_neuromancer(self, world):
        """get_game_state should include neuromancer rating and level."""
        from core.apps.hardware import HardwareApp

        app = HardwareApp(world)
        result = app.init()
        assert "neuromancer_rating" in result
        assert "neuromancer_level" in result

    def test_neuromancer_level_name(self, world):
        """Neuromancer level should have a human-readable name."""
        from core.neuromancer import get_neuromancer_level

        world.player.neuromancer_rating = 0
        level = get_neuromancer_level(world)
        assert level == "Neutral"

        world.player.neuromancer_rating = -80
        level = get_neuromancer_level(world)
        assert level == "Anarchic"

        world.player.neuromancer_rating = 80
        level = get_neuromancer_level(world)
        assert level == "Sentinel"


# ======================================================================
# Bounce Chain Management
# ======================================================================
class TestBounceChainUI:
    def test_get_bounce_chain(self, world):
        """Should return current bounce chain."""
        from core.remote_controller import RemoteController

        rc = RemoteController(world)
        world.bounce.hops = ["127.0.0.1", "1.1.1.1"]
        result = rc.get_bounce_chain()
        assert result["success"] is True
        assert "127.0.0.1" in result["chain"]
        assert "1.1.1.1" in result["chain"]

    def test_add_bounce_node(self, world):
        """Should be able to add a node to the bounce chain."""
        from core.remote_controller import RemoteController

        rc = RemoteController(world)
        world.computers["1.1.1.1"] = Computer(
            ip="1.1.1.1", name="Proxy", computer_type=NodeType.PUBLIC_SERVER
        )
        result = rc.add_bounce_node("1.1.1.1")
        assert result["success"] is True
        assert "1.1.1.1" in world.bounce.hops

    def test_remove_bounce_node(self, world):
        """Should be able to remove a node from the bounce chain."""
        from core.remote_controller import RemoteController

        rc = RemoteController(world)
        world.bounce.hops = ["127.0.0.1", "1.1.1.1"]
        result = rc.remove_bounce_node("1.1.1.1")
        assert result["success"] is True
        assert "1.1.1.1" not in world.bounce.hops

    def test_reorder_bounce_chain(self, world):
        """Should be able to reorder bounce chain."""
        from core.remote_controller import RemoteController

        rc = RemoteController(world)
        world.bounce.hops = ["127.0.0.1", "1.1.1.1", "2.2.2.2"]
        result = rc.reorder_bounce_chain(["127.0.0.1", "2.2.2.2", "1.1.1.1"])
        assert result["success"] is True
        assert world.bounce.hops == ["127.0.0.1", "2.2.2.2", "1.1.1.1"]


# ======================================================================
# Task Management App
# ======================================================================
class TestTaskManagementApp:
    def test_task_app_exists(self):
        """Task management app should exist."""
        from core.apps.tasks import TasksApp

        assert TasksApp.app_id == "tasks"

    def test_task_app_init(self, world):
        """Task app should return task list."""
        from core.apps.tasks import TasksApp

        app = TasksApp(world)
        result = app.init()
        assert isinstance(result, dict)
        assert "tasks" in result

    def test_task_app_lists_tasks(self, world):
        """Task app should list active tasks."""
        from core.apps.tasks import TasksApp

        world.tasks.append(
            RunningTask(
                task_id=1,
                tool_name="Password_Breaker",
                target_ip="10.0.0.1",
                cpu_cost_ghz=30,
                progress=0.5,
                is_active=True,
            )
        )
        app = TasksApp(world)
        result = app.init()
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["tool"] == "Password_Breaker"

    def test_task_app_stop_task(self, world):
        """Task app should expose stop_task function."""
        from core.apps.tasks import TasksApp

        world.tasks.append(
            RunningTask(
                task_id=1,
                tool_name="Password_Breaker",
                target_ip="10.0.0.1",
                cpu_cost_ghz=30,
                progress=0.5,
                is_active=True,
            )
        )
        app = TasksApp(world)
        funcs = app.expose_functions()
        assert "stop_task" in funcs

    def test_task_app_nuke_gateway(self, world):
        """Task app should expose nuke_gateway function."""
        from core.apps.tasks import TasksApp

        app = TasksApp(world)
        funcs = app.expose_functions()
        assert "nuke_gateway" in funcs


# ======================================================================
# Overclocking Controls
# ======================================================================
class TestOverclockingUI:
    def test_set_cpu_overclock(self, world):
        """Should be able to set CPU overclock."""
        from core.hardware_engine import HardwareEngine

        HardwareEngine.set_cpu_overclock(world, 1, 2.0)
        assert world.gateway.cpus[0].overclock == 2.0

    def test_set_ram_overclock(self, world):
        """Should be able to set RAM overclock."""
        from core.hardware_engine import HardwareEngine

        HardwareEngine.set_ram_overclock(world, 1.5)
        assert world.gateway.ram_overclock == 1.5

    def test_overclock_in_hardware_app(self, world):
        """Hardware app init should include overclock info."""
        from core.apps.hardware import HardwareApp

        app = HardwareApp(world)
        result = app.init()
        assert "overclock" in result


# ======================================================================
# Fixture
# ======================================================================
@pytest.fixture
def world():
    s = GameState()
    generate_world(s)
    return s
