"""
Onlink-Clone: Hardware HUD

Functional gauges for Heat, Power, and CPU Load.
No steampunk polish — just clear, readable meters.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar, QGroupBox,
)
from PySide6.QtCore import Slot


class HardwareHUD(QWidget):
    """Simple hardware status panel with progress bars."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # --- Heat ---
        heat_group = QGroupBox("TEMPERATURE")
        heat_lay = QVBoxLayout(heat_group)
        self._heat_bar = QProgressBar()
        self._heat_bar.setRange(0, 100)
        self._heat_bar.setFormat("%v°")
        self._heat_bar.setStyleSheet(self._bar_style("#ff4444", "#441111"))
        self._heat_label = QLabel("0.0° — OK")
        heat_lay.addWidget(self._heat_bar)
        heat_lay.addWidget(self._heat_label)
        layout.addWidget(heat_group)

        # --- Power ---
        power_group = QGroupBox("POWER")
        power_lay = QVBoxLayout(power_group)
        self._power_bar = QProgressBar()
        self._power_bar.setRange(0, 100)
        self._power_bar.setFormat("%v%")
        self._power_bar.setStyleSheet(self._bar_style("#44aaff", "#112244"))
        self._power_label = QLabel("0W / 100W")
        power_lay.addWidget(self._power_bar)
        power_lay.addWidget(self._power_label)
        layout.addWidget(power_group)

        # --- CPU ---
        cpu_group = QGroupBox("CPU LOAD")
        cpu_lay = QVBoxLayout(cpu_group)
        self._cpu_bar = QProgressBar()
        self._cpu_bar.setRange(0, 100)
        self._cpu_bar.setFormat("%v%")
        self._cpu_bar.setStyleSheet(self._bar_style("#44ff88", "#114422"))
        self._cpu_label = QLabel("0 / 60 Ghz")
        cpu_lay.addWidget(self._cpu_bar)
        cpu_lay.addWidget(self._cpu_label)
        layout.addWidget(cpu_group)

        # --- Tasks ---
        tasks_group = QGroupBox("RUNNING TASKS")
        tasks_lay = QVBoxLayout(tasks_group)
        self._tasks_label = QLabel("No active tasks")
        self._tasks_label.setWordWrap(True)
        tasks_lay.addWidget(self._tasks_label)
        layout.addWidget(tasks_group)

        layout.addStretch()

    def refresh(self, state) -> None:
        """Force refresh from game state."""
        self.on_heat_changed(state.gateway.heat)
        self.on_power_changed(state.gateway.power_draw, state.gateway.psu_capacity)
        
        active_tasks = [t for t in state.tasks if t.is_active]
        cpu_load = sum(t.cpu_cost_ghz for t in active_tasks)
        self.update_cpu_load(cpu_load, state.gateway.cpu_speed)
        
        tasks = []
        for t in active_tasks:
            tasks.append({
                "tool_name": t.tool_name,
                "progress": t.progress,
                "cpu_cost": t.cpu_cost_ghz
            })
        self.on_task_progress(tasks)

    # ------------------------------------------------------------------
    # Slots (connected to engine signals)
    # ------------------------------------------------------------------
    @Slot(float)
    def on_heat_changed(self, heat: float) -> None:
        self._heat_bar.setValue(int(heat))
        if heat > 75:
            status = "⚠ CRITICAL"
            self._heat_bar.setStyleSheet(self._bar_style("#ff0000", "#440000"))
        elif heat > 50:
            status = "⚠ WARNING"
            self._heat_bar.setStyleSheet(self._bar_style("#ffaa00", "#442200"))
        else:
            status = "OK"
            self._heat_bar.setStyleSheet(self._bar_style("#ff4444", "#441111"))
        self._heat_label.setText(f"{heat:.1f}° — {status}")

    @Slot(float, float)
    def on_power_changed(self, draw: float, capacity: float) -> None:
        pct = int((draw / capacity) * 100) if capacity > 0 else 0
        self._power_bar.setValue(min(pct, 100))
        over = " ⚠ OVERLOAD" if draw > capacity else ""
        self._power_label.setText(f"{draw:.0f}W / {capacity:.0f}W{over}")

    @Slot(list)
    def on_task_progress(self, tasks: list) -> None:
        if not tasks:
            self._tasks_label.setText("No active tasks")
            return

        lines = []
        total_cpu = 0.0
        for t in tasks:
            pct = t["progress"] * 100
            lines.append(f"🔧 {t['tool_name']}: {pct:.0f}%")
            total_cpu += t.get("cpu_cost", 0)

        self._tasks_label.setText("\n".join(lines))

    def update_cpu_load(self, load_ghz: float, max_ghz: float) -> None:
        pct = int((load_ghz / max_ghz) * 100) if max_ghz > 0 else 0
        self._cpu_bar.setValue(min(pct, 100))
        self._cpu_label.setText(f"{load_ghz:.0f} / {max_ghz:.0f} Ghz")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _bar_style(fg: str, bg: str) -> str:
        return f"""
            QProgressBar {{
                border: 1px solid #333;
                border-radius: 3px;
                background: {bg};
                text-align: center;
                color: #ddd;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background: {fg};
                border-radius: 2px;
            }}
        """
