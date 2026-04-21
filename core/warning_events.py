"""
Onlink-Clone: Warning Events

When log suspicion reaches HIGH level, the player receives a warning
that authorities are investigating. Gives a window to delete logs
before the trace completes and game over occurs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.game_state import GameState

# Track which logs have already triggered warnings
_warned_logs: set = set()


def check_warnings(state: GameState) -> list[dict]:
    """
    Check all logs for HIGH suspicion levels and emit warnings.
    Each log only triggers one warning.
    """
    events = []

    for comp in state.computers.values():
        for log_entry in comp.logs:
            if log_entry.is_deleted:
                continue

            log_id = f"{comp.ip}:{id(log_entry)}"
            if log_id in _warned_logs:
                continue

            if log_entry.suspicion_level >= 3:  # Under Investigation
                _warned_logs.add(log_id)
                events.append(
                    {
                        "type": "warning",
                        "message": f"WARNING: {comp.name} is investigating suspicious activity from your connection!",
                        "computer": comp.name,
                        "computer_ip": comp.ip,
                        "log_subject": log_entry.subject,
                        "urgency": "high",
                    }
                )

    return events


def reset_warnings() -> None:
    """Reset warning state (for new games)."""
    _warned_logs.clear()
