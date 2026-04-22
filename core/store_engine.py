"""
Onlink-Clone: Store Engine

Hardware upgrades and software purchases.
Ported from the ajhenley fork — all SQLAlchemy replaced with GameState ops.
"""

from __future__ import annotations

import logging

from core.game_state import GameState, SoftwareType, VFSFile

log = logging.getLogger(__name__)

# ======================================================================
# Catalogs
# ======================================================================
HARDWARE_CATALOG = [
    {
        "name": "Gateway ALPHA",
        "cpu": 60,
        "modem": 1,
        "memory": 24,
        "psu": 100,
        "cooling": 1.0,
        "price": 0,
    },
    {
        "name": "Gateway BETA",
        "cpu": 80,
        "modem": 2,
        "memory": 32,
        "psu": 150,
        "cooling": 1.2,
        "price": 3000,
    },
    {
        "name": "Gateway GAMMA",
        "cpu": 100,
        "modem": 3,
        "memory": 48,
        "psu": 200,
        "cooling": 1.5,
        "price": 6000,
    },
    {
        "name": "Gateway DELTA",
        "cpu": 120,
        "modem": 4,
        "memory": 64,
        "psu": 300,
        "cooling": 2.0,
        "price": 12000,
    },
    {
        "name": "Gateway OMEGA",
        "cpu": 150,
        "modem": 5,
        "memory": 96,
        "psu": 500,
        "cooling": 3.0,
        "price": 25000,
    },
]

COOLING_CATALOG = [
    {"name": "Standard Heat Sink", "cooling": 1.0, "price": 0},
    {"name": "Dual Fan Array", "cooling": 1.5, "price": 500},
    {"name": "Liquid Loop v1", "cooling": 2.5, "price": 2000},
    {"name": "Cryo-Plate", "cooling": 5.0, "price": 8000},
]

PSU_CATALOG = [
    {"name": "Generic 100W PSU", "psu": 100, "price": 0},
    {"name": "Bronze 250W PSU", "psu": 250, "price": 800},
    {"name": "Gold 500W PSU", "psu": 500, "price": 2500},
    {"name": "Nuclear Cell 1000W", "psu": 1000, "price": 10000},
]

