"""
Onlink-Clone: Mission Widget

Displays available missions and allows the player to accept them.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QTextEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from core.game_state import GameState
from core.mission_engine import get_available_missions, accept_mission


class MissionWidget(QWidget):
    """Widget for viewing and accepting missions."""
    
    mission_accepted = Signal(int)

    def __init__(self, engine, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._engine = engine
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("UPLINK MISSION BBS")
        header.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        header.setStyleSheet("color: #66ccff;")
        layout.addWidget(header)

        # Split into list and details
        self._mission_list = QListWidget()
        self._mission_list.setFont(QFont("Consolas", 9))
        self._mission_list.setStyleSheet("""
            QListWidget { background: #000022; color: #aaaaff; border: 1px solid #000088; }
            QListWidget::item:selected { background: #0000aa; color: white; }
        """)
        self._mission_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._mission_list, 2)

        self._details = QTextEdit()
        self._details.setReadOnly(True)
        self._details.setFont(QFont("Consolas", 9))
        self._details.setStyleSheet("background: #000000; color: #ffffff; border: 1px solid #000088;")
        layout.addWidget(self._details, 3)

        self._accept_btn = QPushButton("ACCEPT MISSION")
        self._accept_btn.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        self._accept_btn.setStyleSheet("""
            QPushButton { background: #004400; color: #00ff00; border: 1px solid #00ff00; padding: 5px; }
            QPushButton:hover { background: #006600; }
            QPushButton:disabled { background: #222; color: #444; border: 1px solid #444; }
        """)
        self._accept_btn.clicked.connect(self._on_accept_clicked)
        self._accept_btn.setEnabled(False)
        layout.addWidget(self._accept_btn)

    def refresh(self, state: GameState) -> None:
        """Rebuild the mission list."""
        self._mission_list.clear()
        missions = get_available_missions(state)
        
        for m in missions:
            list_item = QListWidgetItem(f"[{m['payment']}c] - {m['employer']}")
            list_item.setData(Qt.ItemDataRole.UserRole, m)
            self._mission_list.addItem(list_item)
            
        self._details.clear()
        self._accept_btn.setEnabled(False)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        m = item.data(Qt.ItemDataRole.UserRole)
        if m:
            text = (
                f"EMPLOYER: {m['employer']}\n"
                f"PAYMENT:  {m['payment']} Credits\n"
                f"TARGET:   {m['target_ip']}\n"
                f"DIFFICULTY: {'*' * m['difficulty']}\n\n"
                f"DESCRIPTION:\n{m['description']}"
            )
            self._details.setText(text)
            self._accept_btn.setEnabled(True)

    def _on_accept_clicked(self) -> None:
        item = self._mission_list.currentItem()
        if not item: return
        
        m = item.data(Qt.ItemDataRole.UserRole)
        res = accept_mission(self._engine.state, m['id'])
        if res.get("success"):
            QMessageBox.information(self, "Mission Accepted", "The mission has been accepted. Check your email for details.")
            self.mission_accepted.emit(m['id'])
            self.refresh(self._engine.state)
        else:
            QMessageBox.warning(self, "Error", res.get("error", "Unknown error"))
