import pytest

from core import finance_engine
from core.game_state import BankAccount, GameState


@pytest.fixture
def state():
    from core.game_state import Computer
    s = GameState()
    # Add actual computer nodes so forensics can find them
    s.computers["victim.bank"] = Computer(ip="victim.bank", name="Victim Bank")
    s.computers["offshore.bank"] = Computer(ip="offshore.bank", name="Offshore Bank")
    s.computers["standard.bank"] = Computer(ip="standard.bank", name="Standard Bank")

    # 1. Victim Bank Account (Non-player)
    s.bank_accounts.append(BankAccount(id=1, bank_ip="victim.bank", balance=10000, is_player=False, account_number="11111111"))
    # 2. Player Offshore Account
    s.bank_accounts.append(BankAccount(id=2, bank_ip="offshore.bank", balance=0, is_player=True, is_offshore=True, account_number="22222222"))
    # 3. Player Standard Account
    s.bank_accounts.append(BankAccount(id=3, bank_ip="standard.bank", balance=0, is_player=True, is_offshore=False, account_number="33333333"))
    return s

def test_theft_is_hot(state):
    """Verify that funds from a non-player account are 100% hot."""
    finance_engine.transfer_funds(state, 1, 3, 5000)

    player_acc = next(a for a in state.bank_accounts if a.id == 3)
    assert player_acc.hot_ratio == 1.0
    assert state._hot_ratio == 1.0

def test_offshore_laundering(state):
    """Verify that offshore transfers reduce hotness by 50%."""
    # Step 1: Steal money to standard account (100% hot)
    finance_engine.transfer_funds(state, 1, 3, 5000)

    # Step 2: Transfer to offshore account
    finance_engine.transfer_funds(state, 3, 2, 5000)

    offshore_acc = next(a for a in state.bank_accounts if a.id == 2)
    # 1.0 hotness * 0.5 offshore factor = 0.5
    assert offshore_acc.hot_ratio == 0.5
    assert state._hot_ratio == 0.5

def test_bounce_laundering(state):
    """Verify that bouncing through nodes reduces hotness."""
    # Set bounce chain length to 4
    state.bounce.hops = ["hop1", "hop2", "hop3", "hop4"]

    # Steal money
    finance_engine.transfer_funds(state, 1, 3, 5000)

    player_acc = next(a for a in state.bank_accounts if a.id == 3)
    # source(1.0) * (1.0 - (4 * 0.05)) = 1.0 * 0.8 = 0.8
    assert player_acc.hot_ratio == 0.8

def test_ghost_logs_created(state):
    """Verify that ghost logs are created in bank internal_logs."""
    finance_engine.transfer_funds(state, 1, 3, 1000)

    victim_bank = state.computers.get("victim.bank")
    # Should have 1 public log and 1 internal log (ghost log)
    assert len(victim_bank.internal_logs) == 1
    assert "Ghost Log" in victim_bank.internal_logs[0].subject

def test_blending_hot_and_clean_funds(state):
    """Verify that mixing hot and clean funds averages the hot_ratio."""
    # 1. Give player 1000 clean credits
    player_acc = next(a for a in state.bank_accounts if a.id == 3)
    player_acc.balance = 1000
    player_acc.hot_ratio = 0.0
    state.player.balance = 1000

    # 2. Steal 1000 hot credits (no bounces)
    state.bounce.hops = []
    finance_engine.transfer_funds(state, 1, 3, 1000)

    # Result: (1000 * 0.0 + 1000 * 1.0) / 2000 = 0.5
    assert player_acc.hot_ratio == 0.5
