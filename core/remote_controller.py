"""
Onlink-Clone: Remote Interface Controller (API Layer)

Bridges the high-fidelity UI to the core simulation engines.
Implements the API/Controller pattern for remote server interactions.
Generates HTML from the backend so the frontend is a thin renderer.
"""

from __future__ import annotations
import json
import logging
from html import escape
from core.game_state import GameState, NodeType, SoftwareType
from core import task_engine, trace_engine, constants as C

log = logging.getLogger(__name__)


class ScreenHTMLBuilder:
    """Generates HTML for server screens. Keeps UI logic in Python."""

    @staticmethod
    def build_menu_html(title: str, options: list[dict]) -> str:
        items = "".join(
            f'<button class="menu-btn" style="text-align:left;" onclick="remoteNavigate({opt["screen_type"]})">{escape(opt["name"])}</button>'
            for opt in options
        )
        return (
            f'<div style="padding:20px;">'
            f'<div style="color:var(--cyan); font-weight:bold; margin-bottom:15px; font-size:14px;">{escape(title)}</div>'
            f'<div style="display:flex; flex-direction:column; gap:5px;">{items}</div>'
            f'</div>'
        )

    @staticmethod
    def build_password_html(title: str, hint: str) -> str:
        return (
            f'<div style="padding:40px; text-align:center;">'
            f'<div style="color:var(--red); font-weight:bold;">PASSWORD REQUIRED</div>'
            f'<div style="color:#444; font-size:9px; margin-top:10px;">{escape(hint) if hint else ""}</div>'
            f'</div>'
        )

    @staticmethod
    def build_file_server_html(files: list[dict]) -> str:
        if not files:
            return (
                '<div style="padding:15px; overflow-y:auto; height:100%;">'
                '<div style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">FILE SERVER</div>'
                '<div style="color:#333; text-align:center;">No files</div></div>'
            )
        items = "".join(
            f'<div style="border:1px solid #222; padding:8px; margin-bottom:4px; '
            f'display:flex; justify-content:space-between; align-items:center;">'
            f'<div><span style="color:#fff;">{escape(f["name"])}</span> '
            f'<span style="color:#444; font-size:9px;">({f["size"]}GQ)</span></div>'
            f'<div style="display:flex; gap:4px;">'
            f'<button class="menu-btn" style="font-size:9px;" '
            f'onclick="serverCopyFile(\'{escape(f["name"])}\')">COPY</button>'
            f'<button class="menu-btn" style="font-size:9px; background:#300; '
            f'color:#a55;" onclick="serverDeleteFile(\'{escape(f["name"])}\')">DEL</button>'
            f'</div></div>'
            for f in files
        )
        return (
            f'<div style="padding:15px; overflow-y:auto; height:100%;">'
            f'<div style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">FILE SERVER</div>'
            f'{items}</div>'
        )

    @staticmethod
    def build_logs_html(logs: list[dict]) -> str:
        if not logs:
            return (
                '<div style="padding:15px;">'
                '<div style="color:var(--yellow); font-weight:bold; margin-bottom:10px;">LOGS</div>'
                '<div style="color:#333; text-align:center;">Empty</div></div>'
            )
        items = "".join(
            f'<div style="display:flex; justify-content:space-between; align-items:center; '
            f'font-family:monospace; font-size:9px; border-bottom:1px solid #111; padding:4px 0;">'
            f'<span style="color:var(--red);">{escape(log_entry["subject"])}'
            f'{"" if not log_entry.get("modified") else " <span style=\\\"color:var(--orange); font-size:8px;\\\">[MODIFIED]</span>"}'
            f'</span>'
            f'<span style="color:var(--cyan); cursor:pointer;" '
            f'onclick="interactWithIP(\'{escape(log_entry["from"])}\')">{escape(log_entry["from"])}</span>'
            f'<span style="color:#666;">{escape(log_entry["time"])}</span>'
            f'<button class="menu-btn" style="font-size:7px; padding:1px 4px;" '
            f'onclick="modifyLogPrompt({log_entry["index"]})">MODIFY</button>'
            f'</div>'
            for log_entry in logs
        )
        # Serialize logs for JS access
        logs_json = json.dumps(logs)
        return (
            f'<div style="padding:15px;">'
            f'<div style="color:var(--yellow); font-weight:bold; margin-bottom:10px;">LOGS</div>'
            f'{items}</div>'
            f'<script>window._logData = {logs_json};</script>'
        )

    @staticmethod
    def build_bbs_html(missions: list[dict]) -> str:
        if not missions:
            return (
                '<div style="padding:15px; overflow-y:auto; height:100%;">'
                '<div style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">MISSION BBS</div>'
                '<div style="color:#333; text-align:center;">No missions available</div></div>'
            )
        items = "".join(
            f'<div style="border:1px solid #222; padding:10px; margin-bottom:5px; '
            f'display:flex; justify-content:space-between; align-items:center;">'
            f'<div><div style="color:#fff;">{escape(m.get("employer", m.get("type", "")))}: '
            f'{escape(m.get("description", ""))}</div>'
            f'<div style="color:var(--green); font-size:9px;">Payment: {m.get("payment", "?")}c</div></div>'
            f'<div style="display:flex; gap:4px;">'
            f'<button class="menu-btn" style="font-size:9px;" '
            f'onclick="serverAcceptMission({m["id"]})">ACCEPT</button>'
            f'<button class="menu-btn" style="font-size:9px; background:#222;" '
            f'onclick="serverNegotiateMission({m["id"]})">NEGOTIATE</button>'
            f'</div></div>'
            for m in missions
        )
        return (
            f'<div style="padding:15px; overflow-y:auto; height:100%;">'
            f'<div style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">MISSION BBS</div>'
            f'{items}</div>'
        )

    @staticmethod
    def build_links_html(links: list[str | dict]) -> str:
        if not links:
            return (
                '<div style="padding:15px;">'
                '<div style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">LINKS</div>'
                '<div style="color:#333; text-align:center;">Empty</div></div>'
            )
        items = ""
        for link in links:
            ip = link if isinstance(link, str) else link.get("ip", link.get("name", ""))
            items += (
                f'<div style="color:var(--cyan); cursor:pointer;" '
                f'onclick="interactWithIP(\'{escape(ip)}\')">{escape(ip)}</div>'
            )
        return (
            f'<div style="padding:15px;">'
            f'<div style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">LINKS</div>'
            f'{items}</div>'
        )

    @staticmethod
    def build_console_html(cwd: str) -> str:
        return f'<div style="padding:15px; background:#000; height:100%; font-family:monospace; color:var(--green);">{escape(cwd or "~")}</div>'

    @staticmethod
    def build_software_sales_html(items: list[dict]) -> str:
        if not items:
            return (
                '<div style="padding:15px; overflow-y:auto; height:100%;">'
                '<div style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">SOFTWARE UPGRADES</div>'
                '<div style="color:#333; text-align:center;">No software available</div></div>'
            )
        cards = "".join(
            f'<div style="border:1px solid #222; padding:8px; margin-bottom:4px; '
            f'display:flex; justify-content:space-between; align-items:center;">'
            f'<div><div style="color:#fff; font-size:10px;">{escape(item["name"])} v{item.get("version", 1)}</div>'
            f'<div style="color:#444; font-size:9px;">Size: {item.get("size", "?")}GQ</div></div>'
            f'<div style="display:flex; gap:6px; align-items:center;">'
            f'<span style="color:var(--green); font-size:10px;">{item["price"]}c</span>'
            f'<button class="menu-btn" style="font-size:9px;" '
            f'onclick="serverBuySoftware(\'{escape(item["name"])}\',{item.get("version", 1)})">BUY</button>'
            f'</div></div>'
            for item in items
        )
        return (
            f'<div style="padding:15px; overflow-y:auto; height:100%;">'
            f'<div style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">SOFTWARE UPGRADES</div>'
            f'{cards}</div>'
        )

    @staticmethod
    def build_hardware_sales_html(gateways: list[dict], cooling: list[dict], psu: list[dict], addons: list[dict]) -> str:
        sections = []

        if gateways:
            items = "".join(
                f'<div style="border:1px solid #222; padding:8px; margin-bottom:4px; '
                f'display:flex; justify-content:space-between; align-items:center;">'
                f'<div style="color:#fff; font-size:10px;">{escape(g["name"])}</div>'
                f'<div style="display:flex; gap:6px; align-items:center;">'
                f'<span style="color:var(--green); font-size:10px;">{g["price"]}c</span>'
                f'<button class="menu-btn" style="font-size:9px;" '
                f'onclick="serverBuyGateway(\'{escape(g["name"])}\')">BUY</button>'
                f'</div></div>'
                for g in gateways
            )
            sections.append(f'<div style="color:var(--yellow); font-size:10px; margin-bottom:8px;">GATEWAYS</div>{items}')

        if cooling:
            items = "".join(
                f'<div style="border:1px solid #222; padding:8px; margin-bottom:4px; '
                f'display:flex; justify-content:space-between; align-items:center;">'
                f'<div style="color:#fff; font-size:10px;">{escape(c["name"])}</div>'
                f'<div style="display:flex; gap:6px; align-items:center;">'
                f'<span style="color:var(--green); font-size:10px;">{c["price"]}c</span>'
                f'<button class="menu-btn" style="font-size:9px;" '
                f'onclick="serverBuyCooling(\'{escape(c["name"])}\')">BUY</button>'
                f'</div></div>'
                for c in cooling
            )
            sections.append(f'<div style="color:var(--yellow); font-size:10px; margin:12px 0 8px;">COOLING SYSTEMS</div>{items}')

        if psu:
            items = "".join(
                f'<div style="border:1px solid #222; padding:8px; margin-bottom:4px; '
                f'display:flex; justify-content:space-between; align-items:center;">'
                f'<div style="color:#fff; font-size:10px;">{escape(p["name"])}</div>'
                f'<div style="display:flex; gap:6px; align-items:center;">'
                f'<span style="color:var(--green); font-size:10px;">{p["price"]}c</span>'
                f'<button class="menu-btn" style="font-size:9px;" '
                f'onclick="serverBuyPSU(\'{escape(p["name"])}\')">BUY</button>'
                f'</div></div>'
                for p in psu
            )
            sections.append(f'<div style="color:var(--yellow); font-size:10px; margin:12px 0 8px;">POWER SUPPLIES</div>{items}')

        if addons:
            items = "".join(
                f'<div style="border:1px solid #222; padding:8px; margin-bottom:4px; '
                f'display:flex; justify-content:space-between; align-items:center;">'
                f'<div style="color:#fff; font-size:10px;">{escape(a["name"])}</div>'
                f'<div style="display:flex; gap:6px; align-items:center;">'
                f'<span style="color:var(--green); font-size:10px;">{a["price"]}c</span>'
                f'<button class="menu-btn" style="font-size:9px;" '
                f'onclick="serverBuyAddon(\'{escape(a["name"])}\')">BUY</button>'
                f'</div></div>'
                for a in addons
            )
            sections.append(f'<div style="color:var(--yellow); font-size:10px; margin:12px 0 8px;">ADDONS</div>{items}')

        if not sections:
            return (
                '<div style="padding:15px; overflow-y:auto; height:100%;">'
                '<div style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">HARDWARE UPGRADES</div>'
                '<div style="color:#333; text-align:center;">No hardware available</div></div>'
            )

        return (
            f'<div style="padding:15px; overflow-y:auto; height:100%;">'
            f'<div style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">HARDWARE UPGRADES</div>'
            f'{"".join(sections)}</div>'
        )

    @staticmethod
    def build_news_html(articles: list[dict]) -> str:
        if not articles:
            return (
                '<div style="padding:15px; overflow-y:auto; height:100%;">'
                '<div style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">NEWS FEED</div>'
                '<div style="color:#333; text-align:center;">No news articles</div></div>'
            )
        items = "".join(
            f'<div style="border:1px solid #222; padding:10px; margin-bottom:8px;">'
            f'<div style="color:#fff; font-size:11px; margin-bottom:4px;">{escape(a["headline"])}</div>'
            f'<div style="color:#444; font-size:9px; margin-bottom:6px;">Category: '
            f'{escape(a.get("category", "General"))} | Tick: {a.get("tick", "?")}</div>'
            f'<div style="color:#888; font-size:10px; line-height:1.4;">'
            f'{escape(a.get("body", ""))}</div>'
            f'</div>'
            for a in articles
        )
        return (
            f'<div style="padding:15px; overflow-y:auto; height:100%;">'
            f'<div style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">NEWS FEED</div>'
            f'{items}</div>'
        )

    @staticmethod
    def build_rankings_html(rankings: list[dict]) -> str:
        if not rankings:
            return (
                '<div style="padding:15px; overflow-y:auto; height:100%;">'
                '<div style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">RANKINGS</div>'
                '<div style="color:#333; text-align:center;">No rankings available</div></div>'
            )
        items = "".join(
            f'<div style="border:1px solid #222; padding:8px; display:flex; '
            f'justify-content:space-between; align-items:center;">'
            f'<div style="display:flex; align-items:center; gap:10px;">'
            f'<span style="color:var(--yellow); font-weight:bold; min-width:30px;">#{i+1}</span>'
            f'<span style="color:#fff;">{escape(r.get("name", r.get("handle", "?")))}</span>'
            f'</div>'
            f'<div style="color:var(--green); font-size:10px;">Rating: {r.get("rating", 0)}</div>'
            f'</div>'
            for i, r in enumerate(rankings)
        )
        return (
            f'<div style="padding:15px; overflow-y:auto; height:100%;">'
            f'<div style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">RANKINGS</div>'
            f'<div style="display:flex; flex-direction:column; gap:4px;">{items}</div></div>'
        )

    @staticmethod
    def build_company_info_html(data: dict) -> str:
        vehicles = data.get("vehicles", [])
        return (
            f'<div style="padding:15px; height:100%; display:flex; flex-direction:column;">'
            f'<div style="color:var(--cyan); font-weight:bold; font-size:14px; margin-bottom:5px;">'
            f'{escape(data.get("title", data.get("name", "COMPANY INFO")))}</div>'
            f'<div style="font-size:9px; color:#666; margin-bottom:15px;">TYPE: '
            f'{escape(data.get("company_type", "Unknown"))} | STOCK: {data.get("stock_price", "N/A")}</div>'
            f'<div style="border-top:1px solid #111; padding-top:10px; flex:1;">'
            f'{f"<div style=\\\"color:#888; font-size:10px; margin-bottom:8px;\\\">Owner: {escape(data.get("owner", ""))}</div>" if data.get("owner") else ""}'
            f'{f"<div style=\\\"color:#888; font-size:10px; margin-bottom:8px;\\\">Size: {data.get("size", 0)} employees</div>" if data.get("size") else ""}'
            f'{f"<div style=\\\"color:var(--green); font-size:10px;\\\">Fleet: {len(vehicles)} active vehicles</div>" if vehicles else "<div style=\\\"color:#444; font-size:9px;\\\">No active assets</div>"}'
            f'</div></div>'
        )

    @staticmethod
    def build_record_screen_html(title: str, records: list[dict], theme: str) -> str:
        """Builds a two-panel record viewing screen (list + detail)."""
        if not records:
            return (
                f'<div style="padding:15px;">'
                f'<div style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">'
                f'{escape(title)}</div>'
                f'<div style="color:#444; text-align:center;">No records found</div></div>'
            )

        # Left panel: clickable record list
        list_items = "".join(
            f'<div class="user-name record-entry" style="padding:4px 8px; border-bottom:1px solid #111; '
            f'cursor:pointer;" onclick="viewRecord({i}, \'{theme}\')">{escape(r["name"])}</div>'
            for i, r in enumerate(records)
        )

        # Right panel: detail placeholder
        detail_placeholder = (
            '<div id="record-detail" style="padding:10px; color:#444;">SELECT A RECORD</div>'
        )

        # Serialize records for JS access
        records_json = json.dumps(records)

        return (
            f'<div style="padding:15px; height:100%; display:flex; flex-direction:column;">'
            f'<div style="color:var(--cyan); font-weight:bold; font-size:14px; margin-bottom:15px;">'
            f'{escape(title)}</div>'
            f'<div style="flex:1; display:grid; grid-template-columns: 200px 1fr; gap:15px; min-height:0;">'
            f'<div style="border-right:1px solid #111; overflow-y:auto; background:rgba(0,0,0,0.2);">'
            f'{list_items}</div>'
            f'<div style="overflow-y:auto;">{detail_placeholder}</div>'
            f'</div></div>'
            f'<script>window._recordData = {records_json};</script>'
        )

    @staticmethod
    def build_logistics_control_html(data: dict) -> str:
        manifest = data.get("manifest")
        if not manifest:
            return '<div style="padding:15px; color:#444;">No manifest data found.</div>'

        return (
            f'<div style="padding:20px; height:100%; display:flex; flex-direction:column;">'
            f'<div style="color:var(--yellow); font-weight:bold; font-size:14px; margin-bottom:10px;">LOGISTICS CONTROL SYSTEM</div>'
            f'<div style="border:1px solid #222; padding:15px; background:rgba(0,0,0,0.4); flex:1;">'
            f'<div style="color:#fff; margin-bottom:10px;">Shipment ID: <span style="color:var(--cyan);">{escape(manifest.id)}</span></div>'
            f'<div style="color:#888; font-size:10px; margin-bottom:5px;">CARGO: {escape(manifest.cargo)}</div>'
            f'<div style="color:#888; font-size:10px; margin-bottom:5px;">ORIGIN: {escape(manifest.origin)}</div>'
            f'<div style="color:#fff; font-size:11px; margin-bottom:15px;">DESTINATION: <span id="dest-val" style="color:var(--orange);">{escape(manifest.hacked_destination or manifest.destination)}</span></div>'
            f'<div style="display:flex; flex-direction:column; gap:10px;">'
            f'<button class="menu-btn" onclick="redirectTransportPrompt(\'{escape(manifest.id)}\')">REDIRECT SHIPMENT</button>'
            f'<button class="menu-btn" onclick="sabotageTransportSecurity(\'{escape(manifest.id)}\')"'
            f'{ " disabled style=\\\"opacity:0.5;\\\"" if manifest.is_security_sabotaged else ""}>'
            f'{ "SECURITY SABOTAGED" if manifest.is_security_sabotaged else "SABOTAGE EXTERNAL SECURITY" }</button>'
            f'</div>'
            f'</div>'
            f'</div>'
        )


