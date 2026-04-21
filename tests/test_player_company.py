
from core.game_state import GameState, CompanyType
from core.company_engine import found_company, get_player_company

def test_found_company_deducts_balance_and_registers():
    state = GameState()
    state.player.balance = 15000
    
    res = found_company(state, "CyberDyne", CompanyType.PMC)
    
    assert res["success"] is True
    assert state.player.balance == 5000
    assert state.player.company_id is not None
    
    company = get_player_company(state)
    assert company is not None
    assert company.name == "CyberDyne"
    assert company.company_type == CompanyType.PMC
    assert company.owner_id == "PLAYER"

def test_found_company_insufficient_funds():
    state = GameState()
    state.player.balance = 5000
    
    res = found_company(state, "PoorCorp", CompanyType.LOGISTICS)
    
    assert res["success"] is False
    assert "Insufficient funds" in res["error"]
    assert state.player.company_id is None
