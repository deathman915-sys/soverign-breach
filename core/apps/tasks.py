"""Tasks App - Task management, nuke gateway, overclocking."""

from core.apps import BaseApp


class TasksApp(BaseApp):
    app_id = "tasks"
    name = "Task Manager"
    category = "system"
    icon = "T"
    window_size = (600, 450)
    exe_filename = None

    def init(self):
        tasks = []
        for t in self.state.tasks:
            tasks.append(
                {
                    "id": t.task_id,
                    "tool": t.tool_name,
                    "target": t.target_ip,
                    "progress": t.progress,
                    "active": t.is_active,
                }
            )
        return {
            "tasks": tasks,
            "has_self_destruct": self.state.gateway.has_self_destruct,
            "overclock": {
                "cpus": [
                    {
                        "id": c.id,
                        "model": c.model,
                        "overclock": c.overclock,
                        "health": c.health,
                    }
                    for c in self.state.gateway.cpus
                ],
                "ram_overclock": self.state.gateway.ram_overclock,
            },
        }

    def expose_functions(self):
        return {
            "stop_task": self._stop_task,
            "nuke_gateway": self._nuke_gateway,
            "set_cpu_overclock": self._set_cpu_overclock,
            "set_ram_overclock": self._set_ram_overclock,
        }

    def _stop_task(self, task_id: int):
        from core.task_engine import stop_task

        return stop_task(self.state, task_id)

    def _nuke_gateway(self):
        from core.gateway_nuke import nuke_gateway

        return nuke_gateway(self.state)

    def _set_cpu_overclock(self, cpu_id: int, multiplier: float):
        from core.hardware_engine import HardwareEngine

        return HardwareEngine.set_cpu_overclock(self.state, cpu_id, multiplier)

    def _set_ram_overclock(self, multiplier: float):
        from core.hardware_engine import HardwareEngine

        return HardwareEngine.set_ram_overclock(self.state, multiplier)
