"""
Onlink-Clone: World Simulation & Micro-Data Prototype

This prototype demonstrates the "World Sim" layer where:
1. Companies have specialized types (Logistics, PMC).
2. Procedural "Micro-Data" (Truck Manifests) is generated on-demand.
3. Events (Hijacks) ripple through the Finance and News engines.
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Dict, Optional, Callable

# Reuse existing EventEmitter pattern
class EventEmitter:
    def __init__(self):
        self._listeners: dict[str, list[Callable]] = {}

    def connect(self, event: str, callback: Callable):
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def emit(self, event: str, *args, **kwargs):
        for callback in self._listeners.get(event, []):
            callback(*args, **kwargs)

# =========================================================================
# Domain Models
# =========================================================================

class CompanyType(IntEnum):
    GENERAL = 0
    FINANCIAL = 1
    LOGISTICS = 2
    PMC = 3
    MEDICAL = 4
    GOVERNMENT = 5
    ACADEMIC = 6

@dataclass
class TransportManifest:
    id: str
    origin: str
    destination: str
    cargo: str
    value: int
    carrier_company: str
    status: str = "IN_TRANSIT"  # IN_TRANSIT, DELIVERED, HIJACKED, LOST

@dataclass
class Company:
    name: str
    company_type: CompanyType = CompanyType.GENERAL
    stock_price: float = 100.0
    stock_volatility: float = 0.05
    owner_id: Optional[str] = None  # Could be Player or NPC
    assets: List[str] = field(default_factory=list)

@dataclass
class NewsItem:
    headline: str
    body: str
    tick: int

# =========================================================================
# Specialized Engines
# =========================================================================

class LogisticsEngine:
    """Manages the generation and tracking of transport manifests."""
    def __init__(self, events: EventEmitter):
        self.events = events
        self.active_manifests: Dict[str, TransportManifest] = {}
        self._id_counter = 1000

    def generate_trip(self, company: Company, origin: str, dest: str) -> TransportManifest:
        cargo_items = ["GPU Crates", "Medical Supplies", "Industrial Chemicals", "Luxury Goods", "Server Hardware"]
        manifest = TransportManifest(
            id=f"TRK-{self._id_counter}",
            origin=origin,
            destination=dest,
            cargo=random.choice(cargo_items),
            value=random.randint(5000, 50000),
            carrier_company=company.name
        )
        self._id_counter += 1
        self.active_manifests[manifest.id] = manifest
        print(f"[Logistics] Generated Manifest {manifest.id}: {manifest.cargo} from {origin} to {dest}")
        return manifest

class PMCEngine:
    """Manages PMC squads and interception logic."""
    def __init__(self, events: EventEmitter):
        self.events = events

    def attempt_intercept(self, manifest: TransportManifest, pmc_company: Company) -> bool:
        """Rolls for success. In a real game, this would depend on squad stats/gear."""
        success_chance = 0.7  # High chance for prototype
        success = random.random() < success_chance
        
        if success:
            manifest.status = "HIJACKED"
            print(f"[PMC] {pmc_company.name} SUCCESSFULLY hijacked {manifest.id} ({manifest.cargo})!")
            self.events.emit("hijack_success", manifest=manifest, pmc=pmc_company)
        else:
            print(f"[PMC] {pmc_company.name} FAILED to intercept {manifest.id}.")
            self.events.emit("hijack_failed", manifest=manifest, pmc=pmc_company)
        
        return success

# =========================================================================
# Unified World Simulator
# =========================================================================

class WorldSimPrototype:
    def __init__(self):
        self.events = EventEmitter()
        self.logistics = LogisticsEngine(self.events)
        self.pmc = PMCEngine(self.events)
        
        # State
        self.companies: Dict[str, Company] = {}
        self.news: List[NewsItem] = []
        self.tick_count = 0

        # Setup event listeners for the "Ripple Effect"
        self.events.connect("hijack_success", self._on_hijack_success)

    def add_company(self, company: Company):
        self.companies[company.name] = company

    def _on_hijack_success(self, manifest: TransportManifest, pmc: Company):
        # 1. Finance Ripple: Carrier stock crashes
        carrier = self.companies.get(manifest.carrier_company)
        if carrier:
            drop = random.uniform(0.1, 0.2)
            old_price = carrier.stock_price
            carrier.stock_price *= (1.0 - drop)
            print(f"[Finance] {carrier.name} stock DROPPED from ${old_price:.2f} to ${carrier.stock_price:.2f}")

        # 2. Finance Ripple: PMC stock might rise (or gain notoriety)
        pmc.stock_price *= 1.05
        print(f"[Finance] {pmc.name} stock ROSE to ${pmc.stock_price:.2f} due to successful operation.")

        # 3. News Ripple: Procedural Story Generation
        headline = f"Armed Hijacking: {manifest.cargo} stolen on route to {manifest.destination}"
        body = (f"Authorities report that a {carrier.name} transport was intercepted by an armed force. "
                f"The cargo, valued at ${manifest.value}, is still missing. "
                f"Market analysts are worried about {carrier.name}'s security protocols.")
        
        news = NewsItem(headline, body, self.tick_count)
        self.news.append(news)
        print(f"[News] BREAKING: {headline}")

    def run_demo(self):
        print("--- Starting World Sim Prototype ---")
        
        # 1. Setup Companies
        global_freight = Company("Global Freight", CompanyType.LOGISTICS, stock_price=120.0)
        aegis_pmc = Company("Aegis Defense", CompanyType.PMC, stock_price=85.0)
        self.add_company(global_freight)
        self.add_company(aegis_pmc)

        # 2. Generate Micro-Data (The "Truck")
        print("\nStep 1: Logistics activity detected...")
        manifest = self.logistics.generate_trip(global_freight, "Christchurch", "Dunedin")

        # 3. Perform Action (The "Hijack")
        print("\nStep 2: PMC squad deployed for interception...")
        self.pmc.attempt_intercept(manifest, aegis_pmc)

        # 4. Show News
        print("\nStep 3: Checking News Feed...")
        for item in self.news:
            print(f"[{item.tick}] {item.headline}")
            print(f"    {item.body}\n")

if __name__ == "__main__":
    sim = WorldSimPrototype()
    sim.run_demo()
