"""
Onlink-Clone: Unified Web UI Entry Point (v0.5.1)

Combines high-fidelity simulation logic with a robust Eel bridge.
Restored missing bridges for Neuromancer, Suspicion, Robbery, LAN, and Logistics.
"""

import os
import eel
import logging
import random
from core.engine import GameEngine
from core.world_generator import generate_world
from core import connection_manager, constants as C
from core.game_state import SoftwareType, CompanyType
from core.remote_controller import RemoteController
from core import persistence

# Setup logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Initialize the backend engine ONCE
engine = GameEngine()

# =========================================================================
# Internal Helpers
# =========================================================================

def get_rc():
    """Always returns a RemoteController bound to the CURRENT engine state."""
    return RemoteController(engine.state)

def ensure_world_exists():
    """If the world is empty, generate it immediately to prevent black maps."""
    if not engine.state.computers:
        log.info("OS: World empty, generating canonical nodes...")
        generate_world(engine.state)
        # Ensure player knows core nodes
        for ip in [C.IP_INTERNIC, C.IP_UPLINK_PUBLIC, C.IP_UPLINK_INTERNAL]:
            if ip not in engine.state.player.known_ips:
                engine.state.player.known_ips.append(ip)
        persistence.save_profile(engine.state)

# =========================================================================
# Exposed Core Functions
# =========================================================================

@eel.expose
def get_game_state():
    state = engine.state
    ensure_world_exists()
    return {
        "clock": {
            "tick": state.clock.tick_count,
            "date": state.clock.game_date
        },
        "player": {
            "handle": state.player.handle,
            "balance": state.player.balance,
            "neuromancer_rating": state.player.neuromancer_rating
        },
        "vfs": [file_obj.filename for file_obj in state.vfs.files],
        "connected_ip": state.connection.target_ip
    }

@eel.expose
def list_profiles():
    return persistence.list_profiles()

@eel.expose
def set_player_profile(name: str, handle: str, password: str):
    engine.state.player.name = name
    engine.state.player.handle = handle
    engine.state.player.password = password
    ip = f"185.{random.randint(10,250)}.{random.randint(1,254)}.{random.randint(1,254)}"
    engine.state.player.localhost_ip = ip
    generate_world(engine.state)
    persistence.save_profile(engine.state)
    return {"success": True}

@eel.expose
def load_player_profile(handle: str, password: str):
    save_path = os.path.join(persistence.PROFILES_DIR, f"{handle}.json")
    try:
        import json
        from core.apps import reset_registry
        with open(save_path, "r") as f:
            data = json.load(f)
            if data.get("player", {}).get("password") != password:
                return {"success": False, "error": "Invalid Code"}
            if persistence.load_profile_from_data(engine.state, data):
                ensure_world_exists()
                engine.stop()
                engine.start()
                reset_registry()  # Rebuild registry with loaded state's VFS
                return {"success": True, "handle": handle}
    except Exception as e:
        log.error(f"Load failed: {e}", exc_info=True)
    return {"success": False, "error": "Profile error"}

@eel.expose
def delete_player_profile(handle: str):
    return {"success": persistence.delete_profile(handle)}

# =========================================================================
# Exposed App Logic
# =========================================================================

@eel.expose
def list_apps(category: str = None):
    from core.apps import get_registry
    return get_registry(engine.state).list_apps(engine.state, category)

@eel.expose
def open_app(app_id: str):
    from core.apps import get_registry
    reg = get_registry(engine.state)
    app_cls = reg.get(app_id)
    if not app_cls:
        return {"error": "App not found"}
    return app_cls(engine.state).init()

@eel.expose
def call_app_func(app_id: str, func_name: str, *args):
    from core.apps import get_registry
    reg = get_registry(engine.state)
    app_cls = reg.get(app_id)
    if not app_cls:
        return {"success": False, "error": "App not found"}
    app_inst = app_cls(engine.state)
    funcs = app_inst.expose_functions()
    if func_name not in funcs:
        return {"success": False, "error": "Function not found"}
    return funcs[func_name](*args)

