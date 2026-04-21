"""
Onlink-Clone: HUD Widgets (Screenshot Accurate Overlay)

Floating HUD components positioned manually in the MainWindow.
- Top-Left: Date/Time, IPs, Connection Close, Speed Control. 
  (Uses specific blue rectangles with a matching font block)
- Top-Center: Minimalist CPU Progress Bar + label.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar,
    QPushButton
)
from PySide6.QtCore import Signal


class HudBarLeft(QWidget):
    """The Top-Left blue strip with Connection info, Time, and Speed."""
    action_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Style all children to match the blue boxes in the screenshot
        self.setStyleSheet("""
            QLabel {
                background-color: #000088;
                color: #FFFFFF;
                border: 1px solid #0000FF;
                padding: 2px 10px;
                font-family: Consolas;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #000088;
                color: #FFFFFF;
                border: 1px solid #0000FF;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0000FF; }
            QPushButton:pressed { background-color: #000044; }
        """)
        
        # Close connection button (icon X)
        btn_close = QPushButton("X")
        btn_close.setFixedSize(20, 20)
        btn_close.clicked.connect(lambda: self.action_requested.emit("disconnect"))
        layout.addWidget(btn_close)
        
        # Clock
        self._clock_label = QLabel("00:00:00, 24 March 2010")
        layout.addWidget(self._clock_label)
        
        # IP Box
        self._ip_label = QLabel("127.0.0.1")
        layout.addWidget(self._ip_label)
        
        # Speed controls
        btn_pause = QPushButton("||")
        btn_play = QPushButton(">")
        btn_ff = QPushButton(">>")
        for b in [btn_pause, btn_play, btn_ff]:
            b.setFixedSize(20, 20)
            layout.addWidget(b)
            
        btn_pause.clicked.connect(lambda: self.action_requested.emit("speed 0"))
        btn_play.clicked.connect(lambda: self.action_requested.emit("speed 1"))
        btn_ff.clicked.connect(lambda: self.action_requested.emit("speed 5"))

    def update_clock(self, tick: int, date_tuple: tuple) -> None:
        day, month, year = date_tuple
        game_minutes = tick % 1440
        hours = game_minutes // 60
        mins = game_minutes % 60
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        month_str = months[month - 1] if 1 <= month <= 12 else "???"
        self._clock_label.setText(f"{hours:02d}:{mins:02d}:00, {day} {month_str} {year}")

    def update_connection(self, chain: list[str]) -> None:
        if not chain or chain == ["Localhost"]:
            self._ip_label.setText("127.0.0.1")
        else:
            self._ip_label.setText(chain[-1])


class HudBarCPU(QWidget):
    """The Top-Center CPU tracking section."""
    cpu_allocation_changed = Signal(int, float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Texts
        lbl_head = QLabel("CPU usage")
        lbl_head.setStyleSheet("color: #FFFFFF; font-family: Consolas; font-size: 11px;")
        
        lbl_scale = QLabel("0...........50...........100")
        lbl_scale.setStyleSheet("color: #FFFFFF; font-family: Consolas; font-size: 10px;")
        
        # Bar
        self._cpu_master = QProgressBar()
        self._cpu_master.setRange(0, 100)
        self._cpu_master.setFixedHeight(8)
        self._cpu_master.setTextVisible(False)
        self._cpu_master.setStyleSheet("""
            QProgressBar { border: 1px solid #0000AA; background: black; }
            QProgressBar::chunk { background: #0000FF; }
        """)
        
        layout.addWidget(lbl_head)
        layout.addWidget(lbl_scale)
        layout.addWidget(self._cpu_master)

        self._cpu_rows_layout = QVBoxLayout()
        self._cpu_rows_layout.setSpacing(1)
        layout.addLayout(self._cpu_rows_layout)
        self._cpu_row_widgets: dict[int, dict] = {}

    def update_cpu(self, tasks: list[dict], max_cpu: float) -> None:
        total_load = sum(t.get("cpu_cost", 0) for t in tasks) if tasks else 0
        pct = int((total_load / max_cpu) * 100) if max_cpu > 0 else 0
        self._cpu_master.setValue(min(pct, 100))

        active_ids = set()
        for t in (tasks or []):
            tid = t.get("task_id", 0)
            active_ids.add(tid)
            tool_name = t.get("tool_name", "?")

            if tid not in self._cpu_row_widgets:
                row = QHBoxLayout()
                row.setSpacing(2)

                btn_left = QPushButton("<")
                btn_left.setFixedSize(14, 12)
                btn_left.clicked.connect(lambda checked, _tid=tid: self._adjust_cpu(_tid, -10))
                
                # Custom tiny buttons style
                tiny_style = "QPushButton { background: #000088; color: white; border: 1px solid #0000ff; } QPushButton:hover { background: #0000ff; }"
                btn_left.setStyleSheet(tiny_style)

                lbl = QLabel(tool_name)
                lbl.setStyleSheet("color: #FFFFFF; font-family: Consolas; font-size: 9px;")
                
                bar = QProgressBar()
                bar.setRange(0, 100)
                bar.setFixedHeight(6)
                bar.setTextVisible(False)
                bar.setStyleSheet("QProgressBar { border: 1px solid #0000aa; background: black; } QProgressBar::chunk { background: #0000aa; }")

                btn_right = QPushButton(">")
                btn_right.setFixedSize(14, 12)
                btn_right.setStyleSheet(tiny_style)
                btn_right.clicked.connect(lambda checked, _tid=tid: self._adjust_cpu(_tid, 10))

                btn_x = QPushButton("x")
                btn_x.setFixedSize(14, 12)
                btn_x.setStyleSheet("QPushButton { background: #880000; color: white; border: 1px solid #ff0000; }")

                row.addWidget(btn_left)
                row.addWidget(lbl)
                row.addWidget(bar)
                row.addWidget(btn_right)
                row.addWidget(btn_x)

                self._cpu_rows_layout.addLayout(row)
                self._cpu_row_widgets[tid] = {"layout": row, "bar": bar, "pct": 100, "lbl": lbl, "bl": btn_left, "br": btn_right, "bx": btn_x}

            entry = self._cpu_row_widgets[tid]
            progress = int(t.get("progress", 0) * 100)
            entry["bar"].setValue(progress)

        for tid in list(self._cpu_row_widgets.keys()):
            if tid not in active_ids:
                entry = self._cpu_row_widgets.pop(tid)
                layout = entry["layout"]
                for key in ["bar", "lbl", "bl", "br", "bx"]:
                    if key in entry and entry[key]:
                        entry[key].deleteLater()
                self._cpu_rows_layout.removeItem(layout)

    def _adjust_cpu(self, task_id: int, delta: int) -> None:
        if task_id in self._cpu_row_widgets:
            entry = self._cpu_row_widgets[task_id]
            entry["pct"] = max(10, min(100, entry["pct"] + delta))
            self.cpu_allocation_changed.emit(task_id, entry["pct"] / 100.0)
