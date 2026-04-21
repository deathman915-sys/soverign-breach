"""
Onlink-Clone: Server View Widget

Target server interface shown when connected to a node.
QStackedWidget with sub-screens: Login, FileServer, Console, Logs.

Data binding:
  - Reads: target computer's screens, files, logs
  - Emits: password_submitted, file_action, log_action
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QTextEdit,
    QFrame, QTabWidget,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from core.game_state import GameState
from core import constants as C


class ServerViewWidget(QWidget):
    """Target server interface with tabbed sub-screens."""

    password_submitted = Signal(str, str)     # ip, password
    file_action = Signal(str, str, str)       # ip, filename, action (copy/delete)
    log_action = Signal(str, int, str)        # ip, log_index, action (delete)
    disconnect_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(400, 300)

        self._target_ip: str = ""
        self._target_name: str = ""
        self._state: GameState | None = None
        self._authenticated: bool = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header
        header = QHBoxLayout()
        self._title = QLabel("Not Connected")
        self._title.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        header.addWidget(self._title)
        header.addStretch()
        self._disconnect_btn = QPushButton("Disconnect")
        self._disconnect_btn.clicked.connect(self.disconnect_requested.emit)
        header.addWidget(self._disconnect_btn)
        layout.addLayout(header)

        # Tabs for sub-screens
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # --- Login tab ---
        login_widget = QWidget()
        login_lay = QVBoxLayout(login_widget)
        login_lay.addStretch()

        login_frame = QFrame()
        login_inner = QVBoxLayout(login_frame)
        login_inner.addWidget(QLabel("Admin Login"))

        pw_row = QHBoxLayout()
        pw_row.addWidget(QLabel("Password:"))
        self._pw_input = QLineEdit()
        self._pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw_input.returnPressed.connect(self._on_password_submit)
        pw_row.addWidget(self._pw_input)
        login_inner.addLayout(pw_row)

        self._login_btn = QPushButton("Login")
        self._login_btn.clicked.connect(self._on_password_submit)
        login_inner.addWidget(self._login_btn)

        self._login_status = QLabel("")
        login_inner.addWidget(self._login_status)
        login_lay.addWidget(login_frame)
        login_lay.addStretch()

        self._tabs.addTab(login_widget, "Login")

        # --- Files tab ---
        files_widget = QWidget()
        files_lay = QVBoxLayout(files_widget)
        self._file_list = QListWidget()
        files_lay.addWidget(self._file_list)

        file_btns = QHBoxLayout()
        copy_btn = QPushButton("Copy")
        copy_btn.clicked.connect(lambda: self._on_file_action("copy"))
        file_btns.addWidget(copy_btn)
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(lambda: self._on_file_action("delete"))
        file_btns.addWidget(del_btn)
        files_lay.addLayout(file_btns)

        self._tabs.addTab(files_widget, "Files")

        # --- Console tab ---
        console_widget = QWidget()
        console_lay = QVBoxLayout(console_widget)
        self._console_output = QTextEdit()
        self._console_output.setReadOnly(True)
        self._console_output.setFont(QFont("Consolas", 9))
        console_lay.addWidget(self._console_output)

        self._console_input = QLineEdit()
        self._console_input.setFont(QFont("Consolas", 9))
        self._console_input.setPlaceholderText("Remote command...")
        console_lay.addWidget(self._console_input)

        self._tabs.addTab(console_widget, "Console")

        # --- Logs tab ---
        logs_widget = QWidget()
        logs_lay = QVBoxLayout(logs_widget)
        self._log_list = QListWidget()
        logs_lay.addWidget(self._log_list)

        log_btns = QHBoxLayout()
        del_log_btn = QPushButton("Delete Selected Log")
        del_log_btn.clicked.connect(self._on_log_delete)
        log_btns.addWidget(del_log_btn)
        logs_lay.addLayout(log_btns)

        self._tabs.addTab(logs_widget, "Logs")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
    def connect_to(self, state: GameState, ip: str) -> None:
        """Show the server view for the given IP."""
        self._state = state
        self._target_ip = ip
        self._authenticated = False

        comp = state.computers.get(ip)
        if comp is None:
            self._title.setText(f"??? ({ip})")
            return

        self._target_name = comp.name
        self._title.setText(f"{comp.name}  ({ip})")

        # Determine if password is needed
        has_password = any(
            s.screen_type in (C.SCREEN_PASSWORDSCREEN, C.SCREEN_HIGHSECURITYSCREEN)
            for s in comp.screens
        )

        if has_password:
            self._tabs.setCurrentIndex(0)  # Login tab
            self._login_status.setText("Password required")
            self._pw_input.clear()
            self._pw_input.setFocus()
        else:
            self._authenticated = True
            self._populate_files()
            self._populate_logs()
            self._tabs.setCurrentIndex(1)  # Files tab

    def on_authenticated(self) -> None:
        """Called when password is accepted."""
        self._authenticated = True
        self._login_status.setText("✓ Access Granted")
        self._populate_files()
        self._populate_logs()
        self._tabs.setCurrentIndex(1)

    def on_auth_failed(self) -> None:
        """Called when password is rejected."""
        self._login_status.setText("✗ Access Denied")

    def refresh(self) -> None:
        """Refresh file and log lists."""
        if self._authenticated:
            self._populate_files()
            self._populate_logs()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _populate_files(self) -> None:
        self._file_list.clear()
        if not self._state:
            return
        comp = self._state.computers.get(self._target_ip)
        if comp is None:
            return
        for f in comp.files:
            enc = f" [Encrypted Lv{f.encrypted_level}]" if f.encrypted_level else ""
            item = QListWidgetItem(f"{f.filename}  ({f.size}Gq){enc}")
            item.setData(Qt.ItemDataRole.UserRole, f.filename)
            self._file_list.addItem(item)

    def _populate_logs(self) -> None:
        self._log_list.clear()
        if not self._state:
            return
        comp = self._state.computers.get(self._target_ip)
        if comp is None:
            return
        for i, log in enumerate(comp.logs):
            if log.is_visible and not log.is_deleted:
                item = QListWidgetItem(
                    f"[{log.log_time}] {log.from_ip} ({log.from_name}): {log.subject}")
                item.setData(Qt.ItemDataRole.UserRole, i)
                self._log_list.addItem(item)

    def _on_password_submit(self) -> None:
        pw = self._pw_input.text().strip()
        if pw:
            self.password_submitted.emit(self._target_ip, pw)

    def _on_file_action(self, action: str) -> None:
        current = self._file_list.currentItem()
        if current:
            filename = current.data(Qt.ItemDataRole.UserRole)
            self.file_action.emit(self._target_ip, filename, action)

    def _on_log_delete(self) -> None:
        current = self._log_list.currentItem()
        if current:
            log_idx = current.data(Qt.ItemDataRole.UserRole)
            self.log_action.emit(self._target_ip, log_idx, "delete")
