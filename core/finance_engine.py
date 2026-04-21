"""
Onlink-Clone: Finance Engine

Banking, loans, stock market operations.
Ported from the ajhenley fork — all SQLAlchemy replaced with GameState ops.
"""

from __future__ import annotations

import random
import logging
import string

from core.game_state import (
    GameState,
    BankAccount,
    LoanRecord,
    StockHolding,
)

log = logging.getLogger(__name__)


# ======================================================================
# Banking
# ======================================================================
def get_player_accounts(state: GameState) -> list[dict]:
    """Get all bank accounts owned by the player."""
    return [
        {
            "id": a.id,
            "bank_ip": a.bank_ip,
            "balance": a.balance,
            "loan_amount": a.loan_amount,
            "account_number": a.account_number,
            "transaction_log": [
                {
                    "hash": tx.hash,
                    "amount": tx.amount,
                    "from_account": tx.from_account,
                    "to_account": tx.to_account,
                    "tick": tx.tick,
                    "from_ip": tx.from_ip,
                    "to_ip": tx.to_ip,
                }
                for tx in a.transaction_log
            ],
        }
        for a in state.bank_accounts
        if a.is_player
    ]


def _sync_player_balance(state: GameState) -> None:
    """Helper to keep state.player.balance as the sum of all player bank accounts."""
    state.player.balance = sum(a.balance for a in state.bank_accounts if a.is_player)
    _sync_player_hotness(state)


def _sync_player_hotness(state: GameState) -> None:
    """Calculates the weighted average hot_ratio of all player funds."""
    total_balance = state.player.balance
    if total_balance <= 0:
        state._hot_ratio = 0.0
        return
    
    total_hot_mass = sum(a.balance * a.hot_ratio for a in state.bank_accounts if a.is_player)
    state._hot_ratio = total_hot_mass / total_balance


def transfer_funds(
    state: GameState, from_account_id: int, to_account_id: int, amount: int
) -> dict:
    """Transfer funds between bank accounts."""
    from core.bank_forensics import generate_transaction_hash, create_ghost_log
    from core.game_state import TransactionRecord

    from_acct = next((a for a in state.bank_accounts if a.id == from_account_id), None)
    to_acct = next((a for a in state.bank_accounts if a.id == to_account_id), None)

    if from_acct is None or to_acct is None:
        return {"success": False, "error": "Account not found"}
    if amount <= 0:
        return {"success": False, "error": "Invalid amount"}
    if from_acct.balance < amount:
        return {"success": False, "error": "Insufficient funds"}

    # Laundering Logic: Calculate Hotness
    # 1. Determine if this is a theft (from non-player account)
    source_hotness = 1.0 if not from_acct.is_player else from_acct.hot_ratio
    
    # 2. Apply cleaning (Offshore/Bouncing)
    cleaning_factor = 1.0
    if to_acct.is_offshore:
        cleaning_factor *= 0.5 # Offshore accounts are 50% effective at cleaning per transfer
    
    # Reduce hotness based on bounce length (max 50% reduction)
    bounce_len = state.bounce.length
    if bounce_len > 0:
        reduction = min(0.5, bounce_len * 0.05)
        cleaning_factor *= (1.0 - reduction)

    applied_hotness = source_hotness * cleaning_factor

    # 3. Blend with target account hotness
    new_total_balance = to_acct.balance + amount
    if new_total_balance > 0:
        to_acct.hot_ratio = ((to_acct.balance * to_acct.hot_ratio) + (amount * applied_hotness)) / new_total_balance

    from_acct.balance -= amount
    to_acct.balance += amount

    # Generate and log transaction hash
    tx_hash = generate_transaction_hash(
        from_acct.account_number, to_acct.account_number, amount, state.clock.tick_count
    )
    
    # Create non-deletable ghost logs at both banks
    create_ghost_log(state, from_acct.bank_ip, tx_hash, from_acct.account_number, to_acct.account_number, amount)
    create_ghost_log(state, to_acct.bank_ip, tx_hash, from_acct.account_number, to_acct.account_number, amount)

    record = TransactionRecord(
        hash=tx_hash,
        amount=amount,
        from_account=from_acct.account_number,
        to_account=to_acct.account_number,
        tick=state.clock.tick_count,
        from_ip=from_acct.bank_ip,
        to_ip=to_acct.bank_ip,
        is_hot=(applied_hotness > 0.1),
        hot_ratio=applied_hotness
    )
    from_acct.transaction_log.append(record)
    to_acct.transaction_log.append(record)

    # Update player balance if player account is involved
    _sync_player_balance(state)

    log.info(
        "Transfer: %d from acct %d to acct %d (Hash: %s, Hot: %.2f)",
        amount,
        from_account_id,
        to_account_id,
        tx_hash,
        applied_hotness
    )
    return {"success": True, "amount": amount, "transaction_hash": tx_hash, "hot_ratio": applied_hotness}


