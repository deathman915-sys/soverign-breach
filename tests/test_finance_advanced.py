import pytest
from core.game_state import GameState, BankAccount, LoanRecord, VFSFile, SoftwareType
from core import finance_engine

@pytest.fixture
def state():
    s = GameState()
    s.clock.tick_count = 100
    # Add a primary bank account
    s.bank_accounts.append(BankAccount(id=1, bank_ip="1.1.1.1", balance=5000, is_player=True))
    return s

def test_loan_due_date_assignment(state):
    """Verify that new loans are assigned a future due date."""
    res = finance_engine.take_loan(state, 1, 1000)
    assert res["success"]
    loan = state.loans[0]
    assert loan.due_at_tick == 100 + 5000

def test_asset_repossession_on_default(state):
    """Verify that software is deleted when a loan defaults."""
    # 1. Give player some software
    state.vfs.files.append(VFSFile(id="tool1", filename="PasswordBreaker_v1", version=1, software_type=SoftwareType.CRACKERS))
    state.vfs.files.append(VFSFile(id="tool2", filename="ProxyBypass_v3", version=3, software_type=SoftwareType.BYPASSERS))
    assert len(state.vfs.files) == 2

    # 2. Create an overdue loan
    loan = LoanRecord(id=1, bank_account_id=1, amount=1000, due_at_tick=50, is_paid=False)
    state.loans.append(loan)

    # 3. Tick interest/defaults (current tick 100 > due tick 50)
    events = finance_engine.accrue_interest(state, 100)
    
    # 4. Verify consequences
    assert any(e["type"] == "loan_default" for e in events)
    assert loan.is_defaulted is True
    
    # High version (v3) should have been repossessed first
    assert len(state.vfs.files) == 0 # It deletes up to 2 files
    filenames = [f.filename for f in state.vfs.files]
    assert "ProxyBypass_v3" not in filenames

def test_offshore_maintenance_fees(state):
    """Verify that offshore accounts lose money over time."""
    # 1. Create offshore account
    offshore = BankAccount(id=2, bank_ip="8.8.8.8", balance=10000, is_player=True, is_offshore=True)
    state.bank_accounts.append(offshore)
    
    # 2. Process fees
    events = finance_engine.process_offshore_fees(state, 1000)
    
    # 3. Verify balance reduction (0.5% of 10000 = 50)
    assert offshore.balance == 9950
    assert any(e["type"] == "bank_fee" for e in events)
    # Total player balance should also be synced
    assert state.player.balance == 5000 + 9950

def test_repossess_assets_empty_vfs(state):
    """Ensure repossession handles empty VFS gracefully."""
    state.vfs.files = []
    res = finance_engine.repossess_assets(state)
    assert res["success"] is False
    assert "No assets" in res["msg"]
