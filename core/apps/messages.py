"""Messages App - Email/inbox system."""

from core.apps import BaseApp


class MessagesApp(BaseApp):
    app_id = "messages"
    name = "Messages"
    category = "system"
    icon = "@"
    window_size = (550, 500)
    exe_filename = None

    def init(self):
        return {
            "messages": [
                {
                    "id": m.id,
                    "from": m.from_name,
                    "subject": m.subject,
                    "body": m.body,
                    "is_read": m.is_read,
                    "created_at_tick": m.created_at_tick,
                }
                for m in self.state.messages
            ],
            "unread": len([m for m in self.state.messages if not m.is_read]),
        }