@eel.expose
def get_nodes(query: str = ""):
    ensure_world_exists()
    nodes = []
    search_query = query.lower().strip()
    state = engine.state
    for computer in state.computers.values():
        if computer.ip in state.player.known_ips or computer.computer_type == 10:
            if computer.x == 0 and computer.y == 0:
                continue
            if (
                search_query and
                search_query not in computer.name.lower() and
                search_query not in computer.ip
            ):
                continue
            nodes.append({
                "ip": computer.ip,
                "name": computer.name,
                "x": computer.x,
                "y": computer.y,
                "type": computer.computer_type
            })
    nodes.sort(key=lambda x: x["name"])
    return nodes

@eel.expose
def get_remote_state(ip: str):
    return get_rc().get_remote_state(ip)

@eel.expose
def attempt_connect(ip: str):
    bounce_ips = [b for b in engine.state.bounce.hops if b != ip]
    res = connection_manager.connect(engine.state, ip, bounce_ips=bounce_ips)
    if res["success"]:
        comp = engine.state.computers.get(ip)
        if comp and comp.screens:
            menu = next((s for s in comp.screens if s.screen_type == C.SCREEN_MENUSCREEN), None)
            engine.state.connection._current_screen = menu.screen_type if menu else comp.screens[0].screen_type
    return res

@eel.expose
def navigate_screen(ip: str, screen_type: int):
    return get_rc().navigate_screen(ip, screen_type)

@eel.expose
def disconnect():
    return connection_manager.disconnect(engine.state)

@eel.expose
def toggle_bounce(ip: str):
    hops = engine.state.bounce.hops
    if ip == '__clear__':
        hops.clear()
    elif ip in hops:
        hops.remove(ip)
    else:
        hops.append(ip)
    if C.IP_INTERNIC in hops:
        hops.remove(C.IP_INTERNIC)
        hops.insert(0, C.IP_INTERNIC)
    return hops

@eel.expose
def get_hardware_status():
    state = engine.state
    gw = state.gateway
    active_tasks = [t for t in state.tasks if t.is_active]
    from core.hardware_engine import HardwareEngine
    task_info = []
    total_power = sum(t.cpu_cost_ghz for t in active_tasks)
    for task in active_tasks:
        share = HardwareEngine.allocate_cpu_power(state, total_power, task.cpu_cost_ghz)
        task_info.append({"id": str(task.task_id), "name": task.tool_name, "ghz_share": share})

    return {
        "gateway": {
            "name": gw.name, "heat": gw.heat, "max_heat": gw.max_heat,
            "power_draw": gw.power_draw, "psu_capacity": gw.psu_capacity,
            "vfs_map": [file_obj is not None for file_obj in state.vfs.files]
        },
        "tasks": task_info,
        "vfs": [
            {
                "id": f.id,
                "name": f.filename,
                "size_gq": f.size_gq,
                "ram_cost": f.ram_cost,
                # FIXED: Explicit comparison for test_vfs_type_uses_explicit_comparison
                "type": "tool" if f.software_type != SoftwareType.NONE else "data",
                "blocks": f.blocks,
                "active": f.is_active,
            }
            for f in state.vfs.files
        ]
    }

@eel.expose
def get_finance_state():
    from core.finance_engine import get_player_accounts
    return {"accounts": get_player_accounts(engine.state)}

@eel.expose
def get_finance_html():
    return get_rc().build_finance_html()

@eel.expose
def get_rankings():
    from core.npc_engine import get_rankings
    return get_rankings(engine.state)

@eel.expose
def get_messages():
    return [
        {
            "id": msg.id,
            "from": msg.from_name,
            "subject": msg.subject,
            "body": msg.body,
            "is_read": msg.is_read,
            "created_at_tick": msg.created_at_tick
        }
        for msg in engine.state.messages
    ]

@eel.expose
def mark_message_read(msg_id: int):
    msg = next((m for m in engine.state.messages if m.id == msg_id), None)
    if msg:
        msg.is_read = True
    return {"success": True}

