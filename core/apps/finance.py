"""Finance App - Banking, stocks, loans."""

from core.apps import BaseApp
from core.finance_engine import get_player_accounts, get_stock_prices


class FinanceApp(BaseApp):
    app_id = "finance"
    name = "Finance"
    category = "finance"
    icon = "F"
    window_size = (600, 550)
    exe_filename = "finance.exe"

    def init(self):
        s = self.state
        return {
            "accounts": get_player_accounts(s),
            "loans": [
                {
                    "id": loan.id,
                    "amount": loan.amount,
                    "interest_rate": loan.interest_rate,
                    "is_paid": loan.is_paid,
                    "bank_account_id": loan.bank_account_id,
                }
                for loan in s.loans
            ],
            "holdings": [
                {
                    "company": h.company_name,
                    "shares": h.shares,
                    "purchase_price": h.purchase_price,
                }
                for h in s.stock_holdings
            ],
            "stocks": get_stock_prices(s),
            "credit_rating": s.player.credit_rating,
        }
