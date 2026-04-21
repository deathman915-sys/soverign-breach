"""
Onlink-Clone: Bank Robbery Event

When the player makes an illegal money transfer, a timer starts (default 120 ticks).
If the relevant logs aren't deleted before the timer expires, the player is caught
and the game ends.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.game_state import GameState

log = logging.getLogger(__name__)

# Default timer in ticks (120 seconds at 1 tick/sec)
ROBBERY_TIMER_TICKS = 120


def record_illegal_transfer(
    state: GameState, bank_ip: str, account: str, amount: int
) -> None:
    """Record an illegal transfer and start the robbery timer."""
    if not hasattr(state, "_robbery_timers"):
        state._robbery_timers = []

    state._robbery_timers.append(
        {
            "bank_ip": bank_ip,
            "account": account,
            "amount": amount,
            "ticks_remaining": ROBBERY_TIMER_TICKS,
            "warned_at": ROBBERY_TIMER_TICKS // 2,  # Warn at halfway point
        }
    )
    log.info(f"Bank robbery timer started: {bank_ip} account {account} amount {amount}")


def tick_robbery_timers(state: GameState, ticks: int) -> list[dict]:
    """Advance robbery timers. Returns events when timers expire or warn."""
    events = []
    if not hasattr(state, "_robbery_timers"):
        return events

    remaining = []
    for timer in state._robbery_timers:
        timer["ticks_remaining"] -= ticks

        if timer["ticks_remaining"] <= 0:
            events.append(
                {
                    "type": "bank_robbery_caught",
                    "message": f"CAUGHT! Illegal transfer of {timer['amount']}c from {timer['bank_ip']} detected!",
                    "bank_ip": timer["bank_ip"],
                    "amount": timer["amount"],
                    "game_over": True,
                }
            )
        elif timer["ticks_remaining"] <= timer.get("warned_at", 60):
            events.append(
                {
                    "type": "bank_robbery_warning",
                    "message": f"WARNING: The bank at {timer['bank_ip']} is investigating the transfer of {timer['amount']}c. Delete the logs!",
                    "bank_ip": timer["bank_ip"],
                    "ticks_left": timer["ticks_remaining"],
                }
            )
            timer["warned_at"] = -1  # Only warn once
        else:
            remaining.append(timer)

    state._robbery_timers = remaining
    return events


def clear_robbery_logs(state: GameState) -> None:
    """
    Check if all relevant bank logs have been deleted.
    If so, clear the robbery timers.
    """
    if not hasattr(state, "_robbery_timers"):
        return

    remaining = []
    for timer in state._robbery_timers:
        bank = state.computers.get(timer["bank_ip"])
        is_cleared = False
        if bank:
            # Check if all transfer-related logs are deleted
            transfer_logs = [
                log_entry
                for log_entry in bank.logs
                if "transfer" in log_entry.subject.lower() or "transaction" in log_entry.subject.lower()
            ]
            if transfer_logs and all(log_entry.is_deleted for log_entry in transfer_logs):
                is_cleared = True
                log.info(f"Bank robbery timer cleared: {timer['bank_ip']}")
        
        if not is_cleared:
            remaining.append(timer)
            
    state._robbery_timers = remaining

def get_active_robbery(state: GameState) -> dict | None:
    """Returns the most urgent robbery timer or None."""
    if not hasattr(state, "_robbery_timers") or not state._robbery_timers:
        return None
    # Return the one with least ticks remaining
    return min(state._robbery_timers, key=lambda t: t["ticks_remaining"])
