
from core.game_state import GameState, BankAccount, TransactionRecord
from core.apps.finance import FinanceApp

def test_finance_app_returns_transaction_logs():
    state = GameState()
    tx = TransactionRecord(
        hash="test_hash",
        amount=500,
        from_account="123456",
        to_account="654321",
        tick=100,
        from_ip="1.1.1.1",
        to_ip="2.2.2.2"
    )
    acct = BankAccount(
        id=1,
        owner_name="Agent",
        account_number="123456",
        balance=2500,
        is_player=True,
        transaction_log=[tx]
    )
    state.bank_accounts = [acct]
    
    app = FinanceApp(state)
    data = app.init()
    
    # Verify transaction data is included
    assert "accounts" in data
    assert len(data["accounts"]) > 0
    player_acct = next(a for a in data["accounts"] if a["account_number"] == "123456")
    assert "transaction_log" in player_acct
    assert len(player_acct["transaction_log"]) == 1
    assert player_acct["transaction_log"][0]["hash"] == "test_hash"
