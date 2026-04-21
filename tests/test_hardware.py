"""
Onlink-Clone: Hardware Engine Edge Case Tests

Tests thermal limits, component degradation, CPU scheduling,
PSU capacity, and the melted flag behavior.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from core.game_state import GameState, CPUCore, RunningTask
from core.hardware_engine import HardwareEngine


@pytest.fixture
def state():
    return GameState()


class TestIdleState:
    def test_default_heat(self, state):
        assert state.gateway.heat == 25.0

    def test_default_power(self, state):
        assert state.gateway.power_draw > 0

    def test_not_melted(self, state):
        assert state.gateway.is_melted is False


class TestOverclocking:
    def test_set_cpu_overclock(self, state):
        HardwareEngine.set_cpu_overclock(state, 1, 2.0)
        assert state.gateway.cpus[0].overclock == 2.0

    def test_overclock_increases_power(self, state):
        HardwareEngine.set_cpu_overclock(state, 1, 2.0)
        HardwareEngine.process_tick(state)
        assert state.gateway.power_draw > 40.0

    def test_overclock_increases_heat(self, state):
        HardwareEngine.set_cpu_overclock(state, 1, 2.0)
        for _ in range(50):
            HardwareEngine.process_tick(state)
        assert state.gateway.heat > 25.0

    def test_ram_overclock(self, state):
        HardwareEngine.set_ram_overclock(state, 1.5)
        assert state.gateway.ram_overclock == 1.5


class TestMeltdown:
    def test_forced_meltdown(self, state):
        state.gateway.heat = 100.0
        HardwareEngine.process_tick(state)
        assert state.gateway.is_melted is True

    def test_meltdown_damages_cpu(self, state):
        state.gateway.heat = 100.0
        HardwareEngine.process_tick(state)
        assert state.gateway.cpus[0].health < 100.0

    def test_meltdown_damages_ram(self, state):
        state.gateway.heat = 100.0
        HardwareEngine.process_tick(state)
        assert state.gateway.ram_health < 100.0

    def test_meltdown_damages_storage(self, state):
        state.gateway.heat = 100.0
        HardwareEngine.process_tick(state)
        assert state.gateway.storage_health < 100.0


class TestCPUAllocation:
    def test_single_task_gets_all(self, state):
        state.tasks = [RunningTask(task_id=1, cpu_cost_ghz=60.0)]
        total = 60.0
        share = HardwareEngine.allocate_cpu_power(state, total, 60.0)
        assert share > 0

    def test_two_tasks_split_proportionally(self, state):
        state.tasks = [
            RunningTask(task_id=1, cpu_cost_ghz=30.0),
            RunningTask(task_id=2, cpu_cost_ghz=30.0),
        ]
        total = 60.0
        s1 = HardwareEngine.allocate_cpu_power(state, total, 30.0)
        s2 = HardwareEngine.allocate_cpu_power(state, total, 30.0)
        assert s1 == s2


class TestPSULimits:
    def test_overload_trips(self, state):
        state.gateway.psu_capacity = 10.0
        state.tasks = [RunningTask(task_id=1, cpu_cost_ghz=60.0, power_cost=50.0)]
        HardwareEngine.process_tick(state)
        assert state.gateway.power_draw > state.gateway.psu_capacity


class TestComponentHealth:
    def test_cpu_health_cannot_go_negative(self, state):
        state.gateway.heat = 200.0
        for _ in range(100):
            HardwareEngine.process_tick(state)
        for cpu in state.gateway.cpus:
            assert cpu.health >= 0.0

    def test_ram_health_cannot_go_negative(self, state):
        state.gateway.heat = 200.0
        for _ in range(100):
            HardwareEngine.process_tick(state)
        assert state.gateway.ram_health >= 0.0

    def test_storage_health_cannot_go_negative(self, state):
        state.gateway.heat = 200.0
        for _ in range(100):
            HardwareEngine.process_tick(state)
        assert state.gateway.storage_health >= 0.0


class TestTaskPerformance:
    def test_task_progress_depends_on_cpu_speed(self, state):
        # Setup: 1 task, 100% priority
        task = RunningTask(task_id=1, tool_name="TestTool", cpu_cost_ghz=10.0, ticks_remaining=100.0)
        state.tasks = [task]
        
        # Base speed 20GHz
        state.gateway.cpus = [CPUCore(id=1, model="Test", base_speed=20, speed=20)]
        
        # Process tick
        HardwareEngine.process_tick(state)
        
        # Expected: 20 GHz available. task is 100% priority.
        # If simulation uses (share / 10.0) as in prototype: 20/10 = 2.0 progress units.
        # But core/engine.py currently uses ticks_remaining -= 1.0 * speed_multiplier
        # We need to unify this. Let's assert ticks_remaining decreased.
        assert task.ticks_remaining < 100.0
        initial_reduction = 100.0 - task.ticks_remaining
        
        # Increase CPU speed and check if reduction is greater
        state.gateway.cpus = [CPUCore(id=1, model="Test", base_speed=40, speed=40)]
        task.ticks_remaining = 100.0
        HardwareEngine.process_tick(state)
        assert (100.0 - task.ticks_remaining) > initial_reduction

    def test_degraded_health_reduces_performance(self, state):
        state.gateway.cpus = [CPUCore(id=1, model="Test", base_speed=20, speed=20, health=100.0)]
        task = RunningTask(task_id=1, ticks_remaining=100.0)
        state.tasks = [task]
        
        HardwareEngine.process_tick(state)
        full_health_reduction = 100.0 - task.ticks_remaining
        
        # Degrade health
        state.gateway.cpus[0].health = 50.0
        task.ticks_remaining = 100.0
        HardwareEngine.process_tick(state)
        degraded_reduction = 100.0 - task.ticks_remaining
        
        assert degraded_reduction < full_health_reduction

    def test_priority_splits_cpu_power(self, state):
        state.gateway.cpus = [CPUCore(id=1, model="Test", base_speed=20, speed=20)]
        t1 = RunningTask(task_id=1, cpu_cost_ghz=10.0, ticks_remaining=100.0)
        t2 = RunningTask(task_id=2, cpu_cost_ghz=10.0, ticks_remaining=100.0)
        state.tasks = [t1, t2]
        
        HardwareEngine.process_tick(state)
        
        # They should both progress equally if priorities are equal
        assert t1.ticks_remaining == t2.ticks_remaining
        
        # Change priority
        t1.cpu_cost_ghz = 30.0 # 3x more priority
        t1.ticks_remaining = 100.0
        t2.ticks_remaining = 100.0
        HardwareEngine.process_tick(state)
        
        r1_new = 100.0 - t1.ticks_remaining
        r2_new = 100.0 - t2.ticks_remaining
        
        assert r1_new > r2_new

    def test_cpu_utilization_increases_power(self, state):
        # Setup: 1 task with many ticks so it stays active
        state.tasks = [RunningTask(task_id=1, cpu_cost_ghz=10.0, power_cost=0.0, ticks_remaining=1000.0)]
        # Base speed 10GHz
        state.gateway.cpus = [CPUCore(id=1, base_speed=10, speed=10)]
        
        HardwareEngine.process_tick(state)
        p1 = state.gateway.power_draw
        
        # Reset task ticks for consistency
        state.tasks[0].ticks_remaining = 1000.0
        # Increase CPU speed (meaning more utilization for the same task)
        state.gateway.cpus[0].base_speed = 40
        HardwareEngine.process_tick(state)
        p2 = state.gateway.power_draw
        
        assert p2 > p1, f"Higher CPU utilization should draw more power. p1={p1}, p2={p2}"
