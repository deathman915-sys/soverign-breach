"""News App - News server."""

from core.apps import BaseApp
from core.news_engine import get_recent_news, add_news


class NewsApp(BaseApp):
    app_id = "news"
    name = "News"
    category = "system"
    icon = "N"
    window_size = (500, 700)
    exe_filename = "news.exe"

    def init(self):
        # Generate initial news if none exists
        if not self.state.world.news:
            add_news(self.state, "company_hack", company_name="TechCorp")
            add_news(self.state, "stock_crash", company_name="DataSoft", percent="23")
            add_news(self.state, "system_failure", system_name="Federal Database")

        news = get_recent_news(self.state)
        d, m, y = self.state.clock.game_date
        for n in news:
            n["date"] = f"{d:02d}/{m:02d}/{y}"
        return {"news": news}
