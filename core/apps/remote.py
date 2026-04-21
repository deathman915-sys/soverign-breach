"""Remote App - Remote terminal for connecting to servers."""

from core.apps import BaseApp


class RemoteApp(BaseApp):
    app_id = "remote"
    name = "Remote"
    category = "network"
    icon = "R"
    window_size = (850, 600)
    exe_filename = None

    def init(self):
        return {"connected": False, "target_ip": None}
