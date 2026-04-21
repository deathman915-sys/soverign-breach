"""
Onlink-Clone: News Widget

Displays procedural news from the game world.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.game_state import GameState
from core.news_engine import get_recent_news


class NewsWidget(QWidget):
    """Widget for viewing world news."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("UPLINK WORLD NEWS")
        header.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        header.setStyleSheet("color: #66ccff;")
        layout.addWidget(header)

        # Split into list and body
        self._news_list = QListWidget()
        self._news_list.setFont(QFont("Consolas", 9))
        self._news_list.setStyleSheet("""
            QListWidget { background: #000022; color: #aaaaff; border: 1px solid #000088; }
            QListWidget::item:selected { background: #0000aa; color: white; }
        """)
        self._news_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._news_list, 1)

        self._news_body = QTextEdit()
        self._news_body.setReadOnly(True)
        self._news_body.setFont(QFont("Consolas", 9))
        self._news_body.setStyleSheet("background: #000000; color: #ffffff; border: 1px solid #000088;")
        layout.addWidget(self._news_body, 2)

    def refresh(self, state: GameState) -> None:
        """Rebuild the news list."""
        self._news_list.clear()
        news_items = get_recent_news(state)
        
        for item in news_items:
            list_item = QListWidgetItem(item["headline"])
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self._news_list.addItem(list_item)
            
        if self._news_list.count() > 0:
            self._news_list.setCurrentRow(0)
            self._on_item_clicked(self._news_list.item(0))

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self._news_body.setText(data["body"])
