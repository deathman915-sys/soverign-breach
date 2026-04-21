"""Map App - World map with node markers."""

from core.apps import BaseApp


class MapApp(BaseApp):
    app_id = "map"
    name = "World Map"
    category = "network"
    icon = "W"
    window_size = (850, 600)
    exe_filename = "map.exe"

    def init(self):
        nodes = []
        for ip, comp in self.state.computers.items():
            if comp.listed or ip in self.state.player.known_ips:
                nodes.append(
                    {
                        "ip": ip,
                        "name": comp.name,
                        "type": comp.computer_type,
                        "x": comp.x,
                        "y": comp.y,
                        "listed": comp.listed,
                    }
                )
        return {"nodes": nodes, "known_ips": self.state.player.known_ips}
