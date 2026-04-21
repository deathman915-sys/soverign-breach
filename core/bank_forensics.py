"""
Onlink-Clone: Bank Forensics Engine
Handles the creation, logging, and tracing of cryptographic transaction hashes.
"""
from __future__ import annotations

import hashlib
import uuid
import logging
from core.game_state import GameState, TransactionRecord

log = logging.getLogger(__name__)

def generate_transaction_hash(from_account: str, to_account: str, amount: int, tick: int) -> str:        
    """Generate a unique cryptographic hash for a transaction."""
    raw_data = f"{from_account}-{to_account}-{amount}-{tick}-{uuid.uuid4().hex}"
    return hashlib.sha256(raw_data.encode('utf-8')).hexdigest()

def create_ghost_log(state: GameState, bank_ip: str, tx_hash: str, from_acc: str, to_acc: str, amount: int):
    """
    Creates a non-deletable forensic entry in the bank's internal logs.
    This bypasses standard 'Log Deleter' tools.
    """
    from core.game_state import AccessLog
    bank = state.computers.get(bank_ip)
    if not bank:
        return

    entry = AccessLog(
        log_time=f"Tick {state.clock.tick_count}",
        from_ip="INTERNAL_TRANSFER",
        from_name="SYSTEM",
        subject=f"Ghost Log: TX {tx_hash[:8]} | {from_acc} -> {to_acc} | {amount}c",
        tick_created=state.clock.tick_count,
        is_visible=False, # Hidden from standard views
        suspicion_level=1
    )
    # Use add_log to ensure it hits internal_logs
    bank.add_log(entry)

def trace_transaction(state: GameState, tx_hash: str) -> list[TransactionRecord]:
    """
    Search all bank accounts for a specific transaction hash.
    Returns a list of matching TransactionRecord objects.
    """
    matches = []
    for acct in state.bank_accounts:
        for tx in acct.transaction_log:
            if tx.hash == tx_hash:
                matches.append(tx)
    
    # Remove duplicates since both sender and receiver log the same hash
    unique_matches = {m.hash: m for m in matches}.values()
    return list(unique_matches)
