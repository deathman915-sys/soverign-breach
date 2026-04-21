"""
Onlink-Clone: Plot Engine

Manages the three Uplink story arcs (Revelation, Faith, ARC).
Ported from the ajhenley fork — simplified for initial release.
"""
from __future__ import annotations

import logging
from core.game_state import GameState, Message

log = logging.getLogger(__name__)

# Plot states
PLOT_IDLE = 0
PLOT_REVELATION_ACT1 = 1
PLOT_REVELATION_ACT2 = 2
PLOT_REVELATION_ACT3 = 3
PLOT_FAITH_INTRO = 10
PLOT_ARC_INTRO = 20


def check_plot_triggers(state: GameState) -> list[dict]:
    """Check for plot progression triggers. Called periodically."""
    events = []

    # Revelation storyline triggered at rating 5+
    if state.player.uplink_rating >= 5 and state.plot_state == PLOT_IDLE:
        state.plot_state = PLOT_REVELATION_ACT1
        state.messages.append(Message(
            id=state.next_message_id,
            from_name="INTERNAL",
            subject="Special Assignment",
            body=(
                "Agent,\n\n"
                "Uplink Corporation has identified a situation requiring "
                "an experienced operative. Details to follow.\n\n"
                "This message will self-destruct.\n\n"
                "- Uplink Internal Services"
            ),
            created_at_tick=state.clock.tick_count,
        ))
        state.next_message_id += 1
        events.append({
            "type": "plot_advance",
            "plot": "revelation",
            "act": 1,
        })

    # More plot progression would follow
    # (ARC, Faith storylines, etc.)

    return events


def get_plot_state(state: GameState) -> dict:
    """Return current plot progression info."""
    return {
        "state": state.plot_state,
        "description": _describe_state(state.plot_state),
    }


def _describe_state(plot_state: int) -> str:
    descriptions = {
        PLOT_IDLE: "No active storyline",
        PLOT_REVELATION_ACT1: "Revelation: Act 1 — Initial contact",
        PLOT_REVELATION_ACT2: "Revelation: Act 2 — Investigation",
        PLOT_REVELATION_ACT3: "Revelation: Act 3 — Climax",
        PLOT_FAITH_INTRO: "Faith storyline introduced",
        PLOT_ARC_INTRO: "ARC storyline introduced",
    }
    return descriptions.get(plot_state, "Unknown")
