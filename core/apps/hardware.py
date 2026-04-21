"""Hardware App - Gateway status and overclocking."""

from core.apps import BaseApp


class HardwareApp(BaseApp):
    app_id = "hardware"
    name = "Hardware"
    category = "system"
    icon = "H"
    window_size = (700, 500)
    exe_filename = None

    def init(self):
        gw = self.state.gateway
        from core.neuromancer import get_neuromancer_level
        from core.hardware_engine import HardwareEngine

        # Ensure VFS map is up to date
        HardwareEngine.rebuild_vfs_map(self.state)

        # Build vfs_map for high-fidelity grid
        vfs_map = [None] * gw.storage_capacity
        for f in self.state.vfs.files:
            if hasattr(f, "blocks"):
                for b_idx in f.blocks:
                    if 0 <= b_idx < len(vfs_map):
                        vfs_map[b_idx] = f.filename

        return {
            "name": gw.name,
            "cpus": [
                {
                    "id": c.id,
                    "model": c.model,
                    "speed": c.speed,
                    "health": c.health,
                    "overclock": c.overclock,
                }
                for c in gw.cpus
            ],
            "ram_used": gw.ram_used,
            "ram_slots": gw.ram_slots,
            "ram_health": gw.ram_health,
            "ram_overclock": gw.ram_overclock,
            "storage_capacity": gw.storage_capacity,
            "storage_used": gw.storage_used,
            "storage_health": gw.storage_health,
            "storage_overclock": gw.storage_overclock,
            "vfs_map": vfs_map,
            "cooling_power": gw.cooling_power,
            "psu_capacity": gw.psu_capacity,
            "power_draw": gw.power_draw,
            "heat": gw.heat,
            "max_heat": gw.max_heat,
            "is_melted": gw.is_melted,
            "has_self_destruct": gw.has_self_destruct,
            "has_motion_sensor": gw.has_motion_sensor,
            "vfs_files": [f.filename for f in self.state.vfs.files],
            "tasks": [
                {
                    "id": t.task_id,
                    "tool": t.tool_name,
                    "target": t.target_ip,
                    "progress": t.progress,
                }
                for t in self.state.tasks
            ],
            "neuromancer_rating": self.state.player.neuromancer_rating,
            "neuromancer_level": get_neuromancer_level(self.state),
            "overclock": {
                "cpus": [
                    {"id": c.id, "model": c.model, "overclock": c.overclock}
                    for c in gw.cpus
                ],
                "ram_overclock": gw.ram_overclock,
                "storage_overclock": gw.storage_overclock,
            },
        }
