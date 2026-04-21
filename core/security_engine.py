"""
Onlink-Clone: Security Engine

Detects security breaches and triggers traces on connected computers.
Ported from the ajhenley fork — all SQLAlchemy replaced with GameState ops.
"""
from __future__ import annotations

import logging
import random
import string
from core.game_state import GameState
from core import trace_engine

log = logging.getLogger(__name__)


def check_security_breaches(state: GameState) -> list[dict]:
    """
    Check if the player's active connection triggers security alerts.
    Called periodically (every ~40 ticks).
    """
    conn = state.connection
    if not conn.is_active or conn.target_ip is None:
        return []

    target = state.computers.get(conn.target_ip)
    if target is None:
        return []

    events = []

    # Check each active security system
    for sec in target.security_systems:
        if not sec.is_active:
            continue

        # Security monitor (type 3) — triggers trace
        if sec.security_type == 3 and not conn.trace_active:
            log.info("Security monitor detected breach on %s", target.name)
            trace_engine.start_trace(state)
            events.append({
                "type": "security_breach",
                "target_ip": conn.target_ip,
                "computer_name": target.name,
                "security_type": sec.security_type,
                "level": sec.level,
            })

    return events


def recover_compromised_systems(state: GameState):
    """
    Background process to re-enable bypassed security and rotate passwords.
    Called periodically by the main engine.
    """
    current_tick = state.clock.tick_count
    recovered_ips = []

    # recovery thresholds (ticks)
    SEC_RECOVERY_TIME = 300   # ~5 mins at 1Hz
    PW_RECOVERY_TIME = 10000  # ~2.7 hours at 1Hz

    for ip, hacked_tick in state.compromised_ips.items():
        comp = state.computers.get(ip)
        if not comp:
            recovered_ips.append(ip)
            continue

        ticks_elapsed = current_tick - hacked_tick
        
        # 1. Re-enable security systems
        if ticks_elapsed >= SEC_RECOVERY_TIME:
            for sec in comp.security_systems:
                if not sec.is_active:
                    sec.is_active = True
                    log.info(f"System Recovery: Security re-enabled on {comp.name} ({ip})")

        # 2. Rotate Admin Passwords
        if ticks_elapsed >= PW_RECOVERY_TIME:
            if "admin" in comp.accounts:
                new_pw = _generate_random_password()
                comp.accounts["admin"] = new_pw
                log.info(f"System Recovery: Admin password rotated on {comp.name} ({ip})")
            
            # Remove from tracking once password is changed
            recovered_ips.append(ip)

    for ip in recovered_ips:
        if ip in state.compromised_ips:
            del state.compromised_ips[ip]


def _generate_random_password(length: int = 8) -> str:
    """Helper to generate a fresh password."""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))