@eel.expose
def get_missions():
    from core.mission_engine import get_available_missions
    return get_available_missions(engine.state)

@eel.expose
def get_active_missions():
    from core.mission_engine import get_active_missions
    return get_active_missions(engine.state)

@eel.expose
def get_news():
    from core.news_engine import get_recent_news
    return get_recent_news(engine.state)

@eel.expose
def get_bounce_chain():
    return engine.state.bounce.hops

@eel.expose
def save_ip(ip: str):
    if ip not in engine.state.player.known_ips:
        engine.state.player.known_ips.append(ip)
        from core import persistence
        persistence.save_profile(engine.state)
    return {"success": True}

@eel.expose
def toggle_tool(tool_id: str):
    return get_rc().toggle_tool(tool_id)

@eel.expose
def toggle_remote_security(ip: str, sec_type: int):
    return get_rc().toggle_remote_security(ip, sec_type)

@eel.expose
def set_speed(speed: int):
    engine.set_speed(speed)
    return {"success": True}

@eel.expose
def stop_task(task_id: int):
    from core.task_engine import stop_task
    return stop_task(engine.state, task_id)

@eel.expose
def found_company(name: str, type_idx: int):
    from core.company_engine import found_company
    return found_company(engine.state, name, CompanyType(type_idx))

@eel.expose
def set_cpu_overclock(cpu_id: int, mult: float):
    from core.hardware_engine import HardwareEngine
    return {"success": HardwareEngine.set_cpu_overclock(engine.state, cpu_id, mult)}

@eel.expose
def set_ram_overclock(mult: float):
    from core.hardware_engine import HardwareEngine
    HardwareEngine.set_ram_overclock(engine.state, mult)
    return {"success": True}

@eel.expose
def set_storage_overclock(mult: float):
    from core.hardware_engine import HardwareEngine
    HardwareEngine.set_storage_overclock(engine.state, mult)
    return {"success": True}

@eel.expose
def defrag_vfs():
    from core.vfs import VirtualFileSystem
    return {"success": True, "reclaimed": VirtualFileSystem.defrag(engine.state)}

@eel.expose
def delete_vfs_file(filename: str):
    from core.vfs import VirtualFileSystem
    return {"success": VirtualFileSystem.delete_file(engine.state, filename)}

@eel.expose
def alter_record(ip: str, name: str, field: str, val: str):
    return get_rc().alter_record(ip, name, field, val)

@eel.expose
def modify_log(ip: str, log_index: int, new_from_ip: str):
    return get_rc().modify_log(ip, log_index, new_from_ip)

@eel.expose
def execute_hack(ip: str, tool_name: str, target_type: str, target_id: str):
    return get_rc().execute_hack(ip, tool_name, target_type, target_id)

@eel.expose
def console_command(ip: str, command: str):
    return get_rc().execute_console_command(ip, command)

@eel.expose
def redirect_transport(ip: str, manifest_id: str, new_destination: str):
    return get_rc().redirect_transport(ip, manifest_id, new_destination)

@eel.expose
def sabotage_transport(ip: str, manifest_id: str):
    return get_rc().sabotage_transport_security(ip, manifest_id)

@eel.expose
def pay_bail():
    from core.event_scheduler import pay_bail as pb
    return pb(engine.state)

@eel.expose
def get_neuromancer():
    from core.neuromancer import get_neuromancer_level
    return {"level": get_neuromancer_level(engine.state), "rating": engine.state.player.neuromancer_rating}

@eel.expose
def get_suspicion():
    from core.log_suspicion import SUSPICION_NAMES
    max_suspicion = 0
    for comp in engine.state.computers.values():
        for log_entry in comp.logs:
            if not log_entry.is_deleted:
                max_suspicion = max(max_suspicion, log_entry.suspicion_level)
    return {"level": max_suspicion, "name": SUSPICION_NAMES.get(max_suspicion, "None")}

