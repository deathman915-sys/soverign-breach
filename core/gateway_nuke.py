"""
Onlink-Clone: Gateway Nuke (Self-Destruct)

Emergency self-destruct for the player's gateway.
Destroys all files, crashes the system, and ends the game.
In Uplink, this is a last resort when about to be traced.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.game_state import GameState


def nuke_gateway(state: GameState) -> dict:
    """
    Self-destruct the player's gateway.
    Requires the Self Destruct addon to be installed.
    Destroys all VFS files, melts the gateway, and triggers game over.
    """
    if not state.gateway.has_self_destruct:
        return {
            "success": False,
            "error": "Self Destruct addon not installed. Purchase from Upgrades.",
        }

    # Destroy all files
    state.vfs.files.clear()

    # Melt the gateway
    state.gateway.is_melted = True
    state.gateway.heat = 200.0
    state.gateway.storage_health = 0.0
    state.gateway.ram_health = 0.0
    for cpu in state.gateway.cpus:
        cpu.health = 0.0

    # Clear any active tasks
    state.tasks.clear()

    # Disconnect
    state.connection.is_active = False
    state.connection.target_ip = None

    return {
        "success": True,
        "game_over": True,
        "reason": "Gateway self-destructed. All data lost.",
    }
