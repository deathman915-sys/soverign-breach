"""
Onlink-Clone: Task Engine

Processes hacking tool ticks — starting, advancing, and completing tasks.
Ported from the ajhenley fork. All SQLAlchemy replaced with GameState ops.

Supports 17+ tool types: Password_Breaker, Dictionary_Hacker, File_Copier,
File_Deleter, Log_Deleter, Log_UnDeleter, Trace_Tracker, Decrypter,
Firewall_Disable, Firewall_Bypass, Proxy_Disable, Proxy_Bypass,
Monitor_Bypass, Log_Modifier, IP_Probe, IP_Lookup, LAN tools, HUD tools,
Voice_Analyser, Defrag, Decypher.
"""

from __future__ import annotations

import json
import logging
import random as _random

from core import constants as C
from core import finance_engine
from core.game_state import (
    Computer,
    GameState,
    NodeType,
    RunningTask,
    SoftwareType,
    VFSFile,
)

log = logging.getLogger(__name__)

BASE_CPU_SPEED = 60


# ======================================================================
# Helpers
# ======================================================================
def _get_cpu_speed(state: GameState) -> int:
    return state.gateway.cpu_speed or BASE_CPU_SPEED


def _resolve_computer(state: GameState, ip: str) -> Computer | None:
    return state.computers.get(ip)


def _player_has_software(state: GameState, software_name: str) -> bool:
    return any(software_name.lower() in f.filename.lower() for f in state.vfs.files)


def _task_dict(
    task: RunningTask, *, completed: bool = False, extra: dict | None = None
) -> dict:
    return {
        "completed": completed,
        "data": {
            "task_id": task.task_id,
            "tool_name": task.tool_name,
            "tool_version": task.tool_version,
            "progress": task.progress,
            "ticks_remaining": task.ticks_remaining,
            "target_ip": task.target_ip,
            "extra": extra or {},
        },
    }


# ======================================================================
# Start a task - Handlers
# ======================================================================
def _start_password_breaker(
    state: GameState, tool_name: str, tool_version: int, target_ip: str, td: dict, cpu_mod: float
) -> tuple[float, dict]:
    computer = _resolve_computer(state, target_ip)
    if computer is None:
        raise ValueError(f"No computer found at IP {target_ip}")
    password = td.get("password", "")
    if not password:
        username = td.get("target_id", "admin")
        if computer.accounts and username in computer.accounts:
            password = computer.accounts[username]
        else:
            # Get password from the computer's first password screen
            for scr in computer.screens:
                if scr.screen_type in (
                    C.SCREEN_PASSWORDSCREEN,
                    C.SCREEN_HIGHSECURITYSCREEN,
                ):
                    password = scr.data1 or ""
                    break
        if not password:
            raise ValueError("No password to crack on this computer")
    ticks_remaining = computer.hack_difficulty * len(password) * cpu_mod
    ticks_per_char = computer.hack_difficulty * cpu_mod
    new_td = {
        "password": password,
        "revealed": "",
        "char_index": 0,
        "ticks_per_char": ticks_per_char,
        "ticks_into_char": 0.0,
    }
    return ticks_remaining, new_td


def _start_dictionary_hacker(
    state: GameState, tool_name: str, tool_version: int, target_ip: str, td: dict, cpu_mod: float
) -> tuple[float, dict]:
    computer = _resolve_computer(state, target_ip)
    if computer is None:
        raise ValueError(f"No computer found at IP {target_ip}")
    password = td.get("password", "")
    if not password:
        for scr in computer.screens:
            if scr.screen_type in (
                C.SCREEN_PASSWORDSCREEN,
                C.SCREEN_HIGHSECURITYSCREEN,
            ):
                password = scr.data1 or ""
                break
    ticks_remaining = C.TICKSREQUIRED_DICTIONARYHACKER * 10000 * cpu_mod
    new_td = {"password": password, "found": False}
    return ticks_remaining, new_td


def _start_file_tool(
    state: GameState, tool_name: str, tool_version: int, target_ip: str, td: dict, cpu_mod: float
) -> tuple[float, dict]:
    file_name = td.get("filename")
    if file_name is None:
        raise ValueError(f"{tool_name} requires target_data.filename")
    computer = _resolve_computer(state, target_ip)
    if computer is None:
        raise ValueError(f"No computer found at IP {target_ip}")
    data_file = next((f for f in computer.files if f.filename == file_name), None)
    if data_file is None:
        raise ValueError(f"File '{file_name}' not found on {target_ip}")

    base_ticks = (
        C.TICKSREQUIRED_COPY if tool_name == "File_Copier" else C.TICKSREQUIRED_DELETE
    )
    ticks_remaining = base_ticks * data_file.size * cpu_mod
    new_td = {"filename": file_name, "target_ip": target_ip}
    return ticks_remaining, new_td