SOFTWARE_CATALOG = [
    {
        "name": "Password Breaker",
        "version": 1,
        "size": 2,
        "type": SoftwareType.CRACKERS,
        "price": 0,
    },
    {
        "name": "Password Breaker",
        "version": 2,
        "size": 2,
        "type": SoftwareType.CRACKERS,
        "price": 1500,
    },
    {
        "name": "Password Breaker",
        "version": 3,
        "size": 3,
        "type": SoftwareType.CRACKERS,
        "price": 5000,
    },
    {
        "name": "Password Breaker",
        "version": 4,
        "size": 3,
        "type": SoftwareType.CRACKERS,
        "price": 12000,
    },
    {
        "name": "Password Breaker",
        "version": 5,
        "size": 4,
        "type": SoftwareType.CRACKERS,
        "price": 25000,
    },
    {
        "name": "Password Breaker",
        "version": 6,
        "size": 5,
        "type": SoftwareType.CRACKERS,
        "price": 50000,
    },
    {
        "name": "Password Breaker",
        "version": 7,
        "size": 6,
        "type": SoftwareType.CRACKERS,
        "price": 100000,
    },
    {
        "name": "File Copier",
        "version": 1,
        "size": 1,
        "type": SoftwareType.FILE_UTIL,
        "price": 0,
    },
    {
        "name": "File Copier",
        "version": 2,
        "size": 1,
        "type": SoftwareType.FILE_UTIL,
        "price": 500,
    },
    {
        "name": "File Deleter",
        "version": 1,
        "size": 1,
        "type": SoftwareType.FILE_UTIL,
        "price": 0,
    },
    {
        "name": "File Deleter",
        "version": 2,
        "size": 1,
        "type": SoftwareType.FILE_UTIL,
        "price": 500,
    },
    {
        "name": "Log Deleter",
        "version": 1,
        "size": 1,
        "type": SoftwareType.LOG_TOOLS,
        "price": 0,
    },
    {
        "name": "Log Deleter",
        "version": 2,
        "size": 1,
        "type": SoftwareType.LOG_TOOLS,
        "price": 800,
    },
    {
        "name": "Log Deleter",
        "version": 3,
        "size": 1,
        "type": SoftwareType.LOG_TOOLS,
        "price": 2000,
    },
    {
        "name": "Log Deleter",
        "version": 4,
        "size": 2,
        "type": SoftwareType.LOG_TOOLS,
        "price": 6000,
    },
    {
        "name": "Trace Tracker",
        "version": 1,
        "size": 1,
        "type": SoftwareType.LOG_TOOLS,
        "price": 0,
    },
    {
        "name": "Trace Tracker",
        "version": 2,
        "size": 1,
        "type": SoftwareType.LOG_TOOLS,
        "price": 1500,
    },
    {
        "name": "Trace Tracker",
        "version": 3,
        "size": 2,
        "type": SoftwareType.LOG_TOOLS,
        "price": 4000,
    },
    {
        "name": "Log UnDeleter",
        "version": 1,
        "size": 1,
        "type": SoftwareType.LOG_TOOLS,
        "price": 2000,
    },
    {
        "name": "Decrypter",
        "version": 1,
        "size": 2,
        "type": SoftwareType.CRACKERS,
        "price": 2500,
    },
    {
        "name": "Decrypter",
        "version": 1,
        "size": 2,
        "type": SoftwareType.CRACKERS,
        "price": 2500,
    },
    {
        "name": "Decrypter",
        "version": 2,
        "size": 2,
        "type": SoftwareType.CRACKERS,
        "price": 6000,
    },
    {
        "name": "Decrypter",
        "version": 3,
        "size": 3,
        "type": SoftwareType.CRACKERS,
        "price": 12000,
    },
    {
        "name": "Decrypter",
        "version": 4,
        "size": 4,
        "type": SoftwareType.CRACKERS,
        "price": 25000,
    },
    {
        "name": "Proxy Bypass",
        "version": 1,
        "size": 2,
        "type": SoftwareType.BYPASSERS,
        "price": 5000,
    },
    {
        "name": "Proxy Bypass",
        "version": 2,
        "size": 3,
        "type": SoftwareType.BYPASSERS,
        "price": 15000,
    },
    {
        "name": "Firewall Bypass",
        "version": 1,
        "size": 2,
        "type": SoftwareType.BYPASSERS,
        "price": 5500,
    },
    {
        "name": "Firewall Bypass",
        "version": 2,
        "size": 3,
        "type": SoftwareType.BYPASSERS,
        "price": 16000,
    },

    {
        "name": "Firewall Disable",
        "version": 1,
        "size": 2,
        "type": SoftwareType.BYPASSERS,
        "price": 3500,
    },
    {
        "name": "Firewall Bypass",
        "version": 1,
        "size": 2,
        "type": SoftwareType.BYPASSERS,
        "price": 5500,
    },
    {
        "name": "Monitor Bypass",
        "version": 1,
        "size": 2,
        "type": SoftwareType.BYPASSERS,
        "price": 4000,
    },
    {
        "name": "HUD_ConnectionAnalysis",
        "version": 1,
        "size": 2,
        "type": SoftwareType.HUD_UPGRADE,
        "price": 3000,
    },
    {
        "name": "HUD_MapShowTrace",
        "version": 1,
        "size": 1,
        "type": SoftwareType.HUD_UPGRADE,
        "price": 2000,
    },
    {
        "name": "HUD_LANView",
        "version": 1,
        "size": 2,
        "type": SoftwareType.HUD_UPGRADE,
        "price": 8000,
    },
    {
        "name": "Voice Analyser",
        "version": 1,
        "size": 2,
        "type": SoftwareType.OTHER,
        "price": 5000,
    },
    {
        "name": "IP Probe",
        "version": 1,
        "size": 1,
        "type": SoftwareType.OTHER,
        "price": 1000,
    },
    {
        "name": "IP Lookup",
        "version": 1,
        "size": 1,
        "type": SoftwareType.OTHER,
        "price": 500,
    },
    {
        "name": "Defrag",
        "version": 1,
        "size": 1,
        "type": SoftwareType.OTHER,
        "price": 500,
    },
    {
        "name": "Log Modifier",
        "version": 1,
        "size": 2,
        "type": SoftwareType.LOG_TOOLS,
        "price": 3000,
    },
    {
        "name": "Log Modifier",
        "version": 2,
        "size": 2,
        "type": SoftwareType.LOG_TOOLS,
        "price": 7000,
    },
    {
        "name": "Self Destruct",
        "price": 4000,
        "is_hardware_addon": True,
        "size": 0,
        "type": SoftwareType.NONE,
        "version": 1,
    },
    {
        "name": "Motion Sensor",
        "price": 2000,
        "is_hardware_addon": True,
        "size": 0,
        "type": SoftwareType.NONE,
        "version": 1,
    },
    # Application executables (free, unlock apps)
    {
        "name": "Map",
        "version": 1,
        "size": 1,
        "type": SoftwareType.OTHER,
        "price": 0,
        "is_exe": True,
        "exe_name": "map.exe",
    },
    {
        "name": "Finance",
        "version": 1,
        "size": 1,
        "type": SoftwareType.OTHER,
        "price": 0,
        "is_exe": True,
        "exe_name": "finance.exe",
    },
    {
        "name": "Missions",
        "version": 1,
        "size": 1,
        "type": SoftwareType.OTHER,
        "price": 0,
        "is_exe": True,
        "exe_name": "missions.exe",
    },
    {
        "name": "News",
        "version": 1,
        "size": 1,
        "type": SoftwareType.OTHER,
        "price": 0,
        "is_exe": True,
        "exe_name": "news.exe",
    },
    {
        "name": "Rankings",
        "version": 1,
        "size": 1,
        "type": SoftwareType.OTHER,
        "price": 0,
        "is_exe": True,
        "exe_name": "rankings.exe",
    },
    {
        "name": "Company",
        "version": 1,
        "size": 1,
        "type": SoftwareType.OTHER,
        "price": 0,
        "is_exe": True,
        "exe_name": "company.exe",
    },
    {
        "name": "Logistics",
        "version": 1,
        "size": 1,
        "type": SoftwareType.OTHER,
        "price": 0,
        "is_exe": True,
        "exe_name": "logistics.exe",
    },
    {
        "name": "Memory Banks",
        "version": 1,
        "size": 1,
        "type": SoftwareType.OTHER,
        "price": 0,
        "is_exe": True,
        "exe_name": "memory_banks.exe",
    },
    {
        "name": "Tutorial",
        "version": 1,
        "size": 1,
        "type": SoftwareType.OTHER,
        "price": 0,
        "is_exe": True,
        "exe_name": "tutorial.exe",
    },
]


