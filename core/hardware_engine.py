"""
Onlink-Clone: Hardware & VFS Engine
Handles real-time calculation of power draw, heat generation, component
degradation, and CPU priority scheduling for active tasks.
"""
from __future__ import annotations

import logging

from core import task_engine
from core.game_state import GameState, RunningTask

log = logging.getLogger(__name__)

class HardwareEngine:
    """
    Standalone engine to process physical gateway constraints.
    Called by the main engine.py loop.
    """

    @staticmethod
    def process_tick(state: GameState, speed_multiplier: float = 1.0) -> tuple[list[dict], list[RunningTask]]:
        """
        Calculates power, heat, component health, and progresses tasks.
        Returns (progress_updates, completed_tasks).
        """
        gw = state.gateway

        # 1. Process Active Tasks Performance
        # We do this first to calculate CPU utilization
        progress_updates, completed_tasks, total_utilization_ghz = HardwareEngine.process_tasks(state, speed_multiplier)

        # 2. Calculate Power Draw
        base_power = 40.0
        # Calculate RAM usage load (static overhead per tool)
        task_load = sum(t.power_cost for t in state.tasks if t.is_active)
        # Dynamic CPU utilization load: 2W per GHz utilized
        util_load = total_utilization_ghz * 2.0
        # Calculate Overclocking penalty (exponential draw above 1.0)
        oc_load = sum(((c.overclock - 1.0) ** 2) * 150 for c in gw.cpus)
        ram_oc_load = ((gw.ram_overclock - 1.0) ** 2) * 50

        gw.power_draw = base_power + task_load + util_load + oc_load + ram_oc_load

        # Check PSU capacity
        if gw.power_draw > gw.psu_capacity:
            log.warning(f"POWER TRIP! Draw ({gw.power_draw}W) exceeded capacity ({gw.psu_capacity}W). Shutting down tasks.")
            # Simple breaker trip: pause all tasks
            for t in state.tasks:
                t.is_active = False
            gw.power_draw = base_power

        # 3. Calculate Heat Generation
        # 10% of power draw is converted to heat
        heat_generated = gw.power_draw * 0.1
        # Cooling removes heat based on efficiency
        heat_removed = gw.coolant_efficiency * gw.cooling_power * 8.0

        # Heat delta
        gw.heat = max(25.0, gw.heat + (heat_generated - heat_removed) * 0.1)

        # 4. Component Degradation
        if gw.heat > gw.max_heat:
            gw.is_melted = True
            damage = (gw.heat - gw.max_heat) * 0.05
            for c in gw.cpus:
                c.health = max(0.0, c.health - damage)
            gw.ram_health = max(0.0, gw.ram_health - damage)
            gw.storage_health = max(0.0, gw.storage_health - damage)
        else:
            gw.is_melted = False

        # 5. Sync VFS block map
        HardwareEngine.rebuild_vfs_map(state)

        return progress_updates, completed_tasks

    @staticmethod
    def process_tasks(state: GameState, speed_multiplier: float = 1.0) -> tuple[list[dict], list[RunningTask], float]:
        """Progresses active tasks based on allocated CPU power. Returns (updates, completed, total_ghz)."""
        active_tasks = [t for t in state.tasks if t.is_active]
        if not active_tasks:
            return [], [], 0.0

        progress_updates = []
        completed_tasks = []
        total_utilization = 0.0

        total_priority = sum(t.cpu_cost_ghz for t in active_tasks)
        if total_priority <= 0:
            total_priority = 1.0

        for t in active_tasks:
            share_ghz = HardwareEngine.allocate_cpu_power(state, total_priority, t.cpu_cost_ghz, task=t)
            total_utilization += share_ghz

            # In our simulation, 10 GHz provides 1 tick of progress per game tick
            # We multiply by speed_multiplier (the game speed)
            effective_speed = (share_ghz / 10.0) * speed_multiplier

            # Use task_engine to handle logic/completion
            result = task_engine.tick_task(state, t, effective_speed)
            progress_updates.append(result["data"])
            if result["completed"]:
                completed_tasks.append(t)

        return progress_updates, completed_tasks, total_utilization

    @staticmethod
    def allocate_cpu_power(state: GameState, total_priority: float, task_priority: float, task: RunningTask = None) -> float:
        """
        Calculates the effective GHz a specific task receives based on its priority
        relative to all other active tasks, factoring in individual CPU health and overclocks.
        """
        gw = state.gateway

        # Calculate total available effective GHz
        total_ghz = 0.0
        for c in gw.cpus:
            # Degraded health linearly reduces effectiveness. Overclock multiplies base.
            health_factor = max(0.1, c.health / 100.0)
            effective_speed = c.base_speed * c.overclock * health_factor
            total_ghz += effective_speed

        if total_priority <= 0:
            return total_ghz

        # Task's share of the total processing power
        share = (task_priority / total_priority) * total_ghz

        # Global RAM overclock modifier acts as a final multiplier on effective data throughput
        final_speed = share * gw.ram_overclock

        # STORAGE IO OC: Apply to specific IO tasks
        if task:
            IO_TOOLS = {"File_Copier", "File_Deleter", "Decrypter", "Defrag", "Log_Deleter", "Log_Modifier"}
            if task.tool_name in IO_TOOLS:
                final_speed *= gw.storage_overclock

        return final_speed

    @staticmethod
    def set_cpu_overclock(state: GameState, cpu_id: int, multiplier: float) -> bool:
        """Sets the overclock multiplier (e.g. 1.0 to 2.0) for a specific CPU."""
        gw = state.gateway
        for c in gw.cpus:
            if c.id == cpu_id:
                c.overclock = max(0.5, min(3.0, multiplier))
                # Update effective speed
                c.speed = int(c.base_speed * c.overclock)
                return True
        return False

    @staticmethod
    def set_ram_overclock(state: GameState, multiplier: float):
        state.gateway.ram_overclock = max(0.5, min(3.0, multiplier))

    @staticmethod
    def set_storage_overclock(state: GameState, multiplier: float):
        state.gateway.storage_overclock = max(0.5, min(3.0, multiplier))

    @staticmethod
    def rebuild_vfs_map(state: GameState):
        """Updates the physical block map based on file allocations."""
        gw = state.gateway
        vfs = state.vfs

        gw.storage_used = sum(f.size_gq for f in vfs.files)

        # Mock fragmentation logic: more files = slightly higher fragmentation
        if gw.storage_capacity > 0:
            gw.fragmentation = min(1.0, (len(vfs.files) * 2) / gw.storage_capacity)

        # Ensure block assignments exist for files
        used_blocks = set()
        for f in vfs.files:
            if hasattr(f, 'blocks'):
                used_blocks.update(f.blocks)

        free_blocks = [i for i in range(gw.storage_capacity) if i not in used_blocks]

        for f in vfs.files:
            if hasattr(f, 'blocks') and not f.blocks and len(free_blocks) >= f.size_gq:
                f.blocks = free_blocks[:f.size_gq]
                free_blocks = free_blocks[f.size_gq:]
                used_blocks.update(f.blocks)
