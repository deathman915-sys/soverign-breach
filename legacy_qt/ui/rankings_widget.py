"""
Onlink-Clone: Rankings Widget
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.game_state import GameState


class RankingsWidget(QWidget):
    """Widget for viewing agent rankings."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(300, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("UPLINK AGENT RANKINGS")
        header.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        header.setStyleSheet("color: #66ccff;")
        layout.addWidget(header)

        self._list = QListWidget()
        self._list.setFont(QFont("Consolas", 9))
        self._list.setStyleSheet("background: #000; color: #aaaaff;")
        layout.addWidget(self._list)

    def refresh(self, state: GameState) -> None:
        """Rebuild the rankings list."""
        self._list.clear()
        
        # In a real game we'd have a list of agents from npc_engine
        # For now, just show the player and some placeholder ranks
        ranks = [
            ("Agent 'Neo'", state.player.uplink_rating),
            ("Agent 'Morpheus'", 12),
            ("Agent 'Trinity'", 10),
            ("Agent 'Cipher'", 8),
            ("Agent 'Ghost'", 5),
            ("Agent 'Niobe'", 3),
        ]
        
        # Sort by rating
        ranks.sort(key=lambda x: x[1], reverse=True)
        
        rating_names = [
            "Registered", "Apprentice", "Novice", "Confident", "Intermediate", 
            "Skilled", "Experienced", "Knowledgeable", "Professional", "Elite", 
            "Mage", "Master", "Legendary", "Ultimate", "Godlike"
        ]

        for i, (name, rating) in enumerate(ranks):
            rat_name = rating_names[min(rating, len(rating_names)-1)]
            item = QListWidgetItem(f"{i+1}. {name:<15} | Rating: {rat_name} ({rating})")
            if "Neo" in name:
                item.setForeground(Qt.GlobalColor.cyan)
            self._list.addItem(item)
