"""Rankings App - Agent leaderboard."""

from core.apps import BaseApp
from core.npc_engine import get_rankings


class RankingsApp(BaseApp):
    app_id = "rankings"
    name = "Rankings"
    category = "system"
    icon = "#"
    window_size = (450, 500)
    exe_filename = "rankings.exe"

    def init(self):
        return {"rankings": get_rankings(self.state)}
