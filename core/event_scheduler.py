"""
Onlink-Clone: Event Scheduler

Manages delayed consequences — warnings, fines, arrests.
Ported from the ajhenley fork — all SQLAlchemy replaced with GameState ops.
"""
from __future__ import annotations

import json
import logging
import random

from core import constants as C
from core.game_state import GameState, Message, PersonStatus, ScheduledEvent

log = logging.getLogger(__name__)

# Event types
EVENT_WARNING = "warning"
EVENT_FINE = "fine"
EVENT_ARREST = "arrest"
EVENT_SUBSCRIPTION = "subscription_fee"
EVENT_MISSION_GENERATE = "mission_generate"


def schedule_event(state: GameState, event_type: str, trigger_tick: int,
                   data: dict | None = None) -> ScheduledEvent:
    """Schedule a new event to trigger at a specific tick."""
    event = ScheduledEvent(
        id=state.next_event_id,
        event_type=event_type,
        trigger_tick=trigger_tick,
        data=json.dumps(data or {}),
    )
    state.next_event_id += 1
    state.scheduled_events.append(event)
    return event


def schedule_trace_consequences(state: GameState, computer_name: str,
                                 current_tick: int, hack_difficulty: float = 0.0) -> None:
    """Schedule escalating consequences after being traced."""
    # Warning first (immediate-ish)
    schedule_event(state, EVENT_WARNING, current_tick + 50, {
        "computer_name": computer_name,
        "message": f"Warning: Your activities on {computer_name} have been logged.",
    })

    # Fine based on difficulty
    fine_amount = int(max(500, hack_difficulty * 20))
    schedule_event(state, EVENT_FINE, current_tick + 500, {
        "computer_name": computer_name,
        "amount": fine_amount,
    })

    # Arrest if high difficulty
    if hack_difficulty >= 100:
        schedule_event(state, EVENT_ARREST, current_tick + 2000, {
            "computer_name": computer_name,
        })


def schedule_initial_events(state: GameState, start_tick: int) -> None:
    """Schedule recurring events at game start."""
    # Uplink subscription fee
    schedule_event(state, EVENT_SUBSCRIPTION, start_tick + 5000, {
        "amount": 300,
        "recurring_interval": 5000,
    })

    # Periodic mission generation
    schedule_event(state, EVENT_MISSION_GENERATE, start_tick + 1000, {
        "count": 3,
        "recurring_interval": 2000,
    })


def trigger_arrest(state: GameState, reason: str = "Investigation Complete") -> dict:
    """Immediately arrests the player, wipes gateway, and pauses simulation.
    Returns event dict for UI handling.
    """
    log.warning(f"ARREST TRIGGERED: {reason}")
    p = state.player
    gw = state.gateway

    p.status = PersonStatus.ARRESTED
    p.is_arrested = True
    p.arrest_count += 1

    # Fine: percentage of current balance
    p.balance = int(p.balance * C.ARREST_BALANCE_SEIZURE_PERCENT)
    # Reset rating
    p.uplink_rating = C.ARREST_RATING_RESET_TO
    # Credit rating penalty
    p.credit_rating = max(1, p.credit_rating - C.ARREST_CREDIT_RATING_PENALTY)
    # Neuromancer drift toward neutral
    if p.neuromancer_rating > 0:
        p.neuromancer_rating = max(0, p.neuromancer_rating - C.ARREST_NEUROMANCER_TOWARD_NEUTRAL)
    elif p.neuromancer_rating < 0:
        p.neuromancer_rating = min(0, p.neuromancer_rating + C.ARREST_NEUROMANCER_TOWARD_NEUTRAL)
    # Jail sentence
    p.jail_sentence_ticks = random.randint(C.ARREST_JAIL_TICKS_MIN, C.ARREST_JAIL_TICKS_MAX)

    # Calculate bail amount based on jail time
    calculated_bail = p.jail_sentence_ticks * C.BAIL_RATE_PER_TICK
    p.bail_amount = max(C.BAIL_MINIMUM, min(C.BAIL_MAXIMUM, calculated_bail))

    # Generate arrest news article
    from core.news_engine import add_news
    add_news(state, "arrest", agent_name=p.handle)

    # Check for disavow threshold
    if p.arrest_count >= C.ARREST_MAX_COUNT_BEFORE_DISAVOWED:
        p.status = PersonStatus.DISAVOWED
        p.disavow_countdown_ticks = C.DISAVOW_PROFILE_DELETE_TICKS
        log.warning(f"PLAYER DISAVOWED after {p.arrest_count} arrests. Profile scheduled for deletion.")

    # Wipe Gateway
    state.vfs.files = []
    gw.heat = 25.0
    gw.is_melted = False
    for cpu in gw.cpus:
        cpu.health = 100.0
        cpu.overclock = 1.0

    # Pause simulation
    state.clock.speed_multiplier = 0

    # Clear active tasks/connections
    state.tasks = []
    state.connection.is_active = False
    state.connection.target_ip = None

    # Save arrested state
    from core import persistence
    persistence.save_profile(state)

    return {
        "type": "arrest" if p.status == PersonStatus.ARRESTED else "disavowed",
        "reason": reason,
        "jail_ticks": p.jail_sentence_ticks,
        "bail_amount": p.bail_amount,
        "balance_remaining": p.balance,
        "arrest_count": p.arrest_count,
    }

