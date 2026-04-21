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
