"""Memory Banks App - VFS file browser showing all files organized by type."""

from core.apps import BaseApp
from core.game_state import SoftwareType


class MemoryBanksApp(BaseApp):
    app_id = "memory_banks"
    name = "Memory Banks"
    category = "system"
    icon = "M"
    window_size = (650, 500)

    TYPE_LABELS = {
        SoftwareType.CRACKERS: "Crackers",
        SoftwareType.FILE_UTIL: "File Utilities",
        SoftwareType.LOG_TOOLS: "Log Tools",
        SoftwareType.BYPASSERS: "Bypassers",
        SoftwareType.HW_DRIVER: "Hardware Drivers",
        SoftwareType.LAN_TOOL: "LAN Tools",
        SoftwareType.LOG_NUKER: "Log Nukers",
        SoftwareType.VDPIN_DEFEATER: "VDPIN Defeaters",
        SoftwareType.HUD_UPGRADE: "HUD Upgrades",
        SoftwareType.OTHER: "Other",
        SoftwareType.NONE: "Data Files",
    }

    def init(self):
        files = []
        for i, f in enumerate(self.state.vfs.files):
            type_label = self.TYPE_LABELS.get(f.software_type, "Unknown")
            files.append({
                "id": f"vfs_{i}",
                "name": f.filename,
                "size": f.size_gq,
                "version": f.version,
                "type_label": type_label,
                "loaded": f.is_active,
            })
        return {"files": files}
