"""
Onlink-Clone: Terminal Widget

Interactive command-line interface for the player.
Supports basic commands: help, status, bounce, hack, vfs, tasks, speed, blackout.
"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QFont, QTextCursor


class TerminalWidget(QWidget):
    """
    Terminal emulator with command input.
    Emits command_entered(str) for the main window to process.
    """

    command_entered = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Output area
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setFont(QFont("Consolas", 10))
        self._output.setStyleSheet(
            "background: #0a0a0a; color: #00ff88; border: 1px solid #333;"
        )
        layout.addWidget(self._output)

        # Input line
        self._input = QLineEdit()
        self._input.setFont(QFont("Consolas", 10))
        self._input.setStyleSheet(
            "background: #0a0a0a; color: #00ff88; border: 1px solid #333; padding: 4px;"
        )
        self._input.setPlaceholderText("Enter command...")
        self._input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._input.returnPressed.connect(self._on_enter)
        self._input.installEventFilter(self)  # arrow-key history on the input itself
        layout.addWidget(self._input)

        # Command history and Tab completion
        self._history: list[str] = []
        self._history_idx = -1
        self._commands = [
            "help", "status", "bounce", "hack", "vfs", "tasks", "speed", "blackout",
            "clear", "disconnect", "hardware", "news", "rankings", "missions", "bank", "messages", "store"
        ]

        self._print_welcome()

    # ------------------------------------------------------------------
    # Focus
    # ------------------------------------------------------------------
    def showEvent(self, event) -> None:
        """Grab focus onto the input line when the terminal appears."""
        super().showEvent(event)
        self._input.setFocus()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def append_output(self, text: str) -> None:
        """Add text to the terminal output."""
        self._output.append(text)
        self._output.moveCursor(QTextCursor.MoveOperation.End)

    def append_error(self, text: str) -> None:
        self.append_output(f'<span style="color:#ff4444;">{text}</span>')

    def append_success(self, text: str) -> None:
        self.append_output(f'<span style="color:#44ff88;">{text}</span>')

    def append_info(self, text: str) -> None:
        self.append_output(f'<span style="color:#44aaff;">{text}</span>')

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _on_enter(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self._history.append(text)
        self._history_idx = -1
        self.append_output(f"<b>&gt; {text}</b>")
        self._input.clear()
        self.command_entered.emit(text)

    def _print_welcome(self) -> None:
        self.append_info("═══════════════════════════════════════")
        self.append_info("  ONLINK TERMINAL v0.1")
        self.append_info("  Type 'help' for available commands")
        self.append_info("═══════════════════════════════════════")

    # ------------------------------------------------------------------
    # Event filter — history navigation on the QLineEdit
    # ------------------------------------------------------------------
    def eventFilter(self, obj, event) -> bool:
        if obj is self._input and event.type() == QEvent.Type.KeyPress:
            # --- Tab Completion ---
            if event.key() == Qt.Key.Key_Tab:
                text = self._input.text().strip().lower()
                if not text:
                    return True
                
                matches = [c for c in self._commands if c.startswith(text)]
                if len(matches) == 1:
                    self._input.setText(matches[0])
                elif len(matches) > 1:
                    # If multiple, show them in output
                    self.append_info(f"Matches: {', '.join(matches)}")
                return True

            # --- History Navigation ---
            if event.key() == Qt.Key.Key_Up and self._history:
                if self._history_idx == -1:
                    self._history_idx = len(self._history) - 1
                elif self._history_idx > 0:
                    self._history_idx -= 1
                self._input.setText(self._history[self._history_idx])
                return True
            elif event.key() == Qt.Key.Key_Down and self._history:
                if self._history_idx < len(self._history) - 1:
                    self._history_idx += 1
                    self._input.setText(self._history[self._history_idx])
                else:
                    self._history_idx = -1
                    self._input.clear()
                return True
        return super().eventFilter(obj, event)
