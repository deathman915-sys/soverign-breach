"""
Onlink-Clone: Finance Widget

Banking and Stock Market interface.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QTabWidget, QPushButton, QLineEdit, QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.game_state import GameState
from core.finance_engine import get_player_accounts, get_stock_prices, buy_stock, sell_stock


class FinanceWidget(QWidget):
    """Widget for managing money and investments."""

    def __init__(self, engine, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._engine = engine
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("FINANCIAL MANAGEMENT")
        header.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        header.setStyleSheet("color: #66ccff;")
        layout.addWidget(header)

        self._tabs = QTabWidget()
        self._tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #000088; background: #000022; }
            QTabBar::tab { background: #000044; color: #8888ff; padding: 8px; border: 1px solid #000088; }
            QTabBar::tab:selected { background: #0000aa; color: white; }
        """)
        layout.addWidget(self._tabs)

        # Tab 1: Banking
        self._bank_tab = QWidget()
        bank_lay = QVBoxLayout(self._bank_tab)
        self._acct_list = QListWidget()
        self._acct_list.setFont(QFont("Consolas", 9))
        self._acct_list.setStyleSheet("background: #000; color: #66ccff;")
        bank_lay.addWidget(QLabel("YOUR ACCOUNTS:"))
        bank_lay.addWidget(self._acct_list)
        self._tabs.addTab(self._bank_tab, "BANKING")

        # Tab 2: Stock Market
        self._stock_tab = QWidget()
        stock_lay = QVBoxLayout(self._stock_tab)
        self._stock_list = QListWidget()
        self._stock_list.setFont(QFont("Consolas", 9))
        self._stock_list.setStyleSheet("background: #000; color: #66ccff;")
        self._stock_list.itemClicked.connect(self._on_stock_clicked)
        stock_lay.addWidget(QLabel("MARKET TICKER:"))
        stock_lay.addWidget(self._stock_list)
        
        # Trade form
        trade_box = QWidget()
        trade_lay = QFormLayout(trade_box)
        self._stock_label = QLabel("Select a stock")
        self._shares_input = QLineEdit("10")
        self._shares_input.setFixedWidth(60)
        self._buy_btn = QPushButton("BUY")
        self._sell_btn = QPushButton("SELL")
        btn_row = QHBoxLayout()
        btn_row.addWidget(self._buy_btn)
        btn_row.addWidget(self._sell_btn)
        
        trade_lay.addRow("Selected:", self._stock_label)
        trade_lay.addRow("Shares:", self._shares_input)
        trade_lay.addRow(btn_row)
        stock_lay.addWidget(trade_box)
        
        self._buy_btn.clicked.connect(self._on_buy_clicked)
        self._sell_btn.clicked.connect(self._on_sell_clicked)
        self._tabs.addTab(self._stock_tab, "STOCKS")

        self.refresh(self._engine.state)

    def refresh(self, state: GameState) -> None:
        """Update account and stock lists."""
        # Refresh Bank Accounts
        self._acct_list.clear()
        accts = get_player_accounts(state)
        for a in accts:
            text = f"Acc #{a['account_number']} @ {a['bank_ip']} | Balance: {a['balance']}c"
            if a['loan_amount'] > 0:
                text += f" | Loan: {a['loan_amount']}c"
            self._acct_list.addItem(text)

        # Refresh Stocks
        self._stock_list.clear()
        stocks = get_stock_prices(state)
        for s in stocks:
            sign = "+" if s['change'] >= 0 else ""
            item = QListWidgetItem(f"{s['company']:<20} {s['price']:>8}c  ({sign}{s['change']})")
            item.setForeground(Qt.GlobalColor.white)
            item.setData(Qt.ItemDataRole.UserRole, s)
            self._stock_list.addItem(item)
            
        # Update balance info if we had a label for it (optional)

    def _on_stock_clicked(self, item: QListWidgetItem) -> None:
        s = item.data(Qt.ItemDataRole.UserRole)
        if s:
            self._stock_label.setText(f"{s['company']} ({s['price']}c)")

    def _on_buy_clicked(self) -> None:
        item = self._stock_list.currentItem()
        if not item: return
        s = item.data(Qt.ItemDataRole.UserRole)
        try:
            shares = int(self._shares_input.text())
            res = buy_stock(self._engine.state, s['company'], shares)
            if res.get("success"):
                QMessageBox.information(self, "Trade Executed", f"Bought {shares} shares of {s['company']}.")
                self.refresh(self._engine.state)
            else:
                QMessageBox.warning(self, "Trade Failed", res.get("error", "Error"))
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Invalid share count")

    def _on_sell_clicked(self) -> None:
        item = self._stock_list.currentItem()
        if not item: return
        s = item.data(Qt.ItemDataRole.UserRole)
        try:
            shares = int(self._shares_input.text())
            res = sell_stock(self._engine.state, s['company'], shares)
            if res.get("success"):
                QMessageBox.information(self, "Trade Executed", f"Sold {shares} shares of {s['company']}.")
                self.refresh(self._engine.state)
            else:
                QMessageBox.warning(self, "Trade Failed", res.get("error", "Error"))
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Invalid share count")
