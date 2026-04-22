import pytest

from core.game_state import BankAccount, GameState
from core.remote_controller import RemoteController


@pytest.fixture
def state():
    s = GameState()
    # Add a sample player account
    s.bank_accounts.append(BankAccount(
        id=1,
        bank_ip="1.1.1.1",
        account_number="12345678",
        balance=5000,
        is_player=True
    ))
    return s

def test_build_finance_html_contains_account_info(state):
    """Verify that the Python-generated finance HTML includes bank data."""
    rc = RemoteController(state)
    html = rc.build_finance_html()

    assert "1.1.1.1" in html
    assert "12345678" in html
    assert "5,000" in html # Formatted balance
    assert "FINANCIAL SUMMARY" in html

def test_build_finance_html_centered_layout(state):
    """Verify that the finance HTML uses the tactical centered layout."""
    rc = RemoteController(state)
    html = rc.build_finance_html()

    # Check for tactical centering constraints
    assert "max-width:800px" in html
    assert "display:flex; flex-direction:column; align-items:center;" in html

def test_build_finance_empty_state():
    """Ensure graceful handling of no accounts."""
    s = GameState()
    rc = RemoteController(s)
    html = rc.build_finance_html()
    assert "No accounts linked" in html
