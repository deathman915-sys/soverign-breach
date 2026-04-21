"""
Onlink-Clone: NPC & Investigation Engine

Handles the simulation of rival agents and government forensic investigators.
Scans internal logs for crimes and initiates passive traceback sequences.
"""

from __future__ import annotations
import logging
import random
from core.game_state import GameState, AccessLog, PassiveTrace, Computer, NodeType

log = logging.getLogger(__name__)

def process_npc_investigations(state: GameState, ticks: float):
    """
    Simulates government agencies scanning their internal logs.
    If a crime is found, starts a PassiveTrace backwards.
    """
    for ip, comp in state.computers.items():
        if comp.computer_type in (NodeType.BANK, NodeType.GOVERNMENT, NodeType.INTERNAL_SRV):
            _scan_for_crimes(state, comp)

def _scan_for_crimes(state: GameState, comp: Computer):
    """NPCs scan the public logs for evidence of hacking."""
    # 0.5% chance per tick to find a crime in logs (once per ~200 ticks per server)
    if random.random() > 0.005:
        return

    for log_entry in comp.logs:
        if log_entry.suspicion_level >= 2 and not _is_already_traced(state, log_entry):
            # FOUND A CRIME! Start a passive trace from this node
            _start_investigation(state, comp.ip, log_entry)

def _is_already_traced(state: GameState, log_entry: AccessLog) -> bool:
    return any(t.target_ip == log_entry.from_ip for t in state.passive_traces if t.is_active)

def _start_investigation(state: GameState, start_node_ip: str, log_entry: AccessLog):
    """Starts a forensic trail hop-by-hop."""
    log.info(f"FORENSICS: Investigation started on {start_node_ip} targeting {log_entry.from_ip}")
    
    trace = PassiveTrace(
        trace_id=state.next_trace_id,
        current_node_ip=start_node_ip,
        target_ip=log_entry.from_ip,
        ticks_until_next_hop=random.randint(300, 600), # Passive traces are slow
        is_active=True
    )
    state.passive_traces.append(trace)
    state.next_trace_id += 1

def tick_npcs(state: GameState, ticks: float) -> list[dict]:
    """Advices NPC state machines."""
    # Placeholder for NPC mission logic
    return []

def get_rankings(state: GameState) -> list[dict]:
    """Returns agent rankings including the player."""
    rankings = []
    # Add Player
    rankings.append({"name": state.player.handle, "rating": state.player.uplink_rating, "is_player": True})
    # Add NPC Agents
    for p in state.world.people:
        if p.is_agent:
            rankings.append({"name": p.name, "rating": p.uplink_rating, "is_player": False})
    
    # Sort by rating descending
    rankings.sort(key=lambda x: x["rating"], reverse=True)
    return rankings