def process_jail_time(state: GameState, ticks: float = 1.0) -> dict | None:
    """Decrements jail sentence and disavow countdown.
    Returns event dict if profile should be deleted, None otherwise.
    """
    p = state.player
    if not p.is_arrested:
        return None

    p.jail_sentence_ticks = max(0, p.jail_sentence_ticks - int(ticks))

    # Handle disavow countdown (starts when jail time finishes)
    if p.jail_sentence_ticks <= 0 and p.status == PersonStatus.DISAVOWED:
        p.disavow_countdown_ticks = max(0, p.disavow_countdown_ticks - int(ticks))
        if p.disavow_countdown_ticks <= 0:
            log.warning("DISAVOW COUNTDOWN EXPIRED. Deleting profile.")
            from core import persistence
            persistence.delete_profile(p.handle)
            return {"type": "profile_deleted"}
        return {"type": "disavow_countdown", "ticks_left": p.disavow_countdown_ticks}

    # Handle jail release (non-disavowed players)
    if p.jail_sentence_ticks <= 0 and p.status == PersonStatus.ARRESTED:
        p.is_arrested = False
        p.status = PersonStatus.NONE
        log.info("Player released from jail.")
        return {"type": "released"}

    return None

def pay_bail(state: GameState) -> dict:
    """Player pays bail to reduce jail time or disavow countdown.
    Returns success/failure dict with details.
    """
    p = state.player
    if not p.is_arrested:
        return {"success": False, "error": "Not currently arrested"}
    if p.bail_amount <= 0:
        return {"success": False, "error": "Bail already paid or not available"}
    if p.balance < p.bail_amount:
        return {"success": False, "error": f"Insufficient funds. Need {p.bail_amount}c, have {p.balance}c"}

    # Deduct bail amount
    p.balance -= p.bail_amount

    if p.status == PersonStatus.DISAVOWED:
        # Reduce disavow countdown by percentage
        reduction = int(p.disavow_countdown_ticks * C.BAIL_DISAVOW_REDUCTION_PERCENT)
        p.disavow_countdown_ticks = max(0, p.disavow_countdown_ticks - reduction)
        log.info(f"Bail paid: disavow countdown reduced by {reduction} ticks")
        return {
            "success": True,
            "bail_paid": p.bail_amount,
            "countdown_reduced": reduction,
            "countdown_remaining": p.disavow_countdown_ticks,
        }
    else:
        # Reduce jail time by percentage
        reduction = int(p.jail_sentence_ticks * C.BAIL_JAIL_REDUCTION_PERCENT)
        p.jail_sentence_ticks = max(0, p.jail_sentence_ticks - reduction)
        paid_amount = p.bail_amount
        p.bail_amount = 0  # Bail can only be paid once per arrest
        log.info(f"Bail paid: jail time reduced by {reduction} ticks")
        return {
            "success": True,
            "bail_paid": paid_amount,
            "jail_reduced": reduction,
            "jail_remaining": p.jail_sentence_ticks,
        }

def process_events(state: GameState, current_tick: int) -> list[dict]:
    """Process all events whose trigger_tick has passed."""
    messages = []
    still_pending = []

    for event in state.scheduled_events:
        if event.is_processed:
            continue

        if current_tick >= event.trigger_tick:
            event.is_processed = True
            data = json.loads(event.data or "{}")
            result = _handle_event(state, event.event_type, data, current_tick)
            if result:
                messages.append(result)
        else:
            still_pending.append(event)

    # Keep only unprocessed events
    state.scheduled_events = [e for e in state.scheduled_events if not e.is_processed]

    return messages


def _handle_event(state: GameState, event_type: str, data: dict,
                  current_tick: int) -> dict | None:
    """Handle a triggered event."""

    if event_type == EVENT_WARNING:
        msg_text = data.get("message", "You have received a warning.")
        state.messages.append(Message(
            id=state.next_message_id,
            from_name="Federal Bureau of Investigation",
            subject="Security Warning",
            body=msg_text,
            created_at_tick=current_tick,
        ))
        state.next_message_id += 1
        return {"type": "warning", "message": msg_text}

    elif event_type == EVENT_FINE:
        amount = data.get("amount", 500)
        state.player.balance = max(0, state.player.balance - amount)
        comp_name = data.get("computer_name", "a system")

        state.messages.append(Message(
            id=state.next_message_id,
            from_name="Uplink Corporation",
            subject=f"Fine: {amount}c",
            body=(
                f"A fine of {amount}c has been deducted from your account "
                f"for unauthorized access to {comp_name}."
            ),
            created_at_tick=current_tick,
        ))
        state.next_message_id += 1
        return {"type": "fine", "amount": amount}

    elif event_type == EVENT_ARREST:
        comp_name = data.get("computer_name", "a system")
        trigger_arrest(state, reason=f"Hacking {comp_name}")

        state.messages.append(Message(
            id=state.next_message_id,
            from_name="Global Criminal Database",
            subject="Arrest",
            body=f"You have been arrested for hacking {comp_name}.",
            created_at_tick=current_tick,
        ))
        state.next_message_id += 1
        return {"type": "game_over", "reason": f"Arrested for hacking {comp_name}"}

    elif event_type == EVENT_SUBSCRIPTION:
        amount = data.get("amount", 300)
        state.player.balance = max(0, state.player.balance - amount)

        state.messages.append(Message(
            id=state.next_message_id,
            from_name="Uplink Corporation",
            subject="Subscription Fee",
            body=f"Your monthly Uplink subscription of {amount}c has been charged.",
            created_at_tick=current_tick,
        ))
        state.next_message_id += 1

        # Reschedule
        interval = data.get("recurring_interval", 5000)
        schedule_event(state, EVENT_SUBSCRIPTION, current_tick + interval, data)
        return {"type": "subscription", "amount": amount}

    elif event_type == EVENT_MISSION_GENERATE:
        from core.mission_engine import generate_missions
        count = data.get("count", 3)
        generate_missions(state, count)

        # Reschedule
        interval = data.get("recurring_interval", 2000)
        schedule_event(state, EVENT_MISSION_GENERATE, current_tick + interval, data)
        return {"type": "missions_generated", "count": count}

    return None