# ======================================================================
# Queries
# ======================================================================
def get_hardware_catalog() -> list[dict]:
    return HARDWARE_CATALOG


def get_software_catalog() -> list[dict]:
    return [s for s in SOFTWARE_CATALOG if not s.get("is_hardware_addon")]


def get_addon_catalog() -> list[dict]:
    return [s for s in SOFTWARE_CATALOG if s.get("is_hardware_addon")]


def get_cooling_catalog() -> list[dict]:
    return COOLING_CATALOG


def get_psu_catalog() -> list[dict]:
    return PSU_CATALOG


# ======================================================================
# Purchases
# ======================================================================
def buy_software(state: GameState, software_name: str, version: int = 1) -> dict:
    """Purchase software and add it to the player's VFS."""
    item = next(
        (
            s
            for s in SOFTWARE_CATALOG
            if s["name"] == software_name
            and s.get("version", 1) == version
            and not s.get("is_hardware_addon")
        ),
        None,
    )
    if item is None:
        return {"success": False, "error": "Software not found in catalog"}

    if state.player.balance < item["price"]:
        return {"success": False, "error": "Insufficient funds"}

    size = item.get("size", 1)
    if state.vfs.free_gq < size:
        return {"success": False, "error": "Insufficient memory"}

    state.player.balance -= item["price"]

    # Remove old version if present
    state.vfs.files = [
        f
        for f in state.vfs.files
        if not (software_name.lower() in f.filename.lower() and f.version < version)
    ]

    # .exe files get their exe_name as filename, others get "Name v1.0"
    if item.get("is_exe"):
        filename = item["exe_name"]
    else:
        filename = f"{software_name} v{version}.0"

    state.vfs.files.append(
        VFSFile(
            filename=filename,
            size_gq=size,
            file_type=2,
            software_type=item["type"],
            version=version,
        )
    )

    log.info("Purchased %s v%d for %dc", software_name, version, item["price"])
    return {
        "success": True,
        "item": software_name,
        "version": version,
        "cost": item["price"],
    }


def buy_gateway(state: GameState, gateway_name: str) -> dict:
    """Upgrade to a new gateway."""
    gw_spec = next((g for g in HARDWARE_CATALOG if g["name"] == gateway_name), None)
    if gw_spec is None:
        return {"success": False, "error": "Gateway not found"}

    # Part exchange: old gateway value
    current = next(
        (g for g in HARDWARE_CATALOG if g["name"] == state.gateway.name), None
    )
    trade_in = int(current["price"] * 0.5) if current else 0
    net_cost = max(0, gw_spec["price"] - trade_in)

    if state.player.balance < net_cost:
        return {
            "success": False,
            "error": f"Need {net_cost}c (after {trade_in}c trade-in)",
        }

    from core.game_state import CPUCore

    state.player.balance -= net_cost
    state.gateway.name = gw_spec["name"]
    # Replace CPUs but preserve the number of slots
    num_cpus = len(state.gateway.cpus)
    state.gateway.cpus = [
        CPUCore(
            id=i + 1,
            model=gw_spec["name"],
            base_speed=gw_spec["cpu"],
            speed=gw_spec["cpu"],
        )
        for i in range(num_cpus)
    ]
    state.gateway.modem_speed = gw_spec["modem"]
    state.gateway.memory_gq = gw_spec["memory"] // 4 # Basic heuristic: 1/4 of total is RAM
    state.gateway.storage_gq = gw_spec["memory"]
    state.gateway.psu_capacity = gw_spec["psu"]
    state.gateway.cooling_power = gw_spec["cooling"]
    state.vfs.total_memory_gq = gw_spec["memory"]

    log.info(
        "Upgraded to %s (cost %dc, trade-in %dc)", gateway_name, net_cost, trade_in
    )
    return {
        "success": True,
        "gateway": gateway_name,
        "cost": net_cost,
        "trade_in": trade_in,
    }


