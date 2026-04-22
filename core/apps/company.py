"""Company Manager App - Manage your player-owned corporation."""

from core.apps import BaseApp
from core.company_engine import get_player_company


class CompanyApp(BaseApp):
    app_id = "company"
    name = "Company Manager"
    category = "finance"
    icon = "C"
    window_size = (750, 550)
    exe_filename = "company.exe"

    def init(self):
        company = get_player_company(self.state)
        if not company:
            return {"owned": False}

        return {
            "owned": True,
            "name": company.name,
            "type": company.company_type.name,
            "stock_price": company.stock_price,
            "size": company.size,
            "balance": self.state.player.balance, # Using player balance as company treasury for now
            "vehicles": [
                {
                    "id": v.id,
                    "name": v.name,
                    "type": v.vehicle_type.name,
                    "status": v.status,
                    "ip": v.ip
                } for v in company.vehicles
            ],
            "manifests": [
                {
                    "id": m.id,
                    "origin": m.origin,
                    "destination": m.destination,
                    "cargo": m.cargo,
                    "value": m.value,
                    "status": m.status.name,
                    "progress": m.progress
                } for m in self.state.world.manifests if m.carrier_company == company.name
            ],
            "squads": [
                {
                    "id": s.id,
                    "name": s.name,
                    "combat": s.combat_rating,
                    "status": s.status.name,
                    "location": f"{s.location_x:.1f}, {s.location_y:.1f}"
                } for s in self.state.world.pmc_squads if s.owner_company == company.name
            ]
        }
