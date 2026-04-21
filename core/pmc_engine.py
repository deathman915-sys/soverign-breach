"""
Onlink-Clone: PMC Engine

Manages tactical squads, interceptions, and combat simulation.
"""
from __future__ import annotations
import random
from typing import TYPE_CHECKING
from core.game_state import GameState, TransportManifest, PMCSquad, ManifestStatus

if TYPE_CHECKING:
    from core.engine import EventEmitter

class PMCEngine:
    def __init__(self, events: EventEmitter):
        self.events = events

    def tick(self, state: GameState):
        """Advance autonomous PMC missions and squad movements."""
        pass

    def attempt_intercept(self, state: GameState, manifest: TransportManifest, squad: PMCSquad) -> bool:
        """
        Attempt to hijack/intercept a logistics shipment using a specific squad.
        Success depends on combat rating vs shipment security level.
        """
        # Sabotage bonus: -50% security level if sabotaged
        effective_security = manifest.security_level
        if manifest.is_security_sabotaged:
            effective_security *= 0.5
            
        # Combat math: squad skill vs manifest security
        base_chance = squad.combat_rating / (squad.combat_rating + effective_security)
        
        # Variance +/- 10%
        variance = random.uniform(-0.1, 0.1)
        success_chance = max(0.05, min(0.95, base_chance + variance))
        
        success = random.random() < success_chance

        pmc_company = next((c for c in state.world.companies if c.name == squad.owner_company), None)

        if success:
            manifest.status = ManifestStatus.HIJACKED
            # Emit event for news/finance to pick up
            self.events.emit("hijack_success", manifest=manifest, pmc=pmc_company)
            return True
        else:
            self.events.emit("hijack_failed", manifest=manifest, pmc=pmc_company)
            return False