class RemoteController:
    def __init__(self, state: GameState):
        self.state = state
        self._active_tools: dict[str, bool] = {}

    def connect(self, ip: str) -> dict:
        """Connect to a server and show its first screen."""
        from core.connection_manager import connect as cm_connect

        result = cm_connect(self.state, ip)
        if result["success"]:
            comp = self.state.computers.get(ip)
            if comp and comp.screens:
                first_screen = comp.screens[0]
                self.state.connection._current_screen = first_screen.screen_type
        return result

    def navigate_screen(self, ip: str, screen_type: int) -> dict:
        """Navigate to a specific screen on the connected server."""
        comp = self.state.computers.get(ip)
        if not comp:
            return {"success": False, "error": "Computer not found"}

        has_screen = any(s.screen_type == screen_type for s in comp.screens)
        if not has_screen:
            return {"success": False, "error": "Screen not available"}

        self.state.connection._current_screen = screen_type
        return {"success": True, "screen_type": screen_type}

    def get_screen_data(self, ip: str) -> dict:
        """Get data for the current screen on a connected server."""
        comp = self.state.computers.get(ip)
        if not comp:
            return {"error": "Computer not found"}

        screen_type = getattr(self.state.connection, "_current_screen", None)
        if screen_type is None:
            return {"error": "No screen active"}

        if screen_type == C.SCREEN_MENUSCREEN:
            return self._render_menu_screen(comp)
        elif screen_type == C.SCREEN_PASSWORDSCREEN:
            return self._render_password_screen(comp)
        elif screen_type == C.SCREEN_FILESERVERSCREEN:
            return self._render_file_server(comp)
        elif screen_type == C.SCREEN_LOGSCREEN:
            return self._render_log_screen(comp)
        elif screen_type == C.SCREEN_BBSSCREEN:
            return self._render_bbs_screen(ip)
        elif screen_type == C.SCREEN_LINKSSCREEN:
            return self._render_links_screen(comp)
        elif screen_type == C.SCREEN_CONSOLESCREEN:
            return self._render_console_screen(comp)
        elif screen_type == C.SCREEN_SWSALESSCREEN:
            return self._render_sw_sales_screen()
        elif screen_type == C.SCREEN_HWSALESSCREEN:
            return self._render_hw_sales_screen()
        elif screen_type == C.SCREEN_NEWSSCREEN:
            return self._render_news_screen()
        elif screen_type == C.SCREEN_RANKINGSCREEN:
            return self._render_ranking_screen()
        elif screen_type == C.SCREEN_ACADEMICSCREEN:
            return self._render_academic_screen(comp)
        elif screen_type == C.SCREEN_CRIMINALSCREEN:
            return self._render_criminal_screen(comp)
        elif screen_type == C.SCREEN_SOCIALSECURITYSCREEN:
            return self._render_social_security_screen(comp)
        elif screen_type == C.SCREEN_CENTRALMEDICALSCREEN:
            return self._render_medical_screen(comp)
        elif screen_type == C.SCREEN_LOGISTICS_CONTROL:
            return self._render_logistics_control(comp)
        else:
            return self._render_company_info(comp)

    def _render_record_bank(self, comp, bank_type: str) -> dict:
        return {
            "type": bank_type,
            "title": comp.name,
            "recordbank": [
                {"name": r.name, "fields": r.fields, "photo_index": r.photo_index}
                for r in comp.recordbank
            ],
        }

    def _render_academic_screen(self, comp) -> dict:
        records = [
            {"name": r.name, "fields": r.fields, "photo_index": r.photo_index}
            for r in comp.recordbank
        ]
        html = ScreenHTMLBuilder.build_record_screen_html("Academic Records", records, "cyan")
        return {"type": "academic", "title": comp.name, "recordbank": records, "html": html}

    def _render_criminal_screen(self, comp) -> dict:
        records = [
            {"name": r.name, "fields": r.fields, "photo_index": r.photo_index}
            for r in comp.recordbank
        ]
        html = ScreenHTMLBuilder.build_record_screen_html("Criminal Records", records, "red")
        return {"type": "criminal", "title": comp.name, "recordbank": records, "html": html}

    def _render_social_security_screen(self, comp) -> dict:
        records = [
            {"name": r.name, "fields": r.fields, "photo_index": r.photo_index}
            for r in comp.recordbank
        ]
        html = ScreenHTMLBuilder.build_record_screen_html("Social Security Records", records, "green")
        return {"type": "social_security", "title": comp.name, "recordbank": records, "html": html}

    def _render_medical_screen(self, comp) -> dict:
        records = [
            {"name": r.name, "fields": r.fields, "photo_index": r.photo_index}
            for r in comp.recordbank
        ]
        html = ScreenHTMLBuilder.build_record_screen_html("Medical Records", records, "orange")
        return {"type": "medical", "title": comp.name, "recordbank": records, "html": html}

    def _render_logistics_control(self, comp) -> dict:
        # Find manifest associated with this vehicle
        manifest = next((m for m in self.state.world.manifests if m.vehicle_ip == comp.ip), None)
        if not manifest:
            return {"error": "Manifest not found for this vehicle"}
        
        html = ScreenHTMLBuilder.build_logistics_control_html({"manifest": manifest})
        return {
            "type": "logistics_control",
            "title": f"Logistics Control - {manifest.id}",
            "manifest": {
                "id": manifest.id,
                "cargo": manifest.cargo,
                "origin": manifest.origin,
                "destination": manifest.destination,
                "hacked_destination": manifest.hacked_destination,
                "is_security_sabotaged": manifest.is_security_sabotaged
            },
            "html": html
        }

    def redirect_transport(self, ip: str, manifest_id: str, new_destination: str) -> dict:
        manifest = next((m for m in self.state.world.manifests if m.id == manifest_id), None)
        if not manifest:
            return {"success": False, "error": "Manifest not found"}
        
        manifest.hacked_destination = new_destination
        log.info(f"TRANSPORT REDIRECTED: {manifest_id} now heading to {new_destination}")
        return {"success": True}

    def sabotage_transport_security(self, ip: str, manifest_id: str) -> dict:
        manifest = next((m for m in self.state.world.manifests if m.id == manifest_id), None)
        if not manifest:
            return {"success": False, "error": "Manifest not found"}
        
        manifest.is_security_sabotaged = True
        log.info(f"TRANSPORT SECURITY SABOTAGED: {manifest_id}")
        return {"success": True}

    def alter_record(self, ip: str, name: str, field: str, new_value: str) -> dict:
        """Modifies a specific record on a remote server."""
        comp = self.state.computers.get(ip)
        if not comp:
            return {"success": False, "error": "Computer not found"}

        record = next((r for r in comp.recordbank if r.name == name), None)
        if not record:
            return {"success": False, "error": "Record not found"}

        record.fields[field] = new_value
        log.info(f"RECORD ALTERED on {ip}: {name} -> {field} set to {new_value}")

        return {"success": True}

    def modify_log(self, ip: str, log_index: int, new_from_ip: str) -> dict:
        """Modify a log entry's from_ip to frame another agent.
        The internal backup log remains untouched for forensic recovery.
        """
        comp = self.state.computers.get(ip)
        if not comp:
            return {"success": False, "error": "Computer not found"}
        if log_index < 0 or log_index >= len(comp.logs):
            return {"success": False, "error": "Log index out of range"}

        old_ip = comp.logs[log_index].from_ip
        comp.logs[log_index].from_ip = new_from_ip
        # Increase suspicion — framing is suspicious behavior
        comp.logs[log_index].suspicion_level = max(comp.logs[log_index].suspicion_level, 1)
        log.info(f"LOG MODIFIED on {ip}: entry #{log_index} from_ip changed from {old_ip} to {new_from_ip}")

        return {"success": True, "old_from": old_ip, "new_from": new_from_ip}

    def _render_menu_screen(self, comp) -> dict:
        screen_names = {
            C.SCREEN_MENUSCREEN: "Menu",
            C.SCREEN_PASSWORDSCREEN: "Password",
            C.SCREEN_FILESERVERSCREEN: "File Server",
            C.SCREEN_LOGSCREEN: "Logs",
            C.SCREEN_BBSSCREEN: "Mission BBS",
            C.SCREEN_LINKSSCREEN: "Links",
            C.SCREEN_CONSOLESCREEN: "Console",
            C.SCREEN_SWSALESSCREEN: "Software Upgrades",
            C.SCREEN_HWSALESSCREEN: "Hardware Upgrades",
            C.SCREEN_NEWSSCREEN: "News",
            C.SCREEN_RANKINGSCREEN: "Rankings",
            C.SCREEN_COMPANYINFO: "Company Info",
            C.SCREEN_ACCOUNTSCREEN: "Accounts",
            C.SCREEN_LOANSSCREEN: "Loans",
            C.SCREEN_SHARESLISTSCREEN: "Shares",
            C.SCREEN_CRIMINALSCREEN: "Criminal Records",
            C.SCREEN_ACADEMICSCREEN: "Academic Records",
            C.SCREEN_SOCIALSECURITYSCREEN: "Social Security",
            C.SCREEN_SECURITYSCREEN: "Security",
            C.SCREEN_CENTRALMEDICALSCREEN: "Medical Records",
        }
        options = []
        for s in comp.screens:
            if s.screen_type == C.SCREEN_PASSWORDSCREEN:
                continue
            name = screen_names.get(s.screen_type, f"Screen {s.screen_type}")
            options.append({"screen_type": s.screen_type, "name": name})
        html = ScreenHTMLBuilder.build_menu_html(comp.name, options)
        return {"type": "menu", "title": comp.name, "options": options, "html": html}

    def _render_password_screen(self, comp) -> dict:
        pw_screen = next((s for s in comp.screens if s.screen_type == 1), None)
        expected_pw = pw_screen.data1 if pw_screen else ""
        hint = f"Admin password: {expected_pw}" if expected_pw else ""
        html = ScreenHTMLBuilder.build_password_html(f"{comp.name} - Password Required", hint)
        return {
            "type": "password",
            "title": f"{comp.name} - Password Required",
            "hint": hint,
            "html": html,
        }

    def _render_file_server(self, comp) -> dict:
        files = [{"name": f.filename, "size": f.size, "type": f.file_type} for f in comp.files]
        html = ScreenHTMLBuilder.build_file_server_html(files)
        return {
            "type": "file_server",
            "title": f"{comp.name} - File Server",
            "files": files,
            "html": html,
        }

    def _render_log_screen(self, comp) -> dict:
        logs = []
        for i, log_entry in enumerate(comp.logs):
            is_mod = comp.log_modified(i)
            logs.append({
                "index": i,
                "subject": log_entry.subject,
                "from": log_entry.from_ip,
                "time": log_entry.log_time,
                "modified": is_mod,
            })
        html = ScreenHTMLBuilder.build_logs_html(logs)
        return {
            "type": "logs",
            "title": f"{comp.name} - Logs",
            "logs": logs,
            "html": html,
        }

    def _render_bbs_screen(self, ip: str) -> dict:
        from core.mission_engine import get_available_missions
        missions = get_available_missions(self.state)
        html = ScreenHTMLBuilder.build_bbs_html(missions)
        return {"type": "bbs", "title": "Mission BBS", "missions": missions, "html": html}

    def _render_links_screen(self, comp) -> dict:
        html = ScreenHTMLBuilder.build_links_html(comp.links)
        return {"type": "links", "title": f"{comp.name} - Links", "links": comp.links, "html": html}

    def _render_console_screen(self, comp) -> dict:
        html = ScreenHTMLBuilder.build_console_html(comp.console_cwd)
        return {"type": "console", "title": f"{comp.name} - Console", "cwd": comp.console_cwd, "html": html}

    def _render_sw_sales_screen(self) -> dict:
        from core.store_engine import get_software_catalog
        items = get_software_catalog()
        html = ScreenHTMLBuilder.build_software_sales_html(items)
        return {"type": "sw_sales", "title": "Software Upgrades", "items": items, "html": html}

    def _render_hw_sales_screen(self) -> dict:
        from core.store_engine import get_hardware_catalog, get_cooling_catalog, get_psu_catalog, get_addon_catalog
        gateways = get_hardware_catalog()
        cooling = get_cooling_catalog()
        psu = get_psu_catalog()
        addons = get_addon_catalog()
        html = ScreenHTMLBuilder.build_hardware_sales_html(gateways, cooling, psu, addons)
        return {
            "type": "hw_sales",
            "title": "Hardware Upgrades",
            "gateways": gateways,
            "cooling": cooling,
            "psu": psu,
            "addons": addons,
            "html": html,
        }

    def _render_news_screen(self) -> dict:
        from core.news_engine import get_recent_news
        articles = get_recent_news(self.state)
        html = ScreenHTMLBuilder.build_news_html(articles)
        return {"type": "news", "title": "News", "articles": articles, "html": html}

    def _render_ranking_screen(self) -> dict:
        from core.npc_engine import get_rankings
        rankings = get_rankings(self.state)
        html = ScreenHTMLBuilder.build_rankings_html(rankings)
        return {"type": "rankings", "title": "Agent Rankings", "rankings": rankings, "html": html}

    def _render_company_info(self, comp) -> dict:
        # Look up the company by name to get type, size, stock_price
        company = next(
            (c for c in self.state.world.companies if c.name == comp.company_name),
            None,
        )
        data = {
            "type": "company_info",
            "title": comp.company_name or comp.name,
            "name": comp.name,
            "company_type": company.company_type.name if company else "Unknown",
            "size": company.size if company else 0,
            "stock_price": company.stock_price if company else 0.0,
            "owner": "Player" if (company and company.owner_id == "PLAYER") else "NPC",
        }
        html = ScreenHTMLBuilder.build_company_info_html(data)
        return {**data, "html": html}

    def get_remote_state(self, ip: str) -> dict:
        comp = self.state.computers.get(ip)
        if not comp:
            return {"error": "Computer not found"}

        security = {
            "proxy": {"level": 0, "active": False, "bypassed": False},
            "firewall": {"level": 0, "active": False, "bypassed": False},
            "monitor": {"level": 0, "active": False, "bypassed": False},
            "encrypter": {"level": 0, "active": False, "bypassed": False}
        }
        for sec_sys in comp.security_systems:
            # Map type to string key
            s_map = {1: "proxy", 2: "firewall", 3: "monitor", 4: "encrypter"}
            key = s_map.get(sec_sys.security_type)
            if key:
                # 'active' in UI context means 'currently providing protection'
                security[key] = {
                    "level": sec_sys.level,
                    "active": sec_sys.is_active and not sec_sys.is_bypassed,
                    "bypassed": sec_sys.is_bypassed
                }

        is_unlocked = (
            comp.ip == self.state.player.localhost_ip or
            comp.computer_type == 0 or
            ip in self.state.player.known_passwords
        )
        links = []
        if comp.computer_type == NodeType.INTERNIC or comp.name == "InterNIC":
            links = [
                {"name": c.name, "ip": c.ip}
                for c in self.state.computers.values()
                if getattr(c, "listed", False) and c.ip != self.state.player.localhost_ip
            ]

        has_console = any(s.screen_type == C.SCREEN_CONSOLESCREEN for s in comp.screens)
        server_data = {
            "name": comp.name,
            "ip": comp.ip,
            "is_unlocked": is_unlocked,
            "security": security,
            "links": links,
            "has_console": has_console,
            "files": [
                {"id": file_obj.filename, "name": file_obj.filename, "size": file_obj.size, "type": "data"}
                for file_obj in comp.files
            ],
            "logs": [
                {"time": log_entry.log_time, "from": log_entry.from_ip, "action": log_entry.subject, "type": "hack"}
                for log_entry in comp.logs if not log_entry.is_deleted
            ],
        }

        local_ram = []
        for idx, file_obj in enumerate(self.state.vfs.files):
            if file_obj.software_type != SoftwareType.NONE or file_obj.file_type == 2:
                is_active = self._active_tools.get(f"vfs_{idx}", True)
                local_ram.append({
                    "id": f"vfs_{idx}",
                    "name": file_obj.filename.split(".")[0],
                    "type": "utility",
                    "active": is_active
                })

        active_tasks = []
        for task in self.state.tasks:
            if task.target_ip == ip:
                active_tasks.append({
                    "id": str(task.task_id),
                    "name": task.tool_name,
                    "target_type": task.extra.get("target_type", "unknown"),
                    "target_id": task.extra.get("target_id", ""),
                    "progress": task.progress
                })

        conn = self.state.connection
        show_trace = any(t["name"] == "Trace_Tracker" for t in local_ram)
        screen_data = self.get_screen_data(ip)
        current_screen = (
            screen_data
            if isinstance(screen_data, dict) and "type" in screen_data
            else None
        )

        return {
            "server": server_data,
            "local_ram": local_ram,
            "tasks": active_tasks,
            "trace_active": conn.trace_active,
            "trace_progress": conn.trace_progress * 100 if show_trace else 0,
            "show_trace_warning": show_trace and conn.trace_active,
            "game_over": False,
            "game_over_reason": "",
            "manifests": [],
            "companies": {},
            "current_screen": current_screen,
            "screen_data": current_screen,
            "screen_options": (
                current_screen.get("options", [])
                if current_screen and current_screen.get("type") == "menu"
                else []
            ),
        }

    def execute_hack(self, ip: str, tool_name: str, target_type: str, target_id: str) -> dict:
        base_name = tool_name.split(" v")[0].replace(" ", "_")
        version = 1
        if " v" in tool_name:
            try:
                version = int(tool_name.split(" v")[1].split(".")[0])
            except ValueError:
                pass

        comp = self.state.computers.get(ip)
        # Trace starts ONLY if a monitor is active AND NOT bypassed
        monitor_active = (
            any(sec.security_type == 3 and sec.is_active and not sec.is_bypassed for sec in comp.security_systems)
            if comp else False
        )
        if monitor_active and not self.state.connection.trace_active:
            trace_engine.start_trace(self.state)

        target_data = {"target_type": target_type, "target_id": target_id}
        if target_type == "log":
            try:
                target_data["log_index"] = int(target_id)
            except ValueError:
                pass
        elif target_type == "file":
            target_data["filename"] = target_id

        try:
            res = task_engine.start_task(
                self.state, base_name, tool_version=version,
                target_ip=ip, target_data=target_data
            )
            return {"success": True, "task_id": res["task_id"]}
        except Exception as e:
            return {"success": False, "msg": str(e)}

    def toggle_tool(self, tool_id: str) -> dict:
        idx = int(tool_id.replace("vfs_", "")) if tool_id.startswith("vfs_") else -1
        if idx < 0 or idx >= len(self.state.vfs.files):
            return {"success": False, "error": "Tool not found"}

        tool = self.state.vfs.files[idx]
        tool.is_active = not tool.is_active
        return {"success": True, "active": tool.is_active}

    def toggle_remote_security(self, ip: str, sec_type: int) -> dict:
        comp = self.state.computers.get(ip)
        if not comp:
            return {"success": False, "error": "Computer not found"}
        for sec in comp.security_systems:
            if sec.security_type == sec_type:
                sec.is_active = not sec.is_active
                return {"success": True, "is_active": sec.is_active}
        return {"success": False, "error": "Security system not found"}

    def execute_console_command(self, ip: str, command: str) -> dict:
        comp = self.state.computers.get(ip)
        if not comp or not comp.is_running:
            return {"success": False, "error": "Computer unavailable", "output": []}
        if not any(s.screen_type == C.SCREEN_CONSOLESCREEN for s in comp.screens):
            return {"success": False, "error": "No console", "output": []}

        parts = command.strip().split()
        if not parts:
            return {"success": True, "output": [], "cwd": comp.console_cwd}

        cmd, args, output = parts[0].lower(), parts[1:], []
        if cmd == "pwd":
            output.append(comp.console_cwd)
        elif cmd == "cd":
            if not args:
                output.append("Usage: cd <dir>")
            else:
                target = args[0]
                if target in ("/", "usr", "/usr", "sys", "/sys", "data", "/data"):
                    comp.console_cwd = target if target.startswith("/") else f"/{target}"
                elif target == "..":
                    comp.console_cwd = "/"
                else:
                    return {
                        "success": False, "error": "Not found",
                        "output": [], "cwd": comp.console_cwd
                    }
        elif cmd == "ls":
            files = [
                f.filename for f in comp.files
                if (comp.console_cwd == "/" and f.file_type == 1) or
                (comp.console_cwd == "/usr" and f.file_type == 1) or
                (comp.console_cwd == "/sys" and f.file_type == 2)
            ]
            output.extend(files if files else ["No files."])
        elif cmd == "delete":
            to_del = [
                f.filename for f in comp.files
                if (not args or f.filename == args[0]) and
                ((comp.console_cwd == "/" and f.file_type == 1) or
                 (comp.console_cwd == "/usr" and f.file_type == 1) or
                 (comp.console_cwd == "/sys" and f.file_type == 2))
            ]
            if args and not to_del:
                return {
                    "success": False, "error": "Not found",
                    "output": [], "cwd": comp.console_cwd
                }
            comp.files = [f for f in comp.files if f.filename not in to_del]
            output.append(
                f"Deleted {len(to_del)} files." if not args else f"Deleted {args[0]}."
            )
        elif cmd == "shutdown":
            comp.is_running = False
            output = ["Shutting down..."]
        elif cmd == "help":
            output.append("pwd, cd, ls, delete, shutdown, help")
        else:
            return {
                "success": False, "error": "Unknown",
                "output": [], "cwd": comp.console_cwd
            }
        return {"success": True, "output": output, "cwd": comp.console_cwd}

    def get_bounce_chain(self) -> dict:
        return {
            "success": True,
            "chain": list(self.state.bounce.hops),
            "count": len(self.state.bounce.hops)
        }

    def add_bounce_node(self, ip: str) -> dict:
        if ip not in self.state.computers or ip in self.state.bounce.hops:
            return {"success": False, "error": "Invalid IP"}
        self.state.bounce.hops.append(ip)
        return {"success": True, "chain": list(self.state.bounce.hops)}

    def remove_bounce_node(self, ip: str) -> dict:
        if (
            ip not in self.state.bounce.hops or
            (ip == self.state.player.localhost_ip and len(self.state.bounce.hops) == 1)
        ):
            return {"success": False, "error": "Invalid remove"}
        self.state.bounce.hops.remove(ip)
        return {"success": True, "chain": list(self.state.bounce.hops)}

    def reorder_bounce_chain(self, new_order: list[str]) -> dict:
        if set(new_order) != set(self.state.bounce.hops):
            return {"success": False, "error": "Invalid reorder"}
        self.state.bounce.hops = list(new_order)
        return {"success": True, "chain": list(self.state.bounce.hops)}