def buy_cooling(state: GameState, cooling_name: str) -> dict:
    """Upgrade cooling system."""
    item = next((c for c in COOLING_CATALOG if c["name"] == cooling_name), None)
    if item is None:
        return {"success": False, "error": "Cooling system not found"}

    if state.player.balance < item["price"]:
        return {"success": False, "error": "Insufficient funds"}

    state.player.balance -= item["price"]
    state.gateway.cooling_power = item["cooling"]

    return {"success": True, "cooling": cooling_name, "cost": item["price"]}


def buy_psu(state: GameState, psu_name: str) -> dict:
    """Upgrade power supply."""
    item = next((p for p in PSU_CATALOG if p["name"] == psu_name), None)
    if item is None:
        return {"success": False, "error": "PSU not found"}

    if state.player.balance < item["price"]:
        return {"success": False, "error": "Insufficient funds"}

    state.player.balance -= item["price"]
    state.gateway.psu_capacity = item["psu"]

    return {"success": True, "psu": psu_name, "cost": item["price"]}


def buy_addon(state: GameState, addon_name: str) -> dict:
    """Purchase a hardware addon."""
    item = next(
        (
            s
            for s in SOFTWARE_CATALOG
            if s["name"] == addon_name and s.get("is_hardware_addon")
        ),
        None,
    )
    if item is None:
        return {"success": False, "error": "Addon not found"}

    if state.player.balance < item["price"]:
        return {"success": False, "error": "Insufficient funds"}

    state.player.balance -= item["price"]

    if addon_name == "Self Destruct":
        state.gateway.has_self_destruct = True
    elif addon_name == "Motion Sensor":
        state.gateway.has_motion_sensor = True

    return {"success": True, "addon": addon_name, "cost": item["price"]}

def buy_cpu(state: GameState, cpu_index: int, model: str) -> dict:
    """Purchase an individual CPU upgrade for a specific slot."""
    # Find model in constants.HARDWARE_UPGRADES
    from core.constants import HARDWARE_UPGRADES
    spec = next((s for s in HARDWARE_UPGRADES if s[0] == model and s[1] == 1), None)
    if not spec:
        return {"success": False, "error": "CPU model not found"}

    cost, speed = spec[2], spec[4]
    if state.player.balance < cost:
        return {"success": False, "error": "Insufficient funds"}

    if cpu_index < 0 or cpu_index >= state.gateway.cpu_slots:
        return {"success": False, "error": "Invalid CPU slot"}

    state.player.balance -= cost
    from core.game_state import CPUCore
    # Replace or update the CPU in that slot
    new_cpu = CPUCore(id=cpu_index+1, model=model, base_speed=speed, speed=speed)
    if cpu_index < len(state.gateway.cpus):
        state.gateway.cpus[cpu_index] = new_cpu
    else:
        state.gateway.cpus.append(new_cpu)

    return {"success": True, "cpu": model, "cost": cost}

def buy_modem(state: GameState, model: str) -> dict:
    """Purchase a modem upgrade."""
    from core.constants import HARDWARE_UPGRADES
    spec = next((s for s in HARDWARE_UPGRADES if s[0] == model and s[1] == 2), None)
    if not spec:
        return {"success": False, "error": "Modem model not found"}

    cost, speed = spec[2], spec[4]
    if state.player.balance < cost:
        return {"success": False, "error": "Insufficient funds"}

    state.player.balance -= cost
    state.gateway.modem_speed = speed
    return {"success": True, "modem": model, "cost": cost}

def buy_memory(state: GameState, model: str) -> dict:
    """Purchase a memory (GQ) upgrade."""
    from core.constants import HARDWARE_UPGRADES
    spec = next((s for s in HARDWARE_UPGRADES if s[0] == model and s[1] == 4), None)
    if not spec:
        return {"success": False, "error": "Memory model not found"}

    cost, amount = spec[2], spec[4]
    if state.player.balance < cost:
        return {"success": False, "error": "Insufficient funds"}

    state.player.balance -= cost
    state.gateway.memory_gq = amount
    return {"success": True, "memory": model, "cost": cost}
