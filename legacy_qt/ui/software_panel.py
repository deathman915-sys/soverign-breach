"""
Onlink-Clone: Software Panel

List of available software tools from the player's VFS.
Click a tool to activate it (emits tool_activated signal).

Matches the right-side panel from the Uplink UI.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from core.game_state import GameState, SoftwareType


# Tool categories for display
TOOL_CATEGORIES = {
    SoftwareType.CRACKERS: "Crackers",
    SoftwareType.BYPASSERS: "Bypassers",
    SoftwareType.FILE_UTIL: "File Utils",
    SoftwareType.LOG_TOOLS: "Log Tools",
    SoftwareType.LOG_NUKER: "Log Nuker",
    SoftwareType.VDPIN_DEFEATER: "VDPIN Defeater",
    SoftwareType.HUD_UPGRADE: "HUD Upgrades",
    SoftwareType.LAN_TOOL: "LAN Tools",
    SoftwareType.OTHER: "Other",
}


class SoftwarePanel(QWidget):
    """Panel listing the player's installed software tools with Uplink/Onlink aesthetics."""

    tool_activated = Signal(str, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(280)
        self._current_filter: SoftwareType | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)

        # Header Section
        self._title_lbl = QLabel("MEMORY BANKS")
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_lbl.setStyleSheet("""
            background: #000066; color: white; border: 1px solid #0000ff;
            font-family: Consolas; font-size: 11px; font-weight: bold; padding: 2px;
        """)
        layout.addWidget(self._title_lbl)

        self._capacity_lbl = QLabel("Memory Capacity : 24 GigaQuads")
        self._capacity_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._capacity_lbl.setStyleSheet("color: #66ccff; font-family: Consolas; font-size: 10px; padding: 5px;")
        layout.addWidget(self._capacity_lbl)

        self._tool_list = QListWidget()
        self._tool_list.setFont(QFont("Consolas", 10))
        self._tool_list.setStyleSheet("""
            QListWidget { 
                background: #000000; color: #ffffff; border: 1px solid #000088; 
                outline: none;
            }
            QListWidget::item { height: 18px; border: none; }
            QListWidget::item:selected { background: #000066; color: white; }
        """)
        self._tool_list.itemDoubleClicked.connect(self._on_activate)
        layout.addWidget(self._tool_list)

    def set_filter(self, sw_type: SoftwareType | None) -> None:
        self._current_filter = sw_type
        if sw_type and sw_type in TOOL_CATEGORIES:
            self._title_lbl.setText(f"MEM: {TOOL_CATEGORIES[sw_type].upper()}")
        else:
            self._title_lbl.setText("MEMORY BANKS")

    def refresh(self, state: GameState) -> None:
        self._tool_list.clear()
        self._capacity_lbl.setText(f"Memory Capacity : {state.gateway.memory_size} GigaQuads")

        # Map software types to the colors seen in screenshot
        # Red/Purple for crackers, Green for data/misc, Gold for special
        type_colors = {
            SoftwareType.CRACKERS: "#aa2222",
            SoftwareType.LOG_TOOLS: "#882288",
            SoftwareType.FILE_UTIL: "#882244",
            SoftwareType.LOG_NUKER: "#ff0000",
            SoftwareType.VDPIN_DEFEATER: "#ddaa00",
            SoftwareType.BYPASSERS: "#2222aa",
            SoftwareType.OTHER: "#22aa44"
        }

        # Create 24 slots (0x000 to 0x017)
        for i in range(24):
            addr = f"0x{i:03X}"
            item = QListWidgetItem()
            
            # Find file for this slot if any (simulated slotting)
            f = state.vfs.files[i] if i < len(state.vfs.files) else None
            
            if f:
                display_text = f"{addr} {f.filename:<20} v{f.version}.0"
                item.setText(display_text)
                color = type_colors.get(f.software_type, "#0000aa")
                item.setBackground(Qt.GlobalColor.black) # Default
                item.setForeground(Qt.GlobalColor.white)
                
                # To simulate the "block" look, we set the background color
                item.setBackground(color)
                item.setData(Qt.ItemDataRole.UserRole, (f.filename, f.version))
            else:
                item.setText(addr)
                item.setForeground(Qt.GlobalColor.white)
                
            self._tool_list.addItem(item)

    def _on_activate(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            name, version = data
            # Extract base tool name (remove " vX.X" suffix)
            base_name = name.split(" v")[0] if " v" in name else name
            # Convert spaces to underscores for engine tool names
            tool_name = base_name.replace(" ", "_")
            self.tool_activated.emit(tool_name, version)
