"""
Onlink-Clone: Company & PMC Ownership Engine

Handles the founding, management, and growth of player-owned corporations.
Supports Private Military Companies (PMC) and Logistics firms.
"""

from __future__ import annotations
import uuid
import logging
from core.game_state import GameState, Company, CompanyType

log = logging.getLogger(__name__)

def found_company(state: GameState, name: str, company_type: CompanyType) -> dict:
    """Found a new company owned by the player."""
    p = state.player
    
    # Cost to found: 10,000 credits
    cost = 10000
    if p.balance < cost:
        return {"success": False, "error": "Insufficient funds (10,000c required)"}
    
    if p.company_id:
        return {"success": False, "error": "You already own a company"}

    p.balance -= cost
    
    new_id = str(uuid.uuid4())
    new_company = Company(
        name=name,
        company_type=company_type,
        owner_id="PLAYER",
        stock_price=50.0, # Initial stock price
        size=10,
        growth=5,
        alignment=0,
        region="Global"
    )
    
    # Store ID in player state
    p.company_id = new_id
    # We need a way to link the Company object to this ID if we use UUIDs
    # For simplicity, let's use the name as ID or add an id field to Company
    
    state.world.companies.append(new_company)
    log.info(f"PLAYER FOUNDED COMPANY: {name} ({company_type.name})")
    
    return {"success": True, "company_name": name}

def get_player_company(state: GameState) -> Company | None:
    """Returns the company owned by the player."""
    for c in state.world.companies:
        if c.owner_id == "PLAYER":
            return c
    return None
