"""Tests for the Bank Forensics and Transaction logic."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.bank_forensics import trace_transaction
from core.finance_engine import open_account, transfer_funds
from core.game_state import GameState


class TestBankForensics:
    def test_transaction_hashing(self):
        s = GameState()
        # Open two accounts
        res1 = open_account(s, "1.1.1.1")
        res2 = open_account(s, "2.2.2.2")
        acct1_id = res1["account_id"]
        acct2_id = res2["account_id"]

        # Give acct1 some money manually for the test
        acct1 = next(a for a in s.bank_accounts if a.id == acct1_id)
        acct2 = next(a for a in s.bank_accounts if a.id == acct2_id)
        acct1.balance = 5000

        # Transfer funds
        tx_res = transfer_funds(s, acct1_id, acct2_id, 1000)
        assert tx_res["success"]
        assert "transaction_hash" in tx_res

        tx_hash = tx_res["transaction_hash"]

        # Verify transaction record exists on the accounts
        assert len(acct1.transaction_log) == 1
        assert acct1.transaction_log[0].hash == tx_hash
        assert len(acct2.transaction_log) == 1
        assert acct2.transaction_log[0].hash == tx_hash

    def test_trace_transaction(self):
        s = GameState()
        res1 = open_account(s, "1.1.1.1")
        res2 = open_account(s, "2.2.2.2")
        res3 = open_account(s, "3.3.3.3")

        acct1_id = res1["account_id"]
        acct2_id = res2["account_id"]
        acct3_id = res3["account_id"]

        acct1 = next(a for a in s.bank_accounts if a.id == acct1_id)
        acct1.balance = 5000

        # acct1 -> acct2 -> acct3
        tx1 = transfer_funds(s, acct1_id, acct2_id, 1000)
        transfer_funds(s, acct2_id, acct3_id, 1000)

        hash1 = tx1["transaction_hash"]

        # Trace hash1 globally
        trace_result = trace_transaction(s, hash1)
        assert len(trace_result) > 0
        assert trace_result[0].from_account == res1["account_number"]
        assert trace_result[0].to_account == res2["account_number"]
        assert trace_result[0].amount == 1000
