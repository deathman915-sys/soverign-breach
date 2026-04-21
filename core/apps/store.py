"""Store App - Software and hardware purchasing."""

from core.apps import BaseApp
from core.store_engine import (
    get_software_catalog,
    get_hardware_catalog,
    get_cooling_catalog,
    get_psu_catalog,
    get_addon_catalog,
)


class StoreApp(BaseApp):
    app_id = "store"
    name = "Upgrades"
    category = "system"
    icon = "U"
    window_size = (900, 650)
    exe_filename = None

    def init(self):
        return {
            "software": get_software_catalog(),
            "gateways": get_hardware_catalog(),
            "cooling": get_cooling_catalog(),
            "psu": get_psu_catalog(),
            "addons": get_addon_catalog(),
            "balance": self.state.player.balance,
        }
