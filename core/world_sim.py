"""
Onlink-Clone: World Simulator

Handles background NPC actions, stock market fluctuations,
infrastructure blackouts, and news generation.

All reads/writes go through GameState — no lateral core imports.
"""
from __future__ import annotations

import random

from core.game_state import (
    GameState, NewsItem,
)


# Tick intervals (in simulation ticks at 5Hz)
NPC_TICK_INTERVAL = 200       # NPC actions every ~40s
STOCK_TICK_INTERVAL = 100     # Stock fluctuation every ~20s
NEWS_TICK_INTERVAL = 500      # Random news every ~100s
COMPUTER_TICK_INTERVAL = 50   # Maintenance check every ~10s
BLACKOUT_DURATION_TICKS = 600 # ~2 minutes of real time

LOG_EXPIRATION_TICKS = 400     # Logs purged after ~80s
REPAIR_CHANCE = 0.2           # 20% chance to fix a security layer per maintenance tick


class WorldSimulator:
    """
    Stateless world simulation.  Called once per engine tick.
    """

    def __init__(self) -> None:
        self._pending_restores: list[tuple[int, str]] = []  # (restore_tick, region)

    # ------------------------------------------------------------------
    # Main tick entry
    # ------------------------------------------------------------------
    def tick(self, state: GameState) -> list[dict]:
        """
        Advance world simulation by one tick.
        Returns a list of event dicts for the UI to consume.
        """
        events: list[dict] = []
        tick = state.clock.tick_count

        # NPC actions
        if tick % NPC_TICK_INTERVAL == 0 and tick > 0:
            events.extend(self._tick_npcs(state))

        # Stock market
        if tick % STOCK_TICK_INTERVAL == 0 and tick > 0:
            self._tick_stocks(state)

        # Computer AI (Maintenance)
        if tick % COMPUTER_TICK_INTERVAL == 0 and tick > 0:
            self._tick_computers(state)

        # News
        if tick % NEWS_TICK_INTERVAL == 0 and tick > 0:
            news = self._generate_news(state)
            if news:
                events.append({"type": "news", "headline": news.headline})

        # Process pending region restores
        events.extend(self._process_restores(state))

        return events

    # ------------------------------------------------------------------
    # Computer Maintenance (Internal AI)
    # ------------------------------------------------------------------
    def _tick_computers(self, state: GameState) -> None:
        """Computers purge old logs and repair security."""
        now = state.clock.tick_count
        for comp in state.computers.values():
            # 1. Log Purge
            comp.logs = [
                log_entry for log_entry in comp.logs
                if not log_entry.is_deleted and (now - getattr(log_entry, "tick_created", 0)) < LOG_EXPIRATION_TICKS       
            ]
            # 2. Security Repair
            for sec in comp.security_systems:
                if not sec.is_active or sec.is_bypassed:
                    if random.random() < REPAIR_CHANCE:
                        sec.is_active = True
                        sec.is_bypassed = False

            # 3. Password Rotation (If breached)
            if comp.ip in state.player.known_passwords:
                # 5% chance to change password per maintenance tick if player knows it
                if random.random() < 0.05:
                    from core.name_generator import generate_password
                    new_pw = generate_password()
                    # Find password screen
                    for scr in comp.screens:
                        if scr.screen_type == 1: # PASSWORD
                            scr.data1 = new_pw
                            # Forget old password
                            if comp.ip in state.player.known_passwords:
                                del state.player.known_passwords[comp.ip]
                            break

    # ------------------------------------------------------------------
    # NPC agents
    # ------------------------------------------------------------------
    def _tick_npcs(self, state: GameState) -> list[dict]:
        """NPCs attempt random hacking actions."""
        events: list[dict] = []
        for npc in state.world.people:
            if not npc.is_agent or npc.has_criminal_record:
                continue
            # Simple model: NPCs have a chance to complete their current mission
            if random.random() < 0.1:
                payout = random.randint(500, 1000) * max(1, npc.uplink_rating)
                events.append({
                    "type": "npc_action",
                    "npc_name": npc.name,
                    "action": "completed_mission",
                    "payout": payout,
                })
        return events

    # ------------------------------------------------------------------
    # Stock market
    # ------------------------------------------------------------------
    def _tick_stocks(self, state: GameState) -> None:
        """Random walk on stock prices."""
        for company in state.world.companies:
            volatility = company.stock_volatility
            change = random.gauss(0, volatility) * company.stock_price
            company.stock_price = max(1.0, company.stock_price + change)

    # ------------------------------------------------------------------
    # Blackouts
    # ------------------------------------------------------------------
    def trigger_blackout(self, state: GameState, region: str) -> list[dict]:
        """
        Called when a power plant is hacked.
        - Takes all nodes in the region offline.
        - Crashes stock prices for companies in that region.
        - Generates a breaking news event.
        - Schedules region restore after BLACKOUT_DURATION_TICKS.
        """
        events: list[dict] = []

        # Take nodes offline
        affected_ips = []
        for node in state.nodes.values():
            if node.region == region and node.is_online:
                node.is_online = False
                affected_ips.append(node.ip)

        # Crash stocks
        for company in state.world.companies:
            if company.region == region:
                crash_pct = random.uniform(0.15, 0.40)
                company.stock_price *= (1.0 - crash_pct)

        # News
        news = NewsItem(
            headline=f"BREAKING: Power grid failure in {region} — {len(affected_ips)} systems offline",
            body=f"A catastrophic failure in the {region} power grid has taken "
                 f"{len(affected_ips)} networked systems offline. Stock markets in the "
                 f"region are in freefall.",
            tick_created=state.clock.tick_count,
        )
        state.world.news.append(news)

        # Schedule restore
        restore_at = state.clock.tick_count + BLACKOUT_DURATION_TICKS
        self._pending_restores.append((restore_at, region))

        events.append({
            "type": "blackout",
            "region": region,
            "affected_count": len(affected_ips),
        })
        return events

    def _process_restores(self, state: GameState) -> list[dict]:
        """Restore regions whose blackout duration has expired."""
        events: list[dict] = []
        remaining: list[tuple[int, str]] = []

        for restore_tick, region in self._pending_restores:
            if state.clock.tick_count >= restore_tick:
                for node in state.nodes.values():
                    if node.region == region:
                        node.is_online = True
                news = NewsItem(
                    headline=f"Power restored in {region}",
                    body=f"The {region} power grid has been restored. Systems are coming back online.",
                    tick_created=state.clock.tick_count,
                )
                state.world.news.append(news)
                events.append({"type": "region_restored", "region": region})
            else:
                remaining.append((restore_tick, region))

        self._pending_restores = remaining
        return events

    # ------------------------------------------------------------------
    # News
    # ------------------------------------------------------------------
    def _generate_news(self, state: GameState) -> NewsItem | None:
        """Generate a random flavour news item."""
        templates = [
            "Global cybercrime rates up 12% this quarter",
            "New encryption standard proposed by IANA",
            "Uplink Corporation reports record agent enrollment",
            "InterNIC warns of rising DNS spoofing attacks",
            "Stock markets volatile amid infrastructure concerns",
            "Government announces tighter penalties for hackers",
        ]
        headline = random.choice(templates)
        news = NewsItem(
            headline=headline,
            body=headline,  # placeholder
            tick_created=state.clock.tick_count,
        )
        state.world.news.append(news)
        return news