def open_account(state: GameState, bank_ip: str) -> dict:
    """Open a new bank account at the specified bank."""
    rng = random.Random()
    acct_num = "".join(rng.choices(string.digits, k=8))

    account = BankAccount(
        id=state.next_account_id,
        owner_name=state.player.handle,
        bank_ip=bank_ip,
        balance=0,
        is_player=True,
        account_number=acct_num,
    )
    state.next_account_id += 1
    state.bank_accounts.append(account)

    return {"success": True, "account_id": account.id, "account_number": acct_num}


# ======================================================================
# Loans
# ======================================================================
def take_loan(state: GameState, bank_account_id: int, amount: int) -> dict:
    """Take out a loan on a bank account."""
    acct = next(
        (a for a in state.bank_accounts if a.id == bank_account_id and a.is_player),
        None,
    )
    if acct is None:
        return {"success": False, "error": "Account not found"}

    max_loan = state.player.credit_rating * 1000
    if acct.loan_amount + amount > max_loan:
        return {"success": False, "error": f"Exceeds credit limit ({max_loan}c)"}

    interest_rate = 0.10  # 10% base
    loan = LoanRecord(
        id=state.next_loan_id,
        bank_account_id=bank_account_id,
        amount=amount,
        interest_rate=interest_rate,
        created_at_tick=state.clock.tick_count,
        due_at_tick=state.clock.tick_count + 5000, # NEW: 5000 ticks to repay
    )
    state.next_loan_id += 1
    state.loans.append(loan)

    acct.balance += amount
    acct.loan_amount += amount
    state.player.balance = acct.balance

    return {"success": True, "loan_id": loan.id, "amount": amount}


def repay_loan(state: GameState, loan_id: int) -> dict:
    """Repay a loan in full."""
    loan = next((l_entry for l_entry in state.loans if l_entry.id == loan_id and not l_entry.is_paid), None)
    if loan is None:
        return {"success": False, "error": "Loan not found"}

    acct = next((a for a in state.bank_accounts if a.id == loan.bank_account_id), None)
    if acct is None:
        return {"success": False, "error": "Account not found"}

    if acct.balance < loan.amount:
        return {"success": False, "error": "Insufficient funds"}

    acct.balance -= loan.amount
    acct.loan_amount = max(0, acct.loan_amount - loan.amount)
    loan.is_paid = True

    if acct.is_player:
        state.player.balance = acct.balance

    return {"success": True}


def accrue_interest(state: GameState, current_tick: int) -> list[dict]:
    """Accrue interest on all outstanding loans and check for defaults."""
    events = []
    for loan in state.loans:
        if loan.is_paid:
            continue
        
        # Interest accrual
        interest = int(loan.amount * loan.interest_rate / 100)  # Per-interval
        if interest > 0:
            loan.amount += interest
            acct = next(
                (a for a in state.bank_accounts if a.id == loan.bank_account_id), None
            )
            if acct:
                acct.loan_amount = sum(
                    l_entry.amount
                    for l_entry in state.loans
                    if l_entry.bank_account_id == acct.id and not l_entry.is_paid
                )

        # Check for default/repossession
        if loan.due_at_tick is not None and current_tick > loan.due_at_tick and not loan.is_defaulted:
            loan.is_defaulted = True
            log.warning(f"LOAN DEFAULT: Account {loan.bank_account_id} defaulted on loan {loan.id}")
            
            repo_results = repossess_assets(state)
            events.append({
                "type": "loan_default",
                "loan_id": loan.id,
                "msg": f"Loan {loan.id} overdue. Assets repossessed.",
                "details": repo_results
            })
            
    return events


def process_offshore_fees(state: GameState, current_tick: int) -> list[dict]:
    """Apply maintenance fees to offshore accounts periodically."""
    events = []
    for acct in state.bank_accounts:
        if acct.is_offshore and acct.balance > 0:
            fee = max(1, int(acct.balance * 0.005)) # 0.5% fee per interval
            acct.balance -= fee
            events.append({
                "type": "bank_fee",
                "bank_ip": acct.bank_ip,
                "amount": fee,
                "msg": f"Offshore maintenance fee: {fee}c"
            })
    _sync_player_balance(state)
    return events