@eel.expose
def get_robbery_timer():
    from core.bank_robbery import get_active_robbery
    timer = get_active_robbery(engine.state)
    if not timer:
        return {"active": False}
    return {
        "active": True,
        "bank_ip": timer["bank_ip"],
        "ticks_left": timer["ticks_remaining"],
        "amount": timer["amount"]
    }

@eel.expose
def get_passive_traces():
    return [{"id": pt.trace_id, "node": pt.current_node_ip, "target": pt.target_ip, "ticks": pt.ticks_until_next_hop} for pt in engine.state.passive_traces]

@eel.expose
def get_manifests():
    return [{"id": m.id, "origin": m.origin, "destination": m.destination, "cargo": m.cargo, "progress": m.progress} for m in engine.state.world.manifests if m.status == "IN_TRANSIT"]

@eel.expose
def hijack_shipment(manifest_id: str, squad_id: str = None):
    manifest = next((m for m in engine.state.world.manifests if m.id == manifest_id), None)
    if not manifest:
        return {"success": False, "error": "Manifest not found"}
    
    # Try to find the squad
    squad = next((s for s in engine.state.world.pmc_squads if s.id == squad_id), None)
    if not squad and engine.state.world.pmc_squads:
        squad = engine.state.world.pmc_squads[0]
        
    if not squad:
        # Fallback to a default squad if none exists (legacy support)
        from core.game_state import PMCSquad
        squad = PMCSquad(id="DEFAULT", name="Alpha Squad", combat_rating=50.0)
        
    return {"success": engine.pmc.attempt_intercept(engine.state, manifest, squad)}

@eel.expose
def start_lan_scan(target_ip: str):
    from core.lan_engine import start_lan_scan as sls
    return sls(engine.state, target_ip)

@eel.expose
def get_lan_state(target_ip: str = None):
    from core.lan_engine import get_lan_state as gls
    return gls(engine.state, target_ip)

@eel.expose
def probe_lan_node(target_ip: str, node_id: int):
    from core.lan_engine import probe_node
    return probe_node(engine.state, target_ip, node_id)

@eel.expose
def spoof_lan_node(target_ip: str, node_id: int):
    from core.lan_engine import spoof_node
    return spoof_node(engine.state, target_ip, node_id)

# =========================================================================
# Mission & Store Actions (Server Screens)
# =========================================================================

@eel.expose
def accept_mission(mission_id: int):
    from core.mission_engine import accept_mission as am
    return am(engine.state, mission_id)

@eel.expose
def negotiate_mission(mission_id: int, increase_pct: int = 20):
    from core.mission_engine import negotiate_mission as nm
    return nm(engine.state, mission_id, increase_pct)

@eel.expose
def complete_mission(mission_id: int):
    from core.mission_engine import complete_mission as cm
    return cm(engine.state, mission_id)

@eel.expose
def buy_software(name: str, version: int = 1):
    from core.store_engine import buy_software as bs
    return bs(engine.state, name, version)

@eel.expose
def buy_gateway(name: str):
    from core.store_engine import buy_gateway as bg
    return bg(engine.state, name)

@eel.expose
def buy_cooling(name: str):
    from core.store_engine import buy_cooling as bc
    return bc(engine.state, name)

@eel.expose
def buy_psu(name: str):
    from core.store_engine import buy_psu as bp
    return bp(engine.state, name)

@eel.expose
def buy_addon(name: str):
    from core.store_engine import buy_addon as ba
    return ba(engine.state, name)

@eel.expose
def buy_cpu(cpu_index: int, model: str):
    from core.store_engine import buy_cpu as bc
    return bc(engine.state, cpu_index, model)

@eel.expose
def buy_modem(model: str):
    from core.store_engine import buy_modem as bm
    return bm(engine.state, model)

@eel.expose
def buy_memory(model: str):
    from core.store_engine import buy_memory as bme
    return bme(engine.state, model)

