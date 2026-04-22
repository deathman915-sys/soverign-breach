
import pytest

from core.game_state import CPUCore, DataFile, GameState
from core.hardware_engine import HardwareEngine
from core.task_engine import start_task


def test_vfs_bus_speed_affects_io_tasks():
    state = GameState()
    # Setup a standard gateway with 10 GHz total
    state.gateway.cpus = [CPUCore(id=1, base_speed=10, speed=10)]
    state.gateway.storage_overclock = 1.0

    # 1. Create an IO task (File Copier)
    from core.game_state import Computer
    comp = Computer(ip="1.1.1.1", name="Target")
    comp.files.append(DataFile(filename="test.dat", size=10))
    state.computers[comp.ip] = comp

    start_task(state, "File_Copier", 1, "1.1.1.1", {"filename": "test.dat"})
    task = state.tasks[0]
    print(f"\n[DEBUG] CPU Speed: {state.gateway.cpu_speed}, Initial Ticks: {task.ticks_remaining}")
    # File copier requires C.TICKSREQUIRED_COPY * size * cpu_modifier
    # Default is 10 * 10 * (60/10) = 600 ticks.

    # Run 100 ticks at 1.0x OC
    for _ in range(100):
        HardwareEngine.process_tasks(state, 1.0)
    progress_1x = task.progress
    print(f"\n[DEBUG] 1.0x OC: Progress={progress_1x}, TicksRemaining={task.ticks_remaining}")

    # Reset and test with 2.0x OC
    task.progress = 0.0
    task.ticks_remaining = 2700.0
    task.is_active = True
    task.extra["initial_ticks"] = 2700.0 # Also reset extra
    state.gateway.storage_overclock = 2.0

    for _ in range(100):
        HardwareEngine.process_tasks(state, 1.0)
    progress_2x = task.progress
    print(f"[DEBUG] 2.0x OC: Progress={progress_2x}, TicksRemaining={task.ticks_remaining}")

    assert progress_2x > progress_1x, "Storage OC should increase IO task progress speed"
    assert progress_2x == pytest.approx(progress_1x * 2.0, rel=1e-2), "Storage OC 2.0x should double IO task speed"

def test_vfs_bus_speed_does_not_affect_cpu_tasks():
    state = GameState()
    state.gateway.cpus = [CPUCore(id=1, base_speed=10, speed=10)]
    state.gateway.storage_overclock = 1.0

    # 2. Create a CPU task (Password Breaker)
    from core.game_state import Computer, ComputerScreen
    comp = Computer(ip="1.1.1.1", name="Target")
    comp.accounts = {"admin": "password"}
    comp.screens.append(ComputerScreen(screen_type=1))
    state.computers[comp.ip] = comp

    start_task(state, "Password_Breaker", 1, "1.1.1.1", {"target_id": "admin"})
    task = state.tasks[0]

    # Run 1 tick at 1.0x OC
    HardwareEngine.process_tasks(state, 1.0)
    progress_1x = task.progress

    # Reset and test with 2.0x OC
    task.progress = 0.0
    task.is_active = True
    # Re-calculate or reset ticks_remaining to a fixed value for consistency
    task.ticks_remaining = 100.0
    state.gateway.storage_overclock = 2.0

    HardwareEngine.process_tasks(state, 1.0)
    progress_2x = task.progress

    assert progress_2x == progress_1x, "Storage OC should NOT affect CPU-bound tasks"
