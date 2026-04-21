"""
Onlink-Clone: Log Suspicion Escalation

In Uplink, access logs escalate through suspicion levels over time:
NOTSUSPICIOUS -> SUSPICIOUS -> SUSPICIOUSANDNOTICED -> UNDERINVESTIGATION

Authentication logs escalate faster than regular connection logs.
Deleted logs stop escalating.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.game_state import GameState


# Suspicion levels
SUSPICION_NONE = 0
SUSPICION_LOW = 1
SUSPICION_MEDIUM = 2
SUSPICION_HIGH = 3

SUSPICION_NAMES = {
    SUSPICION_NONE: "Not Suspicious",
    SUSPICION_LOW: "Suspicious",
    SUSPICION_MEDIUM: "Suspicious and Noticed",
    SUSPICION_HIGH: "Under Investigation",
}

# Ticks to reach each suspicion level
ESCALATION_TICKS = {
    SUSPICION_NONE: 0,
    SUSPICION_LOW: 200,
    SUSPICION_MEDIUM: 800,
    SUSPICION_HIGH: 2000,
}

# Multiplier for auth logs (escalate faster)
AUTH_LOG_MULTIPLIER = 2.0


def escalate_suspicion(state: GameState, ticks: int) -> list[dict]:
    """
    Escalate suspicion levels on all non-deleted logs across all computers.
    Returns list of events when logs reach new suspicion thresholds.
    """
    events = []

    for comp in state.computers.values():
        for log_entry in comp.logs:
            if log_entry.is_deleted:
                continue

            old_level = log_entry.suspicion_level

            # Determine escalation rate
            multiplier = 1.0
            if "authentication" in log_entry.subject.lower():
                multiplier = AUTH_LOG_MULTIPLIER
            elif "routed" in log_entry.subject.lower():
                multiplier = 0.5  # Connection logs escalate slower

            # Financial Forensics Penalty:
            # If player has 'hot' funds, everything escalates faster.
            # Max penalty: 2x speed at 1.0 hot_ratio.
            hot_penalty = 1.0 + getattr(state, "_hot_ratio", 0.0)
            multiplier *= hot_penalty

            effective_ticks = ticks * multiplier

            # Calculate new suspicion level based on total suspicious ticks
            total_ticks = getattr(log_entry, "_suspicious_ticks", 0) + effective_ticks
            log_entry._suspicious_ticks = total_ticks

            new_level = SUSPICION_NONE
            for level, threshold in sorted(ESCALATION_TICKS.items()):
                if total_ticks >= threshold:
                    new_level = level

            log_entry.suspicion_level = new_level

            if new_level > old_level:
                events.append(
                    {
                        "type": "suspicion_escalation",
                        "computer": comp.name,
                        "computer_ip": comp.ip,
                        "log_subject": log_entry.subject,
                        "old_level": SUSPICION_NAMES.get(old_level, "Unknown"),
                        "new_level": SUSPICION_NAMES.get(new_level, "Unknown"),
                        "level": new_level,
                    }
                )

    return events
