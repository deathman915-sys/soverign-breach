"""
Onlink-Clone: Message Widget

Email / Messaging interface.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.game_state import GameState


class MessageWidget(QWidget):
    """Widget for reading emails."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(450, 350)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("UPLINK EMAIL CLIENT")
        header.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        header.setStyleSheet("color: #66ccff;")
        layout.addWidget(header)

        self._msg_list = QListWidget()
        self._msg_list.setFont(QFont("Consolas", 9))
        self._msg_list.setStyleSheet("""
            QListWidget { background: #000022; color: #aaaaff; border: 1px solid #000088; }
            QListWidget::item:selected { background: #0000aa; color: white; }
        """)
        self._msg_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._msg_list, 1)

        self._msg_body = QTextEdit()
        self._msg_body.setReadOnly(True)
        self._msg_body.setFont(QFont("Consolas", 9))
        self._msg_body.setStyleSheet("background: #000000; color: #ffffff; border: 1px solid #000088;")
        layout.addWidget(self._msg_body, 2)

    def refresh(self, state: GameState) -> None:
        """Rebuild the message list."""
        self._msg_list.clear()
        # Sorted by tick (newest first)
        msgs = sorted(state.messages, key=lambda m: m.created_at_tick, reverse=True)
        
        for m in msgs:
            list_item = QListWidgetItem(f"From: {m.from_name:<15} | {m.subject}")
            list_item.setData(Qt.ItemDataRole.UserRole, m)
            self._msg_list.addItem(list_item)
            
        if self._msg_list.count() > 0:
            self._msg_list.setCurrentRow(0)
            self._on_item_clicked(self._msg_list.item(0))

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        m = item.data(Qt.ItemDataRole.UserRole)
        if m:
            text = (
                f"FROM:    {m.from_name}\n"
                f"SUBJECT: {m.subject}\n"
                f"DATE:    Tick {m.created_at_tick}\n"
                f"----------------------------------------\n\n"
                f"{m.body}"
            )
            self._msg_body.setText(text)
