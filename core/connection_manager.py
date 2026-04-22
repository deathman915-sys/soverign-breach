"""
Onlink-Clone: Connection Manager

Manages bounce chains, active connections, and screen navigation.
Ported from the ajhenley fork — all SQLAlchemy replaced with GameState ops.
"""

from __future__ import annotations

import logging

from core import trace_engine
from core.game_state import (
    AccessLog,
    Computer,
    Connection,
    ConnectionNode,
    GameState,
)

log = logging.getLogger(__name__)


def connect(
    state: GameState, target_ip: str, bounce_ips: list[str] | None = None
) -> dict:
    """
    Establish a connection to target_ip through optional bounce chain.
    If bounce_ips is None, uses state.bounce.hops automatically.
    """
    if target_ip not in state.computers:
        return {"error": f"Unknown IP: {target_ip}", "success": False}

    target = state.computers[target_ip]

    # Use bounce chain from state if not explicitly provided
    if bounce_ips is None:
        bounce_ips = list(state.bounce.hops)

    # Remove localhost from front if present (it's implicit)
    if bounce_ips and bounce_ips[0] == state.player.localhost_ip:
        bounce_ips = bounce_ips[1:]

    # Remove target IP from bounce chain (shouldn't bounce through itself)
    bounce_ips = [ip for ip in bounce_ips if ip != target_ip]

    # Build bounce nodes
    nodes = []
    for i, ip in enumerate(bounce_ips):
        if ip in state.computers:
            nodes.append(ConnectionNode(position=i, ip=ip))

    # Add target as final node
    nodes.append(ConnectionNode(position=len(nodes), ip=target_ip))

    state.connection = Connection(
        target_ip=target_ip,
        is_active=True,
        trace_progress=0.0,
        trace_active=False,
        nodes=nodes,
    )

    # IP Auto-Discovery: Permanently add target to known_ips
    if target_ip not in state.player.known_ips:
        state.player.known_ips.append(target_ip)
        from core import persistence
        persistence.save_profile(state)

    # --- MVP Heist: Multi-hop log chain ---
    # Log 1: Target Server logs the previous hop (the last Proxy)
    previous_hop_ip = nodes[-2].ip if len(nodes) > 1 else state.player.localhost_ip
    target.add_log(
        AccessLog(
            log_time=str(state.clock.tick_count),
            from_ip=previous_hop_ip,
            from_name="External Connection",
            subject="Connection Established",
            log_type=1,
        )
    )

    # Log the rest of the chain backwards
    # Proxy logs InterNIC, InterNIC logs Localhost
    for i in range(len(nodes) - 2, -1, -1):
        current_node_ip = nodes[i].ip
        prev_node_ip = nodes[i - 1].ip if i > 0 else state.player.localhost_ip

        comp = state.computers.get(current_node_ip)
        if comp:
            comp.add_log(
                AccessLog(
                    log_time=str(state.clock.tick_count),
                    from_ip=prev_node_ip,
                    from_name="Routing Connection",
                    subject="Connection Bounced",
                    log_type=1,
                )
            )

    log.info(
        "Connected to %s (%s) via %d bounces", target.name, target_ip, len(nodes) - 1
    )

    return {
        "success": True,
        "target_ip": target_ip,
        "target_name": target.name,
        "bounce_count": len(nodes) - 1,
        "screens": _get_screen_list(target),
    }


def disconnect(state: GameState) -> dict:
    """Disconnect from current target and reset all temporary security bypasses."""
    conn = state.connection
    if not conn.is_active:
        return {"success": False, "error": "Not connected"}

    # Reset all bypasses in the world (Uplink/Onlink behavior: bypasses are unstable)
    for comp in state.computers.values():
        for sec in comp.security_systems:
            sec.is_bypassed = False

    old_target = conn.target_ip
    trace_engine.reset_trace(state)
    state.connection = Connection()

    log.info("Disconnected from %s and all bypasses reset", old_target)
    return {"success": True, "disconnected_from": old_target}


def get_screen(state: GameState, screen_index: int) -> dict | None:
    """Get screen data for the currently connected computer."""
    conn = state.connection
    if not conn.is_active or conn.target_ip is None:
        return None

    computer = state.computers.get(conn.target_ip)
    if computer is None:
        return None

    if 0 <= screen_index < len(computer.screens):
        scr = computer.screens[screen_index]
        return {
            "screen_type": scr.screen_type,
            "next_page": scr.next_page,
            "sub_page": scr.sub_page,
            "data1": scr.data1,
            "data2": scr.data2,
            "data3": scr.data3,
        }
    return None


def attempt_password(state: GameState, username: str, password: str) -> dict:
    """Try a password on the connected computer's password screen using the new Login System."""
    conn = state.connection
    if not conn.is_active or conn.target_ip is None:
        return {"success": False, "error": "Not connected"}

    computer = state.computers.get(conn.target_ip)
    if computer is None:
        return {"success": False, "error": "Computer not found"}

    # Use the accounts dictionary for validation if available
    if computer.accounts:
        if username in computer.accounts and computer.accounts[username] == password:
            # Log successful authentication
            prev_hop = state.player.localhost_ip
            if conn.nodes and len(conn.nodes) > 1:
                prev_hop = conn.nodes[-2].ip
            computer.add_log(
                AccessLog(
                    log_time=str(state.clock.tick_count),
                    from_ip=prev_hop,
                    from_name="External Connection",
                    subject="authentication accepted",
                    log_type=1,
                )
            )
            return {"success": True, "message": "Access granted"}
        else:
            return {"success": False, "error": "Access denied"}

    # Fallback for old simple data1 check
    for scr in computer.screens:
        if scr.screen_type in (1, 20):  # PASSWORD / HIGH_SECURITY screens
            if scr.data1 and scr.data1 == password:
                # Log successful authentication
                prev_hop = state.player.localhost_ip
                if conn.nodes and len(conn.nodes) > 1:
                    prev_hop = conn.nodes[-2].ip
                computer.logs.append(
                    AccessLog(
                        log_time=str(state.clock.tick_count),
                        from_ip=prev_hop,
                        from_name="External Connection",
                        subject="authentication accepted",
                        log_type=1,
                    )
                )
                return {
                    "success": True,
                    "next_page": scr.next_page,
                    "message": "Access granted",
                }

    return {"success": False, "error": "Access denied"}


def get_file_list(state: GameState) -> list[dict]:
    """Get files on the currently connected computer."""
    conn = state.connection
    if not conn.is_active or conn.target_ip is None:
        return []

    computer = state.computers.get(conn.target_ip)
    if computer is None:
        return []

    return [
        {
            "filename": f.filename,
            "size": f.size,
            "file_type": f.file_type,
            "encrypted_level": f.encrypted_level,
            "owner": f.owner,
        }
        for f in computer.files
    ]


def get_log_list(state: GameState) -> list[dict]:
    """Get access logs on the currently connected computer."""
    conn = state.connection
    if not conn.is_active or conn.target_ip is None:
        return []

    computer = state.computers.get(conn.target_ip)
    if computer is None:
        return []

    return [
        {
            "index": i,
            "log_time": log_entry.log_time,
            "from_ip": log_entry.from_ip,
            "from_name": log_entry.from_name,
            "subject": log_entry.subject,
            "is_visible": log_entry.is_visible,
            "is_deleted": log_entry.is_deleted,
        }
        for i, log_entry in enumerate(computer.logs)
        if log_entry.is_visible and not log_entry.is_deleted
    ]


def _get_screen_list(computer: Computer) -> list[dict]:
    return [
        {"index": i, "screen_type": s.screen_type}
        for i, s in enumerate(computer.screens)
    ]
