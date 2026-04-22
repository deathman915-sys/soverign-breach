/**
 * Onlink OS - Finance Module
 * Banking, Stocks, Loans
 */
let currentFinanceTab = 'bank';

async function refreshFinance() {
    if (currentFinanceTab === 'bank') await refreshBanking();
    else if (currentFinanceTab === 'stocks') await refreshStocks();
    else if (currentFinanceTab === 'loans') await refreshLoans();
}

async function refreshBanking() {
    const fin = await eel.get_finance_state()();
    const container = document.getElementById('fin-bank');
    if (!container) return;

    let html = `<div style="margin-bottom:15px;">
        <div style="color:var(--yellow); font-weight:bold; margin-bottom:10px;">YOUR ACCOUNTS</div>`;

    if (fin.accounts.length === 0) {
        html += `<div style="color:#444; margin-bottom:15px;">No bank accounts. Open one at a bank server.</div>`;
    } else {
        fin.accounts.forEach(a => {
            html += `<div style="border:1px solid var(--p-blue); padding:10px; margin-bottom:8px; background:rgba(0,170,255,0.03);">
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:var(--cyan);">Account #${a.account_number}</span>
                    <span style="color:var(--green);">${a.balance.toLocaleString()}c</span>
                </div>
                <div style="font-size:9px; color:#666;">Bank: ${a.bank_ip} | Loans: ${a.loan_amount.toLocaleString()}c</div>
            </div>`;
        });
    }

    html += `<div style="margin-top:15px; border-top:1px solid #333; padding-top:15px;">
        <div style="color:var(--yellow); font-weight:bold; margin-bottom:10px;">TRANSFER FUNDS</div>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
            <select id="transfer-from" style="flex:1; background:#0a0a0a; border:1px solid #333; color:white; padding:5px; font-family:inherit;">
                <option value="">From Account</option>
                ${fin.accounts.map(a => `<option value="${a.id}">#${a.account_number} (${a.balance}c)</option>`).join('')}
            </select>
            <select id="transfer-to" style="flex:1; background:#0a0a0a; border:1px solid #333; color:white; padding:5px; font-family:inherit;">
                <option value="">To Account</option>
                ${fin.accounts.map(a => `<option value="${a.id}">#${a.account_number}</option>`).join('')}
            </select>
            <input id="transfer-amount" type="number" placeholder="Amount" style="width:100px; background:#0a0a0a; border:1px solid #333; color:white; padding:5px; font-family:inherit;" />
            <button class="menu-btn" onclick="doTransfer()">TRANSFER</button>
        </div>
    </div></div>`;

    container.innerHTML = html;
}

async function doTransfer() {
    const fromId = parseInt(document.getElementById('transfer-from').value);
    const toId = parseInt(document.getElementById('transfer-to').value);
    const amount = parseInt(document.getElementById('transfer-amount').value);
    if (!fromId || !toId || !amount) { alert('Fill in all fields'); return; }
    if (fromId === toId) { alert('Cannot transfer to same account'); return; }
    const res = await eel.transfer_money(fromId, toId, amount)();
    if (res.success) { alert(`Transferred ${amount}c`); refreshFinance(); }
    else { alert(`Failed: ${res.error}`); }
}

async function refreshStocks() {
    const fin = await eel.get_finance_state()();
    const container = document.getElementById('fin-stocks');
    if (!container) return;

    let html = `<div style="margin-bottom:15px;">
        <div style="color:var(--yellow); font-weight:bold; margin-bottom:10px;">YOUR PORTFOLIO</div>`;

    if (fin.holdings.length === 0) {
        html += `<div style="color:#444; margin-bottom:15px;">No stock holdings.</div>`;
    } else {
        fin.holdings.forEach(h => {
            const current = fin.stocks.find(s => s.company === h.company);
            const price = current ? current.price : h.purchase_price;
            const value = price * h.shares;
            const cost = h.purchase_price * h.shares;
            const pnl = value - cost;
            html += `<div style="border:1px solid var(--p-blue); padding:10px; margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:var(--cyan);">${h.company}</span>
                    <span style="color:${pnl >= 0 ? 'var(--green)' : 'var(--red)'};">${pnl >= 0 ? '+' : ''}${pnl.toLocaleString()}c</span>
                </div>
                <div style="font-size:9px; color:#666;">${h.shares} shares @ ${price}c | Avg cost: ${h.purchase_price}c</div>
                <div style="display:flex; gap:5px; margin-top:5px;">
                    <button class="menu-btn" style="font-size:9px; padding:3px 8px;" onclick="buyShares('${h.company}')">BUY MORE</button>
                    <button class="menu-btn" style="font-size:9px; padding:3px 8px; background:var(--red);" onclick="sellShares('${h.company}', ${h.shares})">SELL ALL</button>
                </div>
            </div>`;
        });
    }

    html += `</div><div style="border-top:1px solid #333; padding-top:15px;">
        <div style="color:var(--yellow); font-weight:bold; margin-bottom:10px;">MARKET</div>
        <table style="width:100%; font-size:10px; border-collapse:collapse;">
            <tr style="color:#666;"><th style="text-align:left; padding:3px;">Company</th><th>Price</th><th>Change</th><th></th></tr>
            ${fin.stocks.map(s => `<tr style="border-bottom:1px solid #222;">
                <td style="padding:4px; color:var(--cyan);">${s.company}</td>
                <td style="text-align:right;">${s.price}c</td>
                <td style="text-align:right; color:${s.change >= 0 ? 'var(--green)' : 'var(--red)'};">${s.change >= 0 ? '+' : ''}${s.change}</td>
                <td style="text-align:right;"><button class="menu-btn" style="font-size:9px; padding:2px 6px;" onclick="buyShares('${s.company}')">BUY</button></td>
            </tr>`).join('')}
        </table>
    </div>`;

    container.innerHTML = html;
}

async function buyShares(company) {
    const shares = parseInt(prompt(`Buy shares in ${company}:`, '10'));
    if (!shares || shares <= 0) return;
    const res = await eel.buy_stock(company, shares)();
    if (res.success) { alert(`Bought ${shares} shares for ${res.cost}c`); refreshFinance(); }
    else { alert(`Failed: ${res.error}`); }
}

async function sellShares(company, maxShares) {
    const shares = parseInt(prompt(`Sell shares in ${company} (max ${maxShares}):`, maxShares));
    if (!shares || shares <= 0) return;
    const res = await eel.sell_stock(company, shares)();
    if (res.success) { alert(`Sold ${shares} shares for ${res.revenue}c`); refreshFinance(); }
    else { alert(`Failed: ${res.error}`); }
}

async function refreshLoans() {
    const fin = await eel.get_finance_state()();
    const container = document.getElementById('fin-loans');
    if (!container) return;

    let html = `<div style="margin-bottom:15px;">
        <div style="color:var(--yellow); font-weight:bold; margin-bottom:10px;">YOUR LOANS</div>`;

    if (fin.loans.length === 0) {
        html += `<div style="color:#444; margin-bottom:15px;">No outstanding loans.</div>`;
    } else {
        fin.loans.forEach(l => {
            html += `<div style="border:1px solid ${l.is_paid ? '#333' : 'var(--orange)'}; padding:10px; margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:var(--cyan);">Loan #${l.id}</span>
                    <span style="color:var(--orange);">${l.amount.toLocaleString()}c</span>
                </div>
                <div style="font-size:9px; color:#666;">Interest: ${(l.interest_rate * 100).toFixed(1)}% | ${l.is_paid ? 'PAID' : 'OUTSTANDING'}</div>
                ${!l.is_paid ? `<button class="menu-btn" style="margin-top:5px; font-size:9px; padding:3px 8px;" onclick="repayLoan(${l.id})">REPAY</button>` : ''}
            </div>`;
        });
    }

    html += `</div><div style="border-top:1px solid #333; padding-top:15px;">
        <div style="color:var(--yellow); font-weight:bold; margin-bottom:10px;">TAKE A LOAN</div>
        <div style="color:#666; font-size:10px; margin-bottom:10px;">Credit Rating: ${fin.credit_rating} (Max loan: ${fin.credit_rating * 1000}c)</div>
        <div style="display:flex; gap:10px;">
            <select id="loan-account" style="flex:1; background:#0a0a0a; border:1px solid #333; color:white; padding:5px; font-family:inherit;">
                <option value="">Select Account</option>
                ${fin.accounts.map(a => `<option value="${a.id}">#${a.account_number}</option>`).join('')}
            </select>
            <input id="loan-amount" type="number" placeholder="Amount" style="width:100px; background:#0a0a0a; border:1px solid #333; color:white; padding:5px; font-family:inherit;" />
            <button class="menu-btn" onclick="takeLoan()">BORROW</button>
        </div>
    </div>`;

    container.innerHTML = html;
}

async function takeLoan() {
    const acctId = parseInt(document.getElementById('loan-account').value);
    const amount = parseInt(document.getElementById('loan-amount').value);
    if (!acctId || !amount) { alert('Fill in all fields'); return; }
    const res = await eel.take_loan(acctId, amount)();
    if (res.success) { alert(`Loan taken: ${amount}c`); refreshFinance(); }
    else { alert(`Failed: ${res.error}`); }
}

async function repayLoan(loanId) {
    const res = await eel.repay_loan(loanId)();
    if (res.success) { alert('Loan repaid'); refreshFinance(); }
    else { alert(`Failed: ${res.error}`); }
}

function switchFinanceTab(tab) {
    currentFinanceTab = tab;
    document.querySelectorAll('.fin-tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('fin-tab-' + tab).classList.add('active');
    document.getElementById('fin-bank').classList.toggle('hidden', tab !== 'bank');
    document.getElementById('fin-stocks').classList.toggle('hidden', tab !== 'stocks');
    document.getElementById('fin-loans').classList.toggle('hidden', tab !== 'loans');
    refreshFinance();
}

async function openBankAccount(ip) {
    const res = await eel.open_bank_account(ip)();
    if(res.success) showNotification("Bank account opened successfully.", "info");
    else showNotification("Failed to open bank account: " + res.error, "critical");
    refreshApp('finance');
}
async function deleteTransactionLog(txHash) {
    const res = await eel.delete_transaction_log(txHash)();
    if(res.success) showNotification("Transaction log deleted.", "info");
    else showNotification("Failed to delete log.", "critical");
    refreshApp('finance');
}
