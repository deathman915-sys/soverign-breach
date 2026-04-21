"""
Onlink-Clone: Neuromancer Rating

Secondary "dark side" rating that tracks the moral alignment of the player's actions.
Increases for destructive/creative actions, decreases for tracing/framing users.
11 levels from Revolutionary (most evil) to Neutral (most good).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.game_state import GameState

# Neuromancer rating levels (matching Uplink)
NEUROMANCER_LEVELS = {
    -100: "Revolutionary",
    -80: "Anarchic",
    -60: "Activist",
    -40: "Single Minded",
    -20: "Aggressive",
    0: "Neutral",
    20: "Defensive",
    40: "Protective",
    60: "Guardian",
    80: "Sentinel",
    100: "Paragon",
}

# Action modifiers
ACTION_MODIFIERS = {
    "steal_file": 2,
    "delete_data": 3,
    "change_academic": 1,
    "change_criminal": -5,
    "change_ssn": -3,
    "change_medical": -4,
    "trace_user": -8,
    "frame_user": -15,
    "remove_computer": 5,
    "complete_mission": 1,
    "get_caught": -10,
}


def adjust_neuromancer(state: GameState, action: str, magnitude: int = 1) -> int:
    """
    Adjust the player's neuromancer rating based on an action.
    Returns the new rating.
    """
    modifier = ACTION_MODIFIERS.get(action, 0) * magnitude
    state.player.neuromancer_rating = max(
        -100, min(100, state.player.neuromancer_rating + modifier)
    )
    return state.player.neuromancer_rating


def get_neuromancer_level(state: GameState) -> str:
    """Get the named level for the current neuromancer rating."""
    rating = state.player.neuromancer_rating
    for threshold in sorted(NEUROMANCER_LEVELS.keys(), reverse=True):
        if rating >= threshold:
            return NEUROMANCER_LEVELS[threshold]
    return NEUROMANCER_LEVELS[-100]
