"""
Onlink-Clone: LAN Engine

Handles LAN-based mission phases (scanning, probing, spoofing, forcing).
Ported from the ajhenley fork — simplified for initial release.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field

from core.game_state import GameState

log = logging.getLogger(__name__)


@dataclass
class LANNode:
    """A node in a computer's internal LAN."""

    id: int = 0
    node_type: str = "router"  # router, terminal, server, mainframe, lock
    ip_suffix: str = ".1"
    is_compromised: bool = False
    connections: list[int] = field(default_factory=list)
    data: dict = field(default_factory=dict)


@dataclass
class LANState:
    """State of a LAN scan on a target computer."""

    target_ip: str = ""
    is_active: bool = False
    nodes: list[LANNode] = field(default_factory=list)
    discovered: set[int] = field(default_factory=set)


# Store per-connection LAN state
_lan_states: dict[str, LANState] = {}


def start_lan_scan(state: GameState, target_ip: str) -> dict:
    """Begin a LAN scan on the target computer."""
    computer = state.computers.get(target_ip)
    if computer is None:
        return {"success": False, "error": "Computer not found"}

    rng = random.Random()

    # Generate a random LAN topology
    num_nodes = rng.randint(3, 8)
    nodes = []
    for i in range(num_nodes):
        node_types = ["router", "terminal", "server", "lock"]
        weights = [0.3, 0.3, 0.2, 0.2]
        node = LANNode(
            id=i,
            node_type=rng.choices(node_types, weights=weights, k=1)[0],
            ip_suffix=f".{i + 1}",
        )
        # Connect to previous nodes
        if i > 0:
            node.connections.append(rng.randint(0, i - 1))
            nodes[node.connections[0]].connections.append(i)
        nodes.append(node)

    # First node is always the router (entry point)
    nodes[0].node_type = "router"
    # Last node is the target
    nodes[-1].node_type = "mainframe"

    lan_state = LANState(
        target_ip=target_ip,
        is_active=True,
        nodes=nodes,
        discovered={0},  # Router is discovered by default
    )
    _lan_states[target_ip] = lan_state

    return {
        "success": True,
        "nodes_count": num_nodes,
        "discovered": [_node_dict(nodes[0])],
    }


def probe_node(target_ip: str, node_id: int) -> dict:
    """Probe a LAN node to discover connected nodes."""
    lan = _lan_states.get(target_ip)
    if lan is None or not lan.is_active:
        return {"success": False, "error": "No active LAN scan"}

    if node_id >= len(lan.nodes) or node_id not in lan.discovered:
        return {"success": False, "error": "Node not accessible"}

    node = lan.nodes[node_id]
    newly_discovered = []
    for conn_id in node.connections:
        if conn_id not in lan.discovered:
            lan.discovered.add(conn_id)
            newly_discovered.append(_node_dict(lan.nodes[conn_id]))

    return {
        "success": True,
        "node": _node_dict(node),
        "discovered": newly_discovered,
    }


def spoof_node(target_ip: str, node_id: int) -> dict:
    """Compromise a LAN node."""
    lan = _lan_states.get(target_ip)
    if lan is None or not lan.is_active:
        return {"success": False, "error": "No active LAN scan"}

    if node_id >= len(lan.nodes) or node_id not in lan.discovered:
        return {"success": False, "error": "Node not accessible"}

    node = lan.nodes[node_id]
    node.is_compromised = True

    return {"success": True, "node": _node_dict(node)}


def get_lan_state(state: GameState, target_ip: str | None = None) -> dict | None:
    """Get current LAN scan state for a target, or all active scans."""
    if target_ip:
        lan = _lan_states.get(target_ip)
        if lan is None:
            return None
        return {
            "target_ip": lan.target_ip,
            "is_active": lan.is_active,
            "nodes": [_node_dict(n) for n in lan.nodes if n.id in lan.discovered],
            "total_nodes": len(lan.nodes),
            "discovered": len(lan.discovered),
        }
    # Return all active scans
    return {
        ip: {
            "target_ip": lan.target_ip,
            "is_active": lan.is_active,
            "discovered": len(lan.discovered),
            "total_nodes": len(lan.nodes),
        }
        for ip, lan in _lan_states.items()
    }


def cleanup_lan(target_ip: str) -> None:
    """Clean up LAN state on disconnect."""
    _lan_states.pop(target_ip, None)


def reset_lan_states() -> None:
    """Reset all LAN states (for new games)."""
    _lan_states.clear()


def _node_dict(node: LANNode) -> dict:
    return {
        "id": node.id,
        "type": node.node_type,
        "ip_suffix": node.ip_suffix,
        "compromised": node.is_compromised,
        "connections": node.connections,
    }