def _start_log_deleter(
    state: GameState, tool_name: str, tool_version: int, target_ip: str, td: dict, cpu_mod: float
) -> tuple[float, dict]:
    ticks_remaining = C.TICKSREQUIRED_LOGDELETER * cpu_mod
    return ticks_remaining, {"log_index": td.get("log_index")}


def _start_trace_tracker(
    state: GameState, tool_name: str, tool_version: int, target_ip: str, td: dict, cpu_mod: float
) -> tuple[float, dict]:
    return -1.0, td


def _start_log_undeleter(
    state: GameState, tool_name: str, tool_version: int, target_ip: str, td: dict, cpu_mod: float
) -> tuple[float, dict]:
    ticks_remaining = (C.TICKSREQUIRED_LOGUNDELETER * cpu_mod) / max(1, tool_version)
    return ticks_remaining, {"log_index": td.get("log_index")}


def _start_generic_tool(
    state: GameState, tool_name: str, tool_version: int, target_ip: str, td: dict, cpu_mod: float
) -> tuple[float, dict]:
    base_ticks_map = {
        "Decrypter": C.TICKSREQUIRED_DECRYPT,
        "Firewall_Disable": C.TICKSREQUIRED_DISABLEFIREWALL,
        "Firewall_Bypass": C.TICKSREQUIRED_ANALYSEFIREWALL,
        "Proxy_Disable": C.TICKSREQUIRED_DISABLEPROXY,
        "Proxy_Bypass": C.TICKSREQUIRED_ANALYSEPROXY,
        "Monitor_Bypass": 50,
        "Log_Modifier": C.TICKSREQUIRED_LOGMODIFIER,
        "IP_Probe": 30,
        "IP_Lookup": 10,
        "Voice_Analyser": 120,
        "Decypher": 80,
    }
    base_ticks = base_ticks_map.get(tool_name, 0)

    if tool_name == "IP_Lookup":
        ticks_remaining = base_ticks * cpu_mod
    else:
        ticks_remaining = (base_ticks * cpu_mod) / max(1, tool_version)

    if tool_name == "Log_Modifier":
        new_td = {
            "log_index": td.get("log_index"),
            "new_from_ip": td.get("new_from_ip"),
            "new_subject": td.get("new_subject"),
        }
        return ticks_remaining, new_td

    return ticks_remaining, td


def _start_lan_tool(
    state: GameState, tool_name: str, tool_version: int, target_ip: str, td: dict, cpu_mod: float
) -> tuple[float, dict]:
    base_ticks = {
        "LAN_Scan": C.TICKSREQUIRED_LANSCAN,
        "LAN_Probe": C.TICKSREQUIRED_SCANLANSYSTEM,
        "LAN_Spoof": C.TICKSREQUIRED_SPOOFLANSYSTEM,
        "LAN_Force": C.TICKSREQUIRED_FORCELANLOCK,
    }.get(tool_name, 0)
    ticks_remaining = base_ticks * cpu_mod / max(1, tool_version)
    return ticks_remaining, td


def _start_defrag(
    state: GameState, tool_name: str, tool_version: int, target_ip: str, td: dict, cpu_mod: float
) -> tuple[float, dict]:
    ticks_remaining = C.TICKSREQUIRED_DEFRAG * 24 * cpu_mod
    return ticks_remaining, td


def _start_hud_tool(
    state: GameState, tool_name: str, tool_version: int, target_ip: str, td: dict, cpu_mod: float
) -> tuple[float, dict]:
    return -1.0, td


