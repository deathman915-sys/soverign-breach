"""
Onlink-Clone: Tool Overlay Widget

Floating per-task progress window, one per running hacking tool.
Matches the small draggable overlay windows from the original Uplink UI.

Each overlay shows:
- Tool name + version
- Progress bar
- Tool-specific UI (e.g., Password Breaker character cycling)
- Target IP
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QMdiSubWindow,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from core.game_state import RunningTask


class ToolOverlayWidget(QWidget):
    """Small floating widget for a single running task."""

    stop_requested = Signal(int)  # task_id

    def __init__(self, task: RunningTask, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._task_id = task.task_id
        self._tool_name = task.tool_name
        self.setMinimumWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Header: tool name + target
        header = QHBoxLayout()
        name_label = QLabel(f"{task.tool_name} v{task.tool_version}")
        name_label.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        header.addWidget(name_label)
        header.addStretch()

        stop_btn = QPushButton("✕")
        stop_btn.setFixedSize(18, 18)
        stop_btn.clicked.connect(lambda: self.stop_requested.emit(self._task_id))
        header.addWidget(stop_btn)
        layout.addLayout(header)

        # Target
        target_label = QLabel(f"→ {task.target_ip}")
        target_label.setFont(QFont("Consolas", 8))
        layout.addWidget(target_label)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setFixedHeight(16)
        self._progress_bar.setFormat("%v%")
        layout.addWidget(self._progress_bar)

        # Tool-specific display
        self._detail_label = QLabel("")
        self._detail_label.setFont(QFont("Consolas", 10))
        self._detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if task.tool_name == "Password_Breaker":
            self._detail_label.setText("Cracking: ______")
        elif task.tool_name == "Dictionary_Hacker":
            self._detail_label.setText("Searching dictionary...")
        elif task.tool_name == "Trace_Tracker":
            self._detail_label.setText("Monitoring trace...")
        elif task.tool_name in ("File_Copier", "File_Deleter"):
            self._detail_label.setText("Processing file...")
        elif task.tool_name in ("Log_Deleter", "Log_UnDeleter"):
            self._detail_label.setText("Modifying logs...")
        else:
            self._detail_label.setText("Running...")

        layout.addWidget(self._detail_label)

    @property
    def task_id(self) -> int:
        return self._task_id

    def update_progress(self, data: dict) -> None:
        """Update from a task progress dict."""
        progress = data.get("progress", 0)
        self._progress_bar.setValue(int(progress * 100))

        extra = data.get("extra", {})

        if self._tool_name == "Password_Breaker":
            revealed = extra.get("revealed", "")
            self._detail_label.setText(f"Cracking: {revealed}")

        elif self._tool_name == "Dictionary_Hacker":
            if extra.get("found"):
                self._detail_label.setText(f"Found: {extra.get('revealed', '')}")
            elif progress >= 1.0:
                self._detail_label.setText("Not found")

        elif self._tool_name == "Trace_Tracker":
            tp = extra.get("trace_progress", 0)
            active = extra.get("trace_active", False)
            if active:
                self._detail_label.setText(f"⚠ TRACE: {tp*100:.0f}%")
            else:
                self._detail_label.setText("No active trace")


def create_tool_overlay(task: RunningTask) -> tuple[QMdiSubWindow, ToolOverlayWidget]:
    """Factory: create a QMdiSubWindow containing a ToolOverlayWidget."""
    widget = ToolOverlayWidget(task)

    sub = QMdiSubWindow()
    sub.setWidget(widget)
    sub.setWindowTitle(f"🔧 {task.tool_name}")
    sub.resize(240, 120)
    sub.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

    return sub, widget
