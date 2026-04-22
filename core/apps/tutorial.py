"""Interactive Tutorial App."""

from core import constants as C
from core.apps import BaseApp


class TutorialApp(BaseApp):
    app_id = "tutorial"
    name = "Tutorial"
    category = "tools"
    icon = "T"
    window_size = (500, 400)
    exe_filename = "tutorial.exe"

    def init(self):
        return {
            "internic_ip": C.IP_INTERNIC
        }

    def expose_functions(self):
        return {
            "verify_step": self.verify_step
        }

    def verify_step(self, step_idx):
        s = self.state
        if step_idx == 1:  # Connect to InterNIC
            return s.connection.target_ip == C.IP_INTERNIC and s.connection.is_active
        if step_idx == 2:  # Browse Links
            return (s.connection.target_ip == C.IP_INTERNIC and
                    getattr(s.connection, "_current_screen", None) == C.SCREEN_LINKSSCREEN)
        if step_idx == 3:  # Bounce
            return len(s.bounce.hops) > 1
        if step_idx == 4:  # Start Cracking
            return any(t.tool_name == "Password_Breaker" for t in s.tasks if t.is_active)
        if step_idx == 5:  # Wipe Logs
            return any(t.tool_name == "Log_Deleter" for t in s.tasks if t.is_active)
        return True
