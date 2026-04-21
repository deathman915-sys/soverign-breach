"""Missions App - Mission BBS."""

from core.apps import BaseApp
from core.mission_engine import get_available_missions, get_active_missions


class MissionsApp(BaseApp):
    app_id = "missions"
    name = "Missions"
    category = "network"
    icon = "M"
    window_size = (600, 600)
    exe_filename = "missions.exe"

    def init(self):
        return {
            "available": get_available_missions(self.state),
            "active": get_active_missions(self.state),
        }
