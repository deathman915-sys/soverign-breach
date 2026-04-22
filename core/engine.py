"""
Onlink-Clone: Game Engine (Pure Python)

Decoupled from PySide6. Uses threading for the tick loop and a simple
EventEmitter for internal signaling. Ready for Web UI bridge.
"""

from __future__ import annotations

import logging
import random
import threading
import time
from typing import Callable

from core import (
    bank_robbery,
    event_scheduler,
    finance_engine,
    log_suspicion,
    mission_engine,
    news_engine,
    npc_engine,
    plot_engine,
    security_engine,
    trace_engine,
    warning_events,
)
from core.game_state import Company, GameState, TransportManifest
from core.hardware_engine import HardwareEngine
from core.logistics_engine import LogisticsEngine
from core.pmc_engine import PMCEngine
from core.world_generator import generate_world

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TICK_RATE_HZ = 1
BASE_TICK_S = 1.0  # 1.0s = 1 real second per tick at speed 1

# Speed multiplier to interval mapping
# 0: Paused, 1: 1Hz, 3: 3Hz, 8: 8Hz
SPEED_MAP = {0: None, 1: 1.0, 3: 0.333, 8: 0.125}

# Tick intervals
SECURITY_CHECK_INTERVAL = 40
FINANCE_TICK_INTERVAL = 200
NPC_TICK_INTERVAL = 200
NEWS_TICK_INTERVAL = 500
EVENT_PROCESS_INTERVAL = 50
PLOT_CHECK_INTERVAL = 1000
LOGISTICS_TICK_INTERVAL = 1000


class EventEmitter:
    """Simple replacement for Qt Signals."""

    def __init__(self):
        self._listeners: dict[str, list[Callable]] = {}

    def connect(self, event: str, callback: Callable):
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def emit(self, event: str, *args, **kwargs):
        for callback in self._listeners.get(event, []):
            callback(*args, **kwargs)