def repossess_assets(state: GameState) -> dict:
    """The bank's automated 'debt collection' script. Deletes software from VFS."""
    if not state.vfs.files:
        return {"success": False, "msg": "No assets found to repossess."}
    
    # Logic: Delete the highest-version software first (most valuable)
    # Filter for software type
    software_files = [f for f in state.vfs.files if f.software_type.value > 0]
    if not software_files:
        # Fallback to data files if no software
        software_files = state.vfs.files

    software_files.sort(key=lambda f: f.version, reverse=True)
    
    deleted = []
    # Delete up to 2 files as penalty
    for _ in range(min(2, len(software_files))):
        f_to_del = software_files.pop(0)
        # Remove from main state
        state.vfs.files = [f for f in state.vfs.files if f.id != f_to_del.id]
        deleted.append(f_to_del.filename)
    
    log.info(f"REPOSSESSION: Deleted {deleted}")
    return {"success": True, "deleted": deleted}


# ======================================================================
# Stock Market
# ===============================================================================
def tick_stock_market(state: GameState) -> None:
    """Apply random walk to all company stock prices."""
    rng = random.Random()
    for comp in state.world.companies:
        if comp.name in ("Government", "InterNIC"):
            continue
        comp.stock_previous_price = comp.stock_price
        change = rng.gauss(0, comp.stock_volatility) * comp.stock_price
        comp.stock_price = max(1.0, comp.stock_price + change)


def buy_stock(state: GameState, company_name: str, shares: int) -> dict:
    """Buy shares in a company."""
    comp = next((c for c in state.world.companies if c.name == company_name), None)
    if comp is None:
        return {"success": False, "error": "Company not found"}

    cost = int(comp.stock_price * shares)
    if state.player.balance < cost:
        return {"success": False, "error": "Insufficient funds"}

    state.player.balance -= cost

    # Update or create holding
    holding = next(
        (h for h in state.stock_holdings if h.company_name == company_name), None
    )
    if holding:
        total_cost = holding.purchase_price * holding.shares + cost
        holding.shares += shares
        holding.purchase_price = (
            total_cost // holding.shares if holding.shares > 0 else 0
        )
    else:
        state.stock_holdings.append(
            StockHolding(
                company_name=company_name,
                shares=shares,
                purchase_price=int(comp.stock_price),
            )
        )

    # Update player bank account
    for acct in state.bank_accounts:
        if acct.is_player:
            acct.balance = state.player.balance
            break

    return {"success": True, "shares": shares, "cost": cost}


def sell_stock(state: GameState, company_name: str, shares: int) -> dict:
    """Sell shares in a company."""
    holding = next(
        (h for h in state.stock_holdings if h.company_name == company_name), None
    )
    if holding is None or holding.shares < shares:
        return {"success": False, "error": "Not enough shares"}

    comp = next((c for c in state.world.companies if c.name == company_name), None)
    if comp is None:
        return {"success": False, "error": "Company not found"}

    revenue = int(comp.stock_price * shares)
    holding.shares -= shares
    state.player.balance += revenue

    # Clean up empty holdings
    if holding.shares <= 0:
        state.stock_holdings = [h for h in state.stock_holdings if h.shares > 0]

    # Update player bank account
    for acct in state.bank_accounts:
        if acct.is_player:
            acct.balance = state.player.balance
            break

    return {"success": True, "shares": shares, "revenue": revenue}


def get_stock_prices(state: GameState) -> list[dict]:
    """Get current stock prices for all companies."""
    return [
        {
            "company": c.name,
            "price": round(c.stock_price, 2),
            "previous": round(c.stock_previous_price, 2),
            "change": round(c.stock_price - c.stock_previous_price, 2),
        }
        for c in state.world.companies
        if c.name not in ("Government", "InterNIC")
    ]


def trigger_stock_crash(state: GameState, company_name: str, reason: str) -> None:
    """Cause an immediate drop in stock price for a company."""
    comp = next((c for c in state.world.companies if c.name == company_name), None)
    if comp is None:
        return

    comp.stock_previous_price = comp.stock_price

    # Crash severity based on reason
    multipliers = {
        "mainframe_destroyed": 0.5,  # 50% loss
        "research_stolen": 0.8,  # 20% loss
        "bank_robbery": 0.7,  # 30% loss
        "data_deleted": 0.9,  # 10% loss
    }

    multiplier = multipliers.get(reason, 0.95)
    comp.stock_price *= multiplier
    log.info(
        f"STOCK CRASH: {company_name} crashed to {comp.stock_price} due to {reason}"
    )
