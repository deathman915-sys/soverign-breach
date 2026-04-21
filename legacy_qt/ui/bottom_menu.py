"""
Onlink-Clone: Bottom Menu Widget (Animated & Refined)

Replaces QMenu with persistent, animated sliding panels.
Single-action buttons trigger immediately (fixes Task 1).
Multi-action buttons (Software) show an animated category list (fixes Task 2).
Uses QPropertyAnimation for the slide effect (fixes Task 4).
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QToolButton, 
    QPushButton, QFrame
)
from PySide6.QtCore import Signal, QPropertyAnimation, QRect, QEasingCurve, QPoint
from PySide6.QtGui import QFont


class AnimatedMenuPanel(QFrame):
    """A sliding panel that matches the screenshot: blue gradient buttons, thin borders."""
    
    action_requested = Signal(str)

    def __init__(self, parent: QWidget, title: str, actions: list[tuple[str, str]]) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("background: transparent;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        
        # We build from bottom to top to match the slide-up feel
        for lbl, cmd in reversed(actions):
            btn = QPushButton(lbl)
            btn.setFont(QFont("Consolas", 9))
            btn.setFixedSize(120, 22)
            # Signature blue gradient and thin border from screenshot
            btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0000aa, stop:1 #000044);
                    color: white;
                    border: 1px solid #0000ff;
                    text-align: left;
                    padding-left: 5px;
                }
                QPushButton:hover {
                    background: #0000ff;
                }
            """)
            btn.clicked.connect(lambda checked=False, _cmd=cmd: self._on_clicked(_cmd))
            layout.addWidget(btn)

        self.adjustSize()
        self.hide()
        
        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.OutQuad)

    def _on_clicked(self, cmd: str) -> None:
        self.hide_panel()
        self.action_requested.emit(cmd)

    def toggle(self, pos: QPoint) -> None:
        if self.isVisible():
            self.hide_panel()
        else:
            self.show_panel(pos)

    def show_panel(self, pos: QPoint) -> None:
        w, h = self.width(), self.height()
        # Position exactly above the button
        target_rect = QRect(pos.x(), pos.y() - h - 2, w, h)
        start_rect = QRect(pos.x(), pos.y(), w, 0)
        
        self.setGeometry(start_rect)
        self.show()
        self.raise_()
        
        self._anim.setStartValue(start_rect)
        self._anim.setEndValue(target_rect)
        self._anim.start()

    def hide_panel(self) -> None:
        self.hide()


class BottomMenuWidget(QWidget):
    """The Uplink bottom-left menu layout matching the high-fidelity screenshot."""

    action_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 1. Big Radar Icon
        self._radar_btn = QToolButton()
        self._radar_btn.setFixedSize(68, 68)
        self._radar_btn.setText("ONLINK")
        self._radar_btn.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        self._radar_btn.setStyleSheet("""
            QToolButton {
                background-color: #000000;
                border: 1px solid #0000ff;
                color: #66ccff;
            }
            QToolButton:hover { border: 1px solid #ffffff; background-color: #000044; }
        """)
        
        self._radar_btn.clicked.connect(lambda: self.action_requested.emit("status"))
        layout.addWidget(self._radar_btn)

        # 2. Icon Grid
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(1)
        
        # Grid layout matching the screenshot exactly (icons only)
        # Using placeholder icons (text) for now
        menu_defs = [
            # Top Row (Indices into a sprite sheet in original)
            (0, 0, "Hardware", [("Hardware", "hardware")]),
            (0, 1, "News", [("News", "news")]),
            (0, 2, "Rankings", [("Rankings", "rankings")]),
            (0, 3, "World Map", [("World Map", "nodes")]),
            (0, 4, "Console", [("Console", "clear")]),
            (0, 5, "Disconnect", [("Disconnect", "disconnect")]),
            
            # Bottom Row
            (1, 0, "Status", [("Status", "status")]),
            (1, 1, "Software", [("File Utilities", "store_util"), ("Security", "store_sec"), ("Crackers", "store")]),
            (1, 2, "Missions", [("Missions", "missions")]),
            (1, 3, "Finance", [("Finance", "bank")]),
            (1, 4, "Messages", [("Messages", "messages")]),
            (1, 5, "Options", [("Options", "speed 0")])
        ]

        self._panels = {}

        for r, c, tooltip, actions in menu_defs:
            btn = QToolButton()
            btn.setFixedSize(33, 33)
            btn.setToolTip(tooltip)
            
            # Icon styling from screenshot
            btn.setStyleSheet("""
                QToolButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #000088, stop:1 #000022);
                    border: 1px solid #0000ff;
                    color: #aaaaff;
                    font-family: Consolas;
                    font-size: 8px;
                }
                QToolButton:hover {
                    border: 1px solid #ffffff;
                    background: #0000aa;
                }
            """)
            btn.setText(tooltip[:2].upper()) # Placeholder for icons

            if len(actions) == 1:
                cmd = actions[0][1]
                btn.clicked.connect(lambda checked=False, _cmd=cmd: self.action_requested.emit(_cmd))
            else:
                panel = AnimatedMenuPanel(self.window(), tooltip, actions)
                panel.action_requested.connect(self.action_requested.emit)
                self._panels[tooltip] = panel
                btn.clicked.connect(lambda checked=False, _btn=btn, _p=panel: self._toggle_panel(_btn, _p))
            
            grid.addWidget(btn, r, c)

        layout.addWidget(grid_widget)
        layout.addStretch(1)

    def _toggle_panel(self, btn: QToolButton, panel: AnimatedMenuPanel) -> None:
        # Close other panels first
        for p in self._panels.values():
            if p != panel: p.hide_panel()
        
        # Calculate global position
        gp = btn.mapTo(self.window(), QPoint(0, 0))
        panel.toggle(gp)