# ======================================================================
# Start a task
# ======================================================================
def start_task(
    state: GameState,
    tool_name: str,
    tool_version: int,
    target_ip: str,
    target_data: dict | None = None,
) -> dict:
    """Create a new RunningTask and return its initial state dict."""
    td = target_data or {}

    cpu_speed = _get_cpu_speed(state)
    cpu_modifier = float(BASE_CPU_SPEED) / cpu_speed

    # HUD gating
    BYPASS_TOOLS = {"Firewall_Bypass", "Proxy_Bypass", "Monitor_Bypass"}
    LAN_TOOLS = {"LAN_Scan", "LAN_Probe", "LAN_Spoof", "LAN_Force"}

    if tool_name in BYPASS_TOOLS:
        if not _player_has_software(state, "HUD_ConnectionAnalysis"):
            raise ValueError("Bypass tools require HUD: Connection Analysis software")

    if tool_name in LAN_TOOLS:
        if not _player_has_software(state, "HUD_LANView"):
            raise ValueError("LAN tools require HUD: LAN View software")

    # Tool Registry
    registry = {
        "Password_Breaker": _start_password_breaker,
        "Dictionary_Hacker": _start_dictionary_hacker,
        "File_Copier": _start_file_tool,
        "File_Deleter": _start_file_tool,
        "Log_Deleter": _start_log_deleter,
        "Trace_Tracker": _start_trace_tracker,
        "Log_UnDeleter": _start_log_undeleter,
        "Decrypter": _start_generic_tool,
        "Firewall_Disable": _start_generic_tool,
        "Firewall_Bypass": _start_generic_tool,
        "Proxy_Disable": _start_generic_tool,
        "Proxy_Bypass": _start_generic_tool,
        "Monitor_Bypass": _start_generic_tool,
        "Log_Modifier": _start_generic_tool,
        "IP_Probe": _start_generic_tool,
        "IP_Lookup": _start_generic_tool,
        "Voice_Analyser": _start_generic_tool,
        "Decypher": _start_generic_tool,
        "LAN_Scan": _start_lan_tool,
        "LAN_Probe": _start_lan_tool,
        "LAN_Spoof": _start_lan_tool,
        "LAN_Force": _start_lan_tool,
        "Defrag": _start_defrag,
        "HUD_ConnectionAnalysis": _start_hud_tool,
        "HUD_IRC-Client": _start_hud_tool,
        "HUD_MapShowTrace": _start_hud_tool,
        "HUD_LANView": _start_hud_tool,
    }

    handler = registry.get(tool_name)
    if not handler:
        raise ValueError(f"Unknown tool: {tool_name}")

    ticks_remaining, td = handler(state, tool_name, tool_version, target_ip, td, cpu_modifier)

    task = RunningTask(
        task_id=state.next_task_id,
        tool_name=tool_name,
        tool_version=tool_version,
        target_ip=target_ip,
        target_data=json.dumps(td),
        progress=0.0,
        ticks_remaining=ticks_remaining,
        is_active=True,
    )
    # Store initial ticks for progress calculation
    task.extra["initial_ticks"] = ticks_remaining

    state.next_task_id += 1
    state.tasks.append(task)

    extra = _build_extra(task, td)
    return _task_dict(task, completed=False, extra=extra)["data"]


# ======================================================================
# Tick a task
# ======================================================================
def tick_task(state: GameState, task: RunningTask, speed: float) -> dict:
    """Advance task by speed ticks and return an update dict."""
    td = json.loads(task.target_data or "{}")

    if task.tool_name == "Trace_Tracker":
        return _tick_trace_tracker(state, task, td)

    # HUD tools run indefinitely
    if task.ticks_remaining < 0:
        return _task_dict(task, completed=False, extra=_build_extra(task, td))

    task.ticks_remaining = max(0.0, task.ticks_remaining - speed)

    # Update progress based on initial_ticks
    total_ticks = _initial_ticks(task, td)
    if total_ticks > 0:
        # progress is (total - remaining) / total
        task.progress = round(min(1.0, 1.0 - task.ticks_remaining / total_ticks), 4)
    else:
        task.progress = 1.0

    is_complete = task.ticks_remaining <= 0

    if task.tool_name == "Password_Breaker":
        td, is_complete = _tick_password_breaker(td, speed, is_complete)
        task.target_data = json.dumps(td)
    elif task.tool_name == "Dictionary_Hacker":
        td, is_complete = _tick_dictionary_hacker(td, speed, is_complete)
        task.target_data = json.dumps(td)

    if is_complete:
        if task.tool_name == "Password_Breaker":
            _complete_password_breaker(state, task, td)
        elif task.tool_name == "File_Copier":
            _complete_file_copier(state, task, td)
        elif task.tool_name == "File_Deleter":
            _complete_file_deleter(state, task, td)
        elif task.tool_name == "Log_Deleter":
            _complete_log_deleter(state, task, td)
        elif task.tool_name == "Monitor_Bypass":
            _complete_security_bypass(state, task, security_type=C.SEC_TYPE_MONITOR)
        elif task.tool_name == "Firewall_Bypass":
            _complete_security_bypass(state, task, security_type=C.SEC_TYPE_FIREWALL)
        elif task.tool_name == "Proxy_Bypass":
            _complete_security_bypass(state, task, security_type=C.SEC_TYPE_PROXY)
        elif task.tool_name == "Decypher":
            _complete_security_bypass(state, task, security_type=C.SEC_TYPE_ENCRYPTER)
        elif task.tool_name == "Firewall_Disable":
            _complete_security_disable(state, task, security_type=C.SEC_TYPE_FIREWALL)
        elif task.tool_name == "Proxy_Disable":
            _complete_security_disable(state, task, security_type=C.SEC_TYPE_PROXY)
        elif task.tool_name == "Dictionary_Hacker":
            _complete_dictionary_hacker(state, task, td)
        elif task.tool_name == "Log_UnDeleter":
            _complete_log_undeleter(state, task, td)
        elif task.tool_name == "Log_Modifier":
            _complete_log_modifier(state, task, td)

        task.is_active = False
        task.progress = 1.0
        task.ticks_remaining = 0

    extra = _build_extra(task, td)
    return _task_dict(task, completed=is_complete, extra=extra)


