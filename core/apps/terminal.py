"""Terminal App - Command line interface."""

from core.apps import BaseApp


class TerminalApp(BaseApp):
    app_id = "terminal"
    name = "Terminal"
    category = "system"
    icon = "$"
    window_size = (700, 500)
    exe_filename = None

    def init(self):
        return {"prompt": f"{self.state.player.handle}@localhost:~$"}