@eel.expose
def get_hardware_upgrades(category: str):
    from core.constants import HARDWARE_UPGRADES
    cat_map = {"cpu": 1, "modem": 2, "memory": 4}
    cat_id = cat_map.get(category.lower(), 0)
    items = [
        {"name": h[0], "price": h[2]} 
        for h in HARDWARE_UPGRADES 
        if h[1] == cat_id
    ]
    return items

@eel.expose
def transfer_money(from_id: int, to_id: int, amount: int):
    from core.finance_engine import transfer_funds
    return transfer_funds(engine.state, from_id, to_id, amount)

@eel.expose
def open_bank_account(bank_ip: str):
    from core.finance_engine import open_account
    return open_account(engine.state, bank_ip)

@eel.expose
def take_loan(acct_id: int, amount: int):
    from core.finance_engine import take_loan as tl
    return tl(engine.state, acct_id, amount)

@eel.expose
def repay_loan(loan_id: int):
    from core.finance_engine import repay_loan as rl
    return rl(engine.state, loan_id)

@eel.expose
def buy_stock(company_name: str, shares: int):
    from core.finance_engine import buy_stock as bs
    return bs(engine.state, company_name, shares)

@eel.expose
def sell_stock(company_name: str, shares: int):
    from core.finance_engine import sell_stock as ss
    return ss(engine.state, company_name, shares)

@eel.expose
def delete_transaction_log(tx_hash: str):
    from core.finance_engine import delete_transaction_log as dtl
    return dtl(engine.state, tx_hash)

# =========================================================================
# Event Callbacks
# =========================================================================

def on_tick(tick_count):
    if not hasattr(eel, "update_hud"):
        return
    state = engine.state
    
    # High-Fidelity Throttling: Only push HUD every 4 ticks (~5Hz) 
    # unless a trace is active (requires 20Hz for smooth progress)
    if tick_count % 4 != 0 and not state.connection.trace_active:
        return

    try:
        hours = (tick_count // 3600) % 24
        minutes = (tick_count // 60) % 60
        seconds = tick_count % 60
        day, month, year = state.clock.game_date
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        data = {
            "clock": {
                "full_str": f"{hours:02d}:{minutes:02d}:{seconds:02d}, {day} {months[month-1]} {year}",
                "time_str": f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            },
            "player": {
                "balance_str": f"{state.player.balance:,}",
                "handle": state.player.handle,
                "localhost_ip": state.player.localhost_ip,
                "neuromancer_str": f"NR:{state.player.neuromancer_rating} Neutral",
                "credit_score": state.player.credit_score
            },
            "trace": {
                "active": state.connection.trace_active,
                "progress": state.connection.trace_progress
            },
            "_hot_ratio": state._hot_ratio # Sync global suspect funds
        }
        eel.update_hud(data)()
    except Exception:
        pass

engine.events.connect("tick_completed", on_tick)

def on_game_over(reason):
    """Handle game over events and push to frontend."""
    if not hasattr(eel, "update_hud"):
        return
    try:
        if not hasattr(eel, "trigger_event"):
            log.warning("Eel trigger_event not exposed, skipping game_over event")
            return
        # reason can be a string or a dict with type/reason fields
        if isinstance(reason, dict):
            eel.trigger_event(reason)()
        else:
            eel.trigger_event({"type": "game_over", "msg": str(reason)})()
    except Exception as e:
        log.error(f"on_game_over failed: {e}", exc_info=True)

engine.events.connect("game_over", on_game_over)

def on_tasks_changed(data):
    """Pushes task progress/completion updates to the UI."""
    if hasattr(eel, "update_tasks"):
        try:
            eel.update_tasks(data)()
        except Exception:
            pass

engine.events.connect("task_progress", on_tasks_changed)
engine.events.connect("task_completed", on_tasks_changed)

def start_game():
    engine.start()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    eel.init("web")
    try:
        eel.start("index.html", size=(1300, 850), mode="edge", port=0)
    except (SystemExit, KeyboardInterrupt):
        engine.stop()

if __name__ == "__main__":
    start_game()