def stop_task(state: GameState, task_id: int) -> dict:
    """Manually stop a running task."""
    for i, task in enumerate(state.tasks):
        if task.task_id == task_id:
            task.is_active = False
            state.tasks.pop(i)
            return {"success": True, "task_id": task_id, "tool": task.tool_name}
    return {"success": False, "error": "Task not found"}


# ======================================================================
# Internal tick/completion helpers
# ======================================================================
def _initial_ticks(task: RunningTask, td: dict) -> float:
    if "initial_ticks" in task.extra:
        return task.extra["initial_ticks"]
    if task.tool_name == "Password_Breaker":
        password = td.get("password", "")
        ticks_per_char = td.get("ticks_per_char", 1)
        return ticks_per_char * len(password)
    if 0 < task.progress < 1.0:
        return task.ticks_remaining / (1.0 - task.progress)
    return task.ticks_remaining


def _tick_password_breaker(
    td: dict, speed: float, would_complete: bool
) -> tuple[dict, bool]:
    password = td.get("password", "")
    ticks_per_char = td.get("ticks_per_char", 1)
    char_index = td.get("char_index", 0)
    ticks_into_char = td.get("ticks_into_char", 0.0)

    ticks_into_char += speed
    while ticks_into_char >= ticks_per_char and char_index < len(password):
        ticks_into_char -= ticks_per_char
        char_index += 1

    td["revealed"] = password[:char_index]
    td["char_index"] = char_index
    td["ticks_into_char"] = ticks_into_char

    is_complete = char_index >= len(password)
    if is_complete:
        td["revealed"] = password
    return td, is_complete


def _tick_dictionary_hacker(
    td: dict, speed: float, would_complete: bool
) -> tuple[dict, bool]:
    # Visual feedback: random characters that reveal over time
    password = td.get("password", "")
    if not password:
        return td, would_complete

    revealed = td.get("revealed", "")
    if len(revealed) < len(password):
        # Just show some random noise until completed
        import string
        noise = "".join(_random.choice(string.ascii_letters) for _ in range(len(password)))
        td["revealed"] = noise

    return td, would_complete


def _tick_trace_tracker(state: GameState, task: RunningTask, td: dict) -> dict:
    conn = state.connection
    extra = {
        "trace_progress": conn.trace_progress,
        "trace_active": conn.trace_active,
    }
    return _task_dict(task, completed=False, extra=extra)


def _complete_password_breaker(state: GameState, task: RunningTask, td: dict) -> None:
    password = td.get("password", "")
    if password:
        state.player.known_passwords[task.target_ip] = password


def _complete_file_copier(state: GameState, task: RunningTask, td: dict) -> None:
    filename = td.get("filename")
    src_ip = td.get("target_ip", task.target_ip)
    if filename is None:
        return
    computer = state.computers.get(src_ip)
    if computer is None:
        return
    source_file = next((f for f in computer.files if f.filename == filename), None)
    if source_file is None:
        return
    # Copy to player's VFS
    copied = VFSFile(
        filename=source_file.filename,
        size_gq=source_file.size,
        file_type=source_file.file_type,
        software_type=SoftwareType(source_file.softwaretype)
        if source_file.softwaretype
        else SoftwareType.NONE,
        encrypted_level=source_file.encrypted_level,
        data=source_file.data or "",
    )
    if state.vfs.free_gq >= copied.size_gq:
        state.vfs.files.append(copied)

        # Uplink Stock Logic: Research Theft
        if filename in ("research_data.dat", "corporate_secrets.dat"):
            finance_engine.trigger_stock_crash(state, computer.company_name, "research_stolen")


