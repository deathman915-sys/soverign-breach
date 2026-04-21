"""
Onlink-Clone: Core Module Tests

Verifies the GameState mediator, NetworkGraph pathfinding,
VFS operations, and WorldSimulator stability.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.game_state import (
    GameState,
    Computer,
    NodeType,
    VFSFile,
    SoftwareType,
    Company,
    Person,
)
from core.network_graph import NetworkGraph
from core.vfs import VirtualFileSystem
from core.world_sim import WorldSimulator


# ======================================================================
# GameState defaults
# ======================================================================
class TestGameState:
    def test_default_state(self):
        s = GameState()
        assert s.player.handle == "AGENT"
        # Sum of default CPUs: 10 + 10 = 20
        assert s.gateway.cpu_speed == 20
        assert s.clock.tick_count == 0
        assert len(s.computers) == 0
        assert len(s.tasks) == 0

    def test_vfs_used_gq(self):
        s = GameState()
        s.vfs.files.append(VFSFile(id="test.dat", filename="test.dat", size_gq=5))
        assert s.vfs.used_gq == 5
        assert s.vfs.free_gq == 59  # 64 - 5

    def test_nodes_backward_compat(self):
        """state.nodes should alias state.computers"""
        s = GameState()
        s.computers["1.1.1.1"] = Computer(ip="1.1.1.1", name="Test")
        assert "1.1.1.1" in s.nodes
        assert s.nodes is s.computers


# ======================================================================
# Network graph
# ======================================================================
class TestNetworkGraph:
    def test_add_and_get_node(self):
        s = GameState()
        NetworkGraph.add_node(s, Computer(ip="A", name="A", trace_speed=-1))
        NetworkGraph.add_node(s, Computer(ip="B", name="B", trace_speed=10))
        NetworkGraph.add_node(s, Computer(ip="C", name="C", trace_speed=20))
        NetworkGraph.add_node(s, Computer(ip="D", name="D", trace_speed=5))
        assert NetworkGraph.get_node(s, "A") is not None
        assert NetworkGraph.get_node(s, "Z") is None

    def test_bidirectional_link(self):
        s = GameState()
        NetworkGraph.add_node(s, Computer(ip="1.2.3.4", name="Test"))
        assert "1.2.3.4" in s.computers

    def test_shortest_path_prefers_high_trace_speed(self):
        s = GameState()
        NetworkGraph.add_node(s, Computer(ip="A", name="A"))
        NetworkGraph.add_node(s, Computer(ip="B", name="B"))
        # Via B (trace_speed=20 → slow to trace → preferred)
        NetworkGraph.add_node(s, Computer(ip="FAST", name="Fast", trace_speed=20))
        # Via D (trace_speed=2 → fast trace → less preferred)
        NetworkGraph.add_node(s, Computer(ip="SLOW", name="Slow", trace_speed=2))

        NetworkGraph.add_link(s, "A", "FAST")
        NetworkGraph.add_link(s, "FAST", "B")
        NetworkGraph.add_link(s, "A", "SLOW")
        NetworkGraph.add_link(s, "SLOW", "B")

        path = NetworkGraph.shortest_path(s, "A", "B")
        assert "FAST" in path

    def test_shortest_path_unreachable(self):
        s = GameState()
        NetworkGraph.add_node(s, Computer(ip="X", name="X"))
        NetworkGraph.add_node(s, Computer(ip="Y", name="Y"))
        path = NetworkGraph.shortest_path(s, "X", "Y")
        assert path == []

    def test_trace_time(self):
        s = GameState()
        NetworkGraph.add_node(s, Computer(ip="A", name="A", trace_speed=10))
        NetworkGraph.add_node(s, Computer(ip="B", name="B", trace_speed=5))
        from core.game_state import BounceChain

        chain = BounceChain(hops=["A", "B"])
        assert NetworkGraph.trace_time(s, chain) == 15.0

    def test_blackout_region(self):
        s = GameState()
        NetworkGraph.add_node(s, Computer(ip="S", name="S", region="London"))
        NetworkGraph.add_node(s, Computer(ip="T", name="T", region="Tokyo"))
        affected = NetworkGraph.blackout_region(s, "London")
        assert "S" in affected
        assert "T" not in affected
        assert not s.computers["S"].is_online
        assert s.computers["T"].is_online

    def test_restore_region(self):
        s = GameState()
        NetworkGraph.add_node(s, Computer(ip="S", name="S", region="London"))
        NetworkGraph.blackout_region(s, "London")
        assert not s.computers["S"].is_online
        NetworkGraph.restore_region(s, "London")
        assert s.computers["S"].is_online

    def test_remove_node(self):
        s = GameState()
        NetworkGraph.add_node(s, Computer(ip="A", name="A"))
        NetworkGraph.add_node(s, Computer(ip="B", name="B"))
        NetworkGraph.add_link(s, "A", "B")
        NetworkGraph.remove_node(s, "A")
        assert "A" not in s.computers
        assert "A" not in s.computers["B"].links


# ======================================================================
# VFS
# ======================================================================
class TestVFS:
    def test_store_and_list(self):
        s = GameState()
        f = VFSFile(filename="test.dat", size_gq=5)
        assert VirtualFileSystem.store_file(s, f)
        assert len(VirtualFileSystem.list_files(s)) == 1

    def test_store_over_capacity(self):
        s = GameState()
        f = VFSFile(filename="huge.dat", size_gq=999)
        assert not VirtualFileSystem.store_file(s, f)

    def test_delete_file(self):
        s = GameState()
        VirtualFileSystem.store_file(s, VFSFile(filename="a.dat", size_gq=1))
        assert VirtualFileSystem.delete_file(s, "a.dat")
        assert len(s.vfs.files) == 0

    def test_delete_nonexistent(self):
        s = GameState()
        assert not VirtualFileSystem.delete_file(s, "ghost.dat")

    def test_find_file(self):
        s = GameState()
        VirtualFileSystem.store_file(s, VFSFile(filename="secret.dat", size_gq=2))
        assert VirtualFileSystem.find_file(s, "secret.dat") is not None
        assert VirtualFileSystem.find_file(s, "nope.dat") is None

    def test_find_software(self):
        s = GameState()
        VirtualFileSystem.store_file(
            s,
            VFSFile(
                filename="Password Breaker v1",
                size_gq=2,
                file_type=2,
                software_type=SoftwareType.CRACKERS,
                version=1,
            ),
        )
        result = VirtualFileSystem.find_software(s, "Password Breaker")
        assert result is not None
        assert result.version == 1

    def test_defrag(self):
        s = GameState()
        VirtualFileSystem.store_file(
            s, VFSFile(filename="a.dat", size_gq=0)
        )  # zero-size ghost
        VirtualFileSystem.store_file(s, VFSFile(filename="b.dat", size_gq=3))
        VirtualFileSystem.store_file(
            s, VFSFile(filename="b.dat", size_gq=3, version=2)
        )  # dup
        reclaimed = VirtualFileSystem.defrag(s)
        assert reclaimed > 0
        assert len(s.vfs.files) == 1  # only b.dat v2 remains

    def test_upgrade_memory(self):
        s = GameState()
        VirtualFileSystem.upgrade_memory(s, 64)
        assert s.vfs.total_memory_gq == 64
        assert s.gateway.storage_capacity == 64


# ======================================================================
# World simulation
# ======================================================================
class TestWorldSim:
    def test_tick_no_crash(self):
        s = GameState()
        s.world.people = [Person(id=1, name="Bot", is_agent=True, uplink_rating=3)]
        s.world.companies = [Company(name="TestCo")]
        ws = WorldSimulator()
        for _ in range(100):
            s.clock.tick_count += 1
            ws.tick(s)
        # Verify the world simulator actually did something
        assert s.clock.tick_count == 100
        assert len(s.world.people) > 0

    def test_blackout_crashes_stocks(self):
        s = GameState()
        NetworkGraph.add_node(
            s,
            Computer(
                ip="10.0.0.1",
                name="Svr",
                computer_type=NodeType.INTERNAL_SRV,
                region="London",
            ),
        )
        s.world.companies = [Company(name="TestCo", stock_price=100.0, region="London")]
        ws = WorldSimulator()
        ws.trigger_blackout(s, "London")
        assert s.world.companies[0].stock_price < 100.0
        assert not s.computers["10.0.0.1"].is_online

    def test_blackout_restore(self):
        s = GameState()
        NetworkGraph.add_node(s, Computer(ip="1.1.1.1", name="S", region="London"))
        s.world.companies = [Company(name="Co", region="London")]
        ws = WorldSimulator()
        ws.trigger_blackout(s, "London")
        # Fast-forward past restore time
        s.clock.tick_count = 99999
        ws.tick(s)
        assert s.computers["1.1.1.1"].is_online
