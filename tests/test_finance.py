import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from core.game_state import (
    GameState,
    BankAccount,
    LoanRecord,
    Company,
    Computer,
)
from core import finance_engine


@pytest.fixture
def state():
    s = GameState()
    # Add a company
    s.world.companies.append(Company(name="TechCorp", stock_price=100.0))
    # Add its computer
    s.computers["10.0.0.1"] = Computer(
        ip="10.0.0.1", name="TechCorp Mainframe", company_name="TechCorp"
    )

    # Add a player bank account
    acct = BankAccount(
        id=1,
        owner_name="AGENT",
        balance=1000,
        is_player=True,
        account_number="12345678",
    )
    s.bank_accounts.append(acct)
    return s


class TestFinanceMechanics:
    def test_loan_interest_accrual(self, state):
        # Create a loan
        loan = LoanRecord(
            id=1, bank_account_id=1, amount=1000, interest_rate=0.10
        )  # 10%
        state.loans.append(loan)

        # interest = int(loan.amount * loan.interest_rate / 100)
        # 1000 * 0.1 / 100 = 1.0 -> 1

        finance_engine.accrue_interest(state, 100)

        assert loan.amount == 1001
        # Verify bank account loan_amount updated
        assert state.bank_accounts[0].loan_amount == 1001

    def test_stock_crash_on_computer_destruction(self, state):
        comp = state.world.companies[0]
        initial_price = comp.stock_price

        # Trigger crash
        finance_engine.trigger_stock_crash(
            state, "TechCorp", reason="mainframe_destroyed"
        )

        assert comp.stock_price < initial_price
        assert comp.stock_price == initial_price * 0.5  # 50% crash for mainframe

    def test_stock_crash_on_data_theft(self, state):
        comp = state.world.companies[0]
        initial_price = comp.stock_price

        # Trigger crash
        finance_engine.trigger_stock_crash(state, "TechCorp", reason="research_stolen")

        assert comp.stock_price < initial_price
        assert comp.stock_price == initial_price * 0.8  # 20% dip for data theft