def _complete_file_deleter(state: GameState, task: RunningTask, td: dict) -> None:
    filename = td.get("filename")
    src_ip = td.get("target_ip", task.target_ip)
    if filename is None:
        return
    computer = state.computers.get(src_ip)
    if computer is None:
        return
    computer.files = [f for f in computer.files if f.filename != filename]

    # Uplink Stock Logic: Mainframe Destruction (Formatting)
    if not computer.files and computer.computer_type == NodeType.INTERNAL_SRV:
        finance_engine.trigger_stock_crash(state, computer.company_name, "mainframe_destroyed")


def _complete_log_deleter(state: GameState, task: RunningTask, td: dict) -> None:
    computer = state.computers.get(task.target_ip)
    if computer is None:
        return

    version = task.tool_version
    log_index = td.get("log_index")

    # NOTE: We ONLY modify computer.logs (public).
    # computer.internal_logs remains as forensic backup.

    if version == 1:
        # Delete oldest visible log
        for log_entry in computer.logs:
            if log_entry.is_visible and not log_entry.is_deleted:
                log_entry.is_deleted = True
                break
    elif version == 2:
        # Delete specific log
        if (
            log_index is not None
            and isinstance(log_index, int)
            and 0 <= log_index < len(computer.logs)
        ):
            computer.logs[log_index].is_deleted = True
    elif version == 3:
        # Delete all visible logs
        for log_entry in computer.logs:
            if log_entry.is_visible and not log_entry.is_deleted:
                log_entry.is_deleted = True
    elif version >= 4:
        # Purge all public logs
        for log_entry in computer.logs:
            log_entry.is_deleted = True
            log_entry.is_visible = False
        # v4+ ALSO purges internal logs (forensic trail)
        for log_entry in computer.internal_logs:
            log_entry.is_deleted = True


def _complete_log_undeleter(state: GameState, task: RunningTask, td: dict) -> None:
    computer = state.computers.get(task.target_ip)
    if computer is None:
        return

    log_index = td.get("log_index")

    if (
        log_index is not None
        and isinstance(log_index, int)
        and 0 <= log_index < len(computer.logs)
    ):
        # Restore the log by setting is_deleted back to False
        computer.logs[log_index].is_deleted = False


def _complete_security_disable(
    state: GameState, task: RunningTask, security_type: int
) -> None:
    computer = state.computers.get(task.target_ip)
    if computer is None:
        return
    for sec in computer.security_systems:
        if sec.security_type == security_type:
            sec.is_active = False


def _complete_security_bypass(
    state: GameState, task: RunningTask, security_type: int
) -> None:
    computer = state.computers.get(task.target_ip)
    if computer is None:
        return
    for sec in computer.security_systems:
        if sec.security_type == security_type:
            sec.is_bypassed = True


def _complete_dictionary_hacker(state: GameState, task: RunningTask, td: dict) -> None:
    password = td.get("password", "")
    if _random.random() < 0.7:
        td["found"] = True
        td["revealed"] = password
        if password:
            state.player.known_passwords[task.target_ip] = password
    else:
        td["found"] = False
        td["revealed"] = ""
    task.target_data = json.dumps(td)


def _complete_log_modifier(state: GameState, task: RunningTask, td: dict) -> None:
    computer = state.computers.get(task.target_ip)
    if computer is None:
        return

    log_index = td.get("log_index")
    new_from_ip = td.get("new_from_ip")
    new_subject = td.get("new_subject")

    if (
        log_index is not None
        and isinstance(log_index, int)
        and 0 <= log_index < len(computer.logs)
    ):
        target_log = computer.logs[log_index]
        if new_from_ip:
            target_log.from_ip = new_from_ip
        if new_subject:
            target_log.subject = new_subject
        # Framing is suspicious
        target_log.suspicion_level = max(target_log.suspicion_level, 1)


# ======================================================================
# Extra data builder for UI display
# ======================================================================
def _build_extra(task: RunningTask, td: dict) -> dict:
    if task.tool_name == "Dictionary_Hacker":
        return {"found": td.get("found", False), "revealed": td.get("revealed", "")}
    if task.tool_name == "Password_Breaker":
        password = td.get("password", "")
        revealed = td.get("revealed", "")
        display = revealed + "_" * (len(password) - len(revealed))
        return {"revealed": display}
    if task.tool_name == "Trace_Tracker":
        return {
            "trace_progress": td.get("trace_progress", 0.0),
            "trace_active": td.get("trace_active", False),
        }
    return {}
