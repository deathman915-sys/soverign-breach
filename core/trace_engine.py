"""
Onlink-Clone: Trace Engine

Advances trace progress through the player's connection.
Ported from the ajhenley fork — all SQLAlchemy replaced with GameState ops.
"""

from __future__ import annotations

import logging
from core.game_state import GameState

log = logging.getLogger(__name__)


def calculate_trace_speed(state: GameState, target_ip: str) -> float:
    """
    Calculate the effective trace speed for a target based on access level.
    In Uplink:
    - No account: 0.1x (very slow trace, gives player time)
    - Known password: 0.7x
    - Admin access: 1.0x (normal)
    - Bank admin: 1.6x (banks trace fast)
    """
    target = state.computers.get(target_ip)
    if not target:
        return 10.0

    base_speed = target.trace_speed if target.trace_speed > 0 else 10.0

    # Check access level
    has_known_password = target_ip in state.player.known_passwords
    has_admin = False
    is_bank = False

    if target.accounts:
        has_admin = "admin" in target.accounts
        # Check if this is a bank (has bank accounts)
        is_bank = any(a.bank_ip == target_ip for a in state.bank_accounts)

    if is_bank and has_admin:
        return base_speed * 1.6
    elif has_admin and has_known_password:
        return base_speed * 1.0
    elif has_known_password:
        return base_speed * 0.7
    else:
        return base_speed * 0.1


def tick_traces(state: GameState, speed: float) -> list[dict]:
    """Advance trace on the active connection. Returns update dicts."""
    conn = state.connection
    if not conn.is_active or not conn.trace_active:
        return []

    # Advance trace through bounce nodes
    if not conn.nodes:
        return []

    # Find the current node being traced
    total_nodes = len(conn.nodes)
    trace_per_node = 1.0 / max(1, total_nodes)

    # Look up the target computer for trace speed
    effective_speed = calculate_trace_speed(state, conn.target_ip)

    # Advance
    increment = speed / (effective_speed * total_nodes)
    conn.trace_progress = min(1.0, conn.trace_progress + increment)

    # Mark traced nodes
    traced_count = int(conn.trace_progress / trace_per_node)
    for i, node in enumerate(conn.nodes):
        node.is_traced = i < traced_count

    return [
        {
            "progress": conn.trace_progress,
            "active": conn.trace_active,
            "traced_nodes": [{"ip": n.ip, "traced": n.is_traced} for n in conn.nodes],
        }
    ]


def check_completed_traces(state: GameState) -> list[dict]:
    """Check if any trace has reached the player. Returns completion dicts."""
    conn = state.connection
    if not conn.is_active or not conn.trace_active:
        return []

    if conn.trace_progress >= 1.0:
        return [{"traced": True, "target_ip": conn.target_ip}]

    return []


def start_trace(state: GameState) -> None:
    """Activate tracing on the current connection."""
    conn = state.connection
    if conn.is_active:
        conn.trace_active = True
        conn.trace_progress = 0.0


def reset_trace(state: GameState) -> None:
    """Reset trace state (e.g., on disconnect)."""
    conn = state.connection
    conn.trace_active = False
    conn.trace_progress = 0.0
    for node in conn.nodes:
        node.is_traced = False
