"""Logistics App - Track and hijack global shipments."""

from core.apps import BaseApp


class LogisticsApp(BaseApp):
    app_id = "logistics"
    name = "Logistics"
    category = "finance"
    icon = "L"
    window_size = (700, 500)
    exe_filename = "logistics.exe"

    def init(self):
        return {
            "manifests": [
                {
                    "id": m.id,
                    "origin": m.origin,
                    "destination": m.destination,
                    "cargo": m.cargo,
                    "value": m.value,
                    "carrier": m.carrier_company,
                    "vehicle_type": m.vehicle_type.name,
                    "status": m.status.name,
                    "progress": m.progress,
                    "vehicle_ip": m.vehicle_ip,
                    "security": m.security_level,
                }
                for m in self.state.world.manifests
                if m.status.name == "IN_TRANSIT"
            ]
        }