class GameEngine:
    """
    The beating heart of the simulation (Non-Qt).
    """

    def __init__(self) -> None:
        self.state = GameState()
        self.events = EventEmitter()

        self.logistics = LogisticsEngine()
        self.pmc = PMCEngine(self.events)

        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

        # Wire up world sim events
        self.events.connect("hijack_success", self._on_hijack_success)

    def _on_hijack_success(self, manifest: TransportManifest, pmc: Company):
        """Handle the ripple effect of a successful hijack."""
        with self._lock:
            # 1. Finance: Carrier stock crash
            carrier = next(
                (
                    c
                    for c in self.state.world.companies
                    if c.name == manifest.carrier_company
                ),
                None,
            )
            if carrier:
                drop = random.uniform(0.1, 0.25)
                carrier.stock_price *= 1.0 - drop

            # 2. Finance: PMC stock boost
            if pmc:
                pmc.stock_price *= 1.05

            # 3. News: Procedural report
            headline = (
                f"Armed Hijacking: {manifest.cargo} stolen near {manifest.destination}"
            )
            body = (
                f"A transport belonging to {manifest.carrier_company} was intercepted. "
                f"Reports indicate the shipment was valued at ${manifest.value}. "
                f"Police are questioning employees about a possible leak."
            )

            news_engine.add_news(self.state, "custom", headline=headline, body=body)
            self.events.emit("world_event", {"type": "news", "headline": headline})

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def new_game(self, player_name: str, player_handle: str) -> None:
        """Initialise a fresh game world."""
        with self._lock:
            self.state = GameState()
            self.state.player.name = player_name
            self.state.player.handle = player_handle
            generate_world(self.state)
            event_scheduler.schedule_initial_events(self.state, 0)
        # Reset module-level state for new game
        from core.lan_engine import reset_lan_states
        from core.warning_events import reset_warnings
        reset_warnings()
        reset_lan_states()

    def start(self) -> None:
        """Start the simulation loop in a background thread."""
        if self._running:
            return
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="GameTick")
        self._thread.start()

    def stop(self) -> None:
        """Stop the simulation and wait for the thread to exit."""
        self._running = False
        # Don't join if we're the tick thread (would deadlock)
        if self._thread is not None and self._thread.is_alive() and threading.current_thread() != self._thread:
            self._thread.join(timeout=2.0)
        self._thread = None

    def set_speed(self, speed: int) -> None:
        """Adjust simulation speed."""
        with self._lock:
            self.state.clock.speed_multiplier = speed

    def _loop(self) -> None:
        """The background tick thread."""
        tick_count = 0
        while self._running:
            try:
                start_time = time.time()

                with self._lock:
                    mult = self.state.clock.speed_multiplier
                    interval = SPEED_MAP.get(mult, BASE_TICK_S)

                if interval is not None:
                    self._tick(interval)
                    tick_count += 1
                    # Sleep for the remainder of the interval to maintain HZ
                    elapsed = time.time() - start_time
                    sleep_time = max(0, interval - elapsed)
                    time.sleep(sleep_time)
                else:
                    # Paused
                    time.sleep(0.1)
            except Exception as e:
                log.error(f"Tick error: {e}", exc_info=True)
                time.sleep(0.5)  # Back off on error

    def _tick(self, interval: float) -> None:
        """One simulation step."""
        with self._lock:
            s = self.state
            s.clock.tick_count += 1
            tc = s.clock.tick_count

        self.logistics.tick(s)

        # Modular Tick Sequence
        if self._tick_hardware_and_tasks(s, tc):
            return
        if self._tick_connection_and_trace(s, tc):
            return
        if self._tick_legal_and_security(s, tc):
            return
        if self._tick_economy_and_world(s, tc):
            return

        self.events.emit("tick_completed", tc)

    def _tick_hardware_and_tasks(self, s: GameState, tc: int) -> bool:
        """Processes hardware thermals, power, and task progress."""
        progress_updates, completed_tasks = HardwareEngine.process_tick(s, 1.0)

        self.events.emit("heat_changed", s.gateway.heat)
        self.events.emit("power_changed", s.gateway.power_draw, s.gateway.psu_capacity)

        if progress_updates:
            self.events.emit("task_progress", progress_updates)
        for t in completed_tasks:
            self.events.emit("task_completed", {"task_id": t.task_id, "tool_name": t.tool_name, "target_ip": t.target_ip})

        s.tasks = [t for t in s.tasks if t.is_active]

        if s.gateway.is_melted:
            self.stop()
            self.events.emit("game_over", "Gateway overheated — hardware destroyed!")
            return True
        return False

    def _tick_connection_and_trace(self, s: GameState, tc: int) -> bool:
        """Processes active and passive traces."""
        if s.connection.trace_active:
            duration = getattr(s.connection, "_trace_duration", 15.0)
            s.connection.trace_progress = min(1.0, s.connection.trace_progress + (1.0 / duration))
            if s.connection.trace_progress >= 1.0:
                self.stop()
                self.events.emit("game_over", "TRACED")
                return True

        npc_engine.process_npc_investigations(s, 1.0)
        self._tick_passive_traces()

        trace_engine.tick_traces(s, 1.0)
        completions = trace_engine.check_completed_traces(s)
        for comp in completions:
            self.events.emit("world_event", {"type": "traced", **comp})
            target = s.computers.get(s.connection.target_ip)
            if target:
                event_scheduler.schedule_trace_consequences(s, target.name, tc, target.hack_difficulty)
        return False

    def _tick_legal_and_security(self, s: GameState, tc: int) -> bool:
        """Processes jail time, security breaches, and suspicion."""
        if s.player.is_arrested:
            from core.event_scheduler import process_jail_time
            jail_result = process_jail_time(s, 1.0)
            if jail_result and jail_result["type"] == "profile_deleted":
                self.stop()
                self.events.emit("game_over", {"type": "profile_deleted"})
                return True
            elif jail_result and jail_result["type"] == "disavow_countdown":
                self.events.emit("world_event", {"type": "disavow_countdown", **jail_result})
            elif jail_result and jail_result["type"] == "released":
                self.events.emit("world_event", {"type": "released"})

        if tc % SECURITY_CHECK_INTERVAL == 0:
            sec_events = security_engine.check_security_breaches(s)
            for evt in sec_events:
                self.events.emit("world_event", evt)

        if tc % 100 == 0:
            security_engine.recover_compromised_systems(s)

        if tc % 50 == 0:
            susp_events = log_suspicion.escalate_suspicion(s, 50)
            for evt in susp_events:
                if evt["level"] >= 3:
                    self.events.emit("world_event", {"type": "investigation", "computer": evt["computer"], "computer_ip": evt["computer_ip"], "log_subject": evt["log_subject"]})

        if tc % 100 == 0:
            for evt in warning_events.check_warnings(s):
                self.events.emit("world_event", evt)
        return False

    def _tick_economy_and_world(self, s: GameState, tc: int) -> bool:
        """Processes stock market, NPCs, news, missions, and bank robberies."""
        if tc % FINANCE_TICK_INTERVAL == 0:
            finance_engine.tick_stock_market(s)
            for evt in finance_engine.accrue_interest(s, tc):
                self.events.emit("world_event", evt)
            for evt in finance_engine.process_offshore_fees(s, tc):
                self.events.emit("world_event", evt)

        if tc % NPC_TICK_INTERVAL == 0:
            for evt in npc_engine.tick_npcs(s, tc):
                self.events.emit("world_event", evt)

        if tc % NEWS_TICK_INTERVAL == 0:
            for evt in news_engine.tick_news(s, tc):
                self.events.emit("world_event", evt)

        if tc % EVENT_PROCESS_INTERVAL == 0:
            sched_events = event_scheduler.process_events(s, tc)
            for evt in sched_events:
                if evt.get("type") == "game_over":
                    self.stop()
                    self.events.emit("game_over", evt["reason"])
                    return True
                self.events.emit("world_event", evt)

        if tc % PLOT_CHECK_INTERVAL == 0:
            for evt in plot_engine.check_plot_triggers(s):
                self.events.emit("world_event", evt)

        if tc % 100 == 0:
            for evt in mission_engine.check_mission_deadlines(s):
                self.events.emit("world_event", evt)

        if tc % 10 == 0:
            bank_robbery.clear_robbery_logs(s)
            robbery_events = bank_robbery.tick_robbery_timers(s, 10)
            for evt in robbery_events:
                if evt.get("game_over"):
                    self.stop()
                    self.events.emit("game_over", evt["message"])
                    return True
                self.events.emit("world_event", evt)
        return False

    def _tick_passive_traces(self) -> None:
        """Advance NPC forensic investigations using internal forensic logs."""
        s = self.state
        for pt in s.passive_traces:
            if not pt.is_active:
                continue

            pt.ticks_until_next_hop -= 1
            if pt.ticks_until_next_hop <= 0:
                # Attempt to move to next hop
                current_comp = s.computers.get(pt.current_node_ip)
                if not current_comp:
                    pt.is_active = False
                    continue

                # Find log pointing backwards in INTERNAL logs (forensic backup)
                found_hop = None
                for log_entry in reversed(current_comp.internal_logs):
                    # Passive traces track the IP used DURING THAT SESSION
                    if not log_entry.is_deleted and log_entry.from_ip != "unknown":
                        found_hop = log_entry.from_ip
                        break

                if found_hop:
                    # Check if reached player (current OR session IP)
                    if found_hop == s.player.localhost_ip or found_hop == s.player.last_login_ip:
                        pt.is_active = False
                        # Trigger proper arrest flow with consequences
                        from core.event_scheduler import trigger_arrest
                        arrest_result = trigger_arrest(s, reason="PASSIVE TRACE REACHED GATEWAY")
                        self.stop()
                        self.events.emit("game_over", arrest_result)
                        return

                    pt.current_node_ip = found_hop
                    pt.ticks_until_next_hop = 400  # Forensic hops are slow
                    self.events.emit(
                        "world_event", {"type": "forensics_update", "node": found_hop}
                    )
                else:
                    # Log trail broken!
                    pt.is_active = False
                    self.events.emit(
                        "world_event",
                        {"type": "forensics_lost", "msg": "Trail went cold"},
                    )
