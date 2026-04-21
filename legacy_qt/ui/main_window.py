"""
Onlink-Clone: Main Window (Screenshot Overlay Paradigm)

Replicates Image 2 layout strictly without layout margins slicing up the desktop.
QMdiArea acts as the sole, full-screen background workspace.
The Map, HUD, and Bottom Menu are explicitly positioned absolute floating panels
on top of the MDI area so windows can slip underneath them or be positioned freely.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow,
    QMdiArea,
    QMdiSubWindow,
    QWidget,
    QTextEdit,
    QStackedWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QFont, QResizeEvent

from core.engine import GameEngine
from core import task_engine
from core import connection_manager

from ui.terminal_widget import TerminalWidget
from ui.hud_bar import HudBarLeft, HudBarCPU
from ui.world_map import WorldMapWidget
from ui.server_view import ServerViewWidget
from ui.software_panel import SoftwarePanel
from ui.news_widget import NewsWidget
from ui.mission_widget import MissionWidget
from ui.finance_widget import FinanceWidget
from ui.message_widget import MessageWidget
from ui.rankings_widget import RankingsWidget
from ui.hardware_hud import HardwareHUD
from ui.tool_overlay import ToolOverlayWidget, create_tool_overlay
from ui.bottom_menu import BottomMenuWidget


class CustomTitleBar(QWidget):
    """A custom title bar for QMdiSubWindow to match Uplink style exactly."""

    def __init__(self, title: str, sub_window: QMdiSubWindow):
        super().__init__(sub_window)
        self._sub = sub_window
        self.setFixedHeight(22)
        self.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0000aa, stop:1 #000044);
            border: 1px solid #0000ff;
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 2, 0)
        layout.setSpacing(5)

        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet(
            "color: white; border: none; background: transparent;"
        )
        layout.addWidget(self.title_lbl)

        layout.addStretch()

        # Close button matching screenshot (small X in box)
        self.close_btn = QPushButton("X")
        self.close_btn.setFixedSize(18, 18)
        self.close_btn.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: #000088; color: white; border: 1px solid #0000ff;
            }
            QPushButton:hover { background: #ff0000; }
        """)
        self.close_btn.clicked.connect(self._sub.close)
        layout.addWidget(self.close_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._old_pos
            self._sub.move(self._sub.x() + delta.x(), self._sub.y() + delta.y())
            self._old_pos = event.globalPosition().toPoint()


class MainWindow(QMainWindow):
    """Top-level Onlink OS window (Absolute MDI Desktop Layout)."""

    def __init__(self, engine: GameEngine) -> None:
        super().__init__()
        self._engine = engine
        self.setWindowTitle("Onlink-Clone — Agent Terminal")
        self.resize(1300, 850)
        self.setStyleSheet(self._global_style())
        self.menuBar().hide()

        # Central widget container for absolute positioning
        self._desktop = QWidget()
        self.setCentralWidget(self._desktop)

        # 1. Main Workspace (MDI Background) fills everything
        self._mdi = QMdiArea(self._desktop)
        self._mdi.setBackground(Qt.GlobalColor.black)
        self._mdi.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._mdi.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 2. FLOATING PANELS (drawn over the MDI area)
        self._hud_left = HudBarLeft(self._desktop)
        self._hud_cpu = HudBarCPU(self._desktop)

        self._world_map = WorldMapWidget(self._desktop)
        self._world_map.set_state(engine.state)
        self._world_map.setFixedSize(300, 200)

        # RIGHT SIDE WORKSPACE (The Dynamic Stack)
        self._right_stack = QStackedWidget(self._desktop)
        self._right_stack.setFixedWidth(300)
        self._right_stack.setStyleSheet(
            "background: #000000; border: 1px solid #000088;"
        )

        self._sw_panel = SoftwarePanel()
        self._news_widget = NewsWidget()
        self._mission_widget = MissionWidget(self._engine)
        self._finance_widget = FinanceWidget(self._engine)
        self._msg_widget = MessageWidget()
        self._rankings_widget = RankingsWidget()
        self._hw_hud = HardwareHUD()

        self._right_stack.addWidget(self._sw_panel)  # 0
        self._right_stack.addWidget(self._news_widget)  # 1
        self._right_stack.addWidget(self._mission_widget)  # 2
        self._right_stack.addWidget(self._finance_widget)  # 3
        self._right_stack.addWidget(self._msg_widget)  # 4
        self._right_stack.addWidget(self._rankings_widget)  # 5
        self._right_stack.addWidget(self._hw_hud)  # 6

        self._bottom_menu = BottomMenuWidget(self._desktop)

        # ========================================================
        # INNER MDI WINDOWS (Only for Remote Interfaces and Floating Tools)
        # ========================================================
        # Terminal (legacy)
        self._terminal_widget = TerminalWidget()
        self._terminal_sub = self._add_sub_window(
            "Terminal", self._terminal_widget, 500, 200
        )

        # Event Log
        self._netlog_widget = self._create_netlog()
        self._netlog_sub = self._add_sub_window("Events", self._netlog_widget, 350, 150)

        # Server View (The Central "Hacked Server" Workspace)
        self._server_view = ServerViewWidget()
        self._server_sub = self._add_sub_window(
            "Remote Server", self._server_view, 650, 500
        )
        self._server_sub.hide()

        # Tool overlays
        self._tool_overlays: dict[int, tuple[QMdiSubWindow, ToolOverlayWidget]] = {}

        # ========================================================
        # SIGNAL WIRING
        # ========================================================
        engine.events.connect("tick_completed", self._on_tick)
        engine.events.connect("task_progress", self._on_task_progress)
        engine.events.connect("task_completed", self._on_task_completed)
        engine.events.connect("world_event", self._on_world_event)
        engine.events.connect("game_over", self._on_game_over)

        self._terminal_widget.command_entered.connect(self._dispatch_command)
        self._hud_left.action_requested.connect(self._dispatch_command)
        self._bottom_menu.action_requested.connect(self._dispatch_command)

        self._world_map.connect_requested.connect(self._do_connect)
        self._world_map.node_clicked.connect(self._on_node_clicked)
        self._world_map.maximize_requested.connect(self._on_map_maximize)

        self._server_view.password_submitted.connect(self._on_password_submitted)
        self._server_view.file_action.connect(self._on_file_action)
        self._server_view.log_action.connect(self._on_log_action)
        self._server_view.disconnect_requested.connect(self._do_disconnect)

        self._sw_panel.tool_activated.connect(self._on_tool_activated)
        self._hud_cpu.cpu_allocation_changed.connect(self._on_cpu_allocation)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._periodic_refresh)
        self._refresh_timer.start(500)

    # ------------------------------------------------------------------
    # Overlay Resizing (Absolute MDI anchoring)
    # ------------------------------------------------------------------
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        w = self._desktop.width()
        h = self._desktop.height()

        # MDI fills entire screen
        self._mdi.setGeometry(0, 0, w, h)

        # Top-Left HUD
        hl_size = self._hud_left.sizeHint()
        self._hud_left.setGeometry(10, 10, hl_size.width(), hl_size.height())

        # Top-Center CPU
        hc_size = self._hud_cpu.sizeHint()
        self._hud_cpu.setGeometry(
            w // 2 - hc_size.width() // 2, 10, hc_size.width(), hc_size.height()
        )

        # Right Side Column (Persistent Map + Dynamic Stack)
        col_w = 300
        self._world_map.setGeometry(w - col_w - 10, 10, col_w, 200)
        self._right_stack.setGeometry(w - col_w - 10, 220, col_w, h - 220 - 10)

        # Bottom-Left Menu
        bm_size = self._bottom_menu.sizeHint()
        # width = 68 (radar) + 6*(33+2) = ~300 max
        self._bottom_menu.setGeometry(
            10, h - bm_size.height() - 10, 350, bm_size.height()
        )

        # If it's the first show, set default window positions securely over desktop
        if not hasattr(self, "_initial_positions_set"):
            self._terminal_sub.move(10, 100)
            self._netlog_sub.move(10, 320)
            self._server_sub.move(w // 2 - 450, h // 2 - 240)
            self._initial_positions_set = True

    # ------------------------------------------------------------------
    # Sub-window factory
    # ------------------------------------------------------------------
    def _add_sub_window(
        self, title: str, widget: QWidget, w: int, h: int
    ) -> QMdiSubWindow:
        sub = QMdiSubWindow()
        sub.setWidget(widget)
        sub.setWindowTitle(title)
        sub.resize(w, h)
        # Use standard flags to ensure system close buttons work
        sub.setWindowFlags(
            Qt.WindowType.SubWindow
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self._mdi.addSubWindow(sub)
        return sub

    def _create_netlog(self) -> QTextEdit:
        log = QTextEdit()
        log.setReadOnly(True)
        log.setFont(QFont("Consolas", 9))
        log.setStyleSheet("background: #000000; color: #88aaff; border: none;")
        return log

    # ------------------------------------------------------------------
    # Periodic refresh
    # ------------------------------------------------------------------
    def _periodic_refresh(self) -> None:
        s = self._engine.state
        self._hud_left.update_clock(s.clock.tick_count, s.clock.game_date)

        # Connection chain
        conn = s.connection
        if conn.is_active:
            chain = [n.ip for n in conn.nodes]
            self._hud_left.update_connection(chain)
            # Not showing trace in the top center HUD currently, tracking in specific tool?
        else:
            self._hud_left.update_connection(["Localhost"])

        self._hw_hud.refresh(s)
        self._world_map.update()

    # ------------------------------------------------------------------
    # Connection actions
    # ------------------------------------------------------------------
    def _do_connect(self, ip: str) -> None:
        s = self._engine.state
        bounce_ips = getattr(s, "_bounce_ips", [])
        result = connection_manager.connect(s, ip, bounce_ips)
        if result.get("success"):
            self._terminal_widget.append_success(
                f"Connected to {result['target_name']} ({ip})"
            )
            self._server_view.connect_to(s, ip)
            self._server_sub.show()
            self._server_sub.setWindowTitle(f"Target: {result['target_name']}")
            self._server_sub.raise_()
        else:
            self._terminal_widget.append_error(
                f"Connection failed: {result.get('error', '?')}"
            )

    def _do_disconnect(self) -> None:
        result = connection_manager.disconnect(self._engine.state)
        if result.get("success"):
            self._terminal_widget.append_success(
                f"Disconnected from {result['disconnected_from']}"
            )
            self._hud_left.update_connection(["Localhost"])
            self._server_sub.hide()
        else:
            self._terminal_widget.append_error("Not connected")

    # ------------------------------------------------------------------
    # Tool / Server View logic
    # ------------------------------------------------------------------
    def _on_password_submitted(self, ip: str, password: str) -> None:
        result = connection_manager.attempt_password(
            self._engine.state, "admin", password
        )
        if result.get("success"):
            self._server_view.on_authenticated()
        else:
            self._server_view.on_auth_failed()

    def _on_file_action(self, ip: str, filename: str, action: str) -> None:
        s = self._engine.state
        tool_name = "File_Copier" if action == "copy" else "File_Deleter"
        try:
            task_engine.start_task(s, tool_name, 1, ip, {"filename": filename})
            self._sw_panel.refresh(s)
        except ValueError as e:
            self._terminal_widget.append_error(str(e))

    def _on_log_action(self, ip: str, log_index: int, action: str) -> None:
        s = self._engine.state
        try:
            task_engine.start_task(s, "Log_Deleter", 2, ip, {"log_index": log_index})
        except ValueError as e:
            self._terminal_widget.append_error(str(e))

    def _on_tool_activated(self, tool_name: str, version: int) -> None:
        s = self._engine.state
        if not s.connection.is_active:
            self._terminal_widget.append_error("Connect to a server first")
            return
        try:
            task_engine.start_task(s, tool_name, version, s.connection.target_ip)
            task = s.tasks[-1]
            sub, widget = create_tool_overlay(task)
            widget.stop_requested.connect(self._on_tool_stop)
            self._mdi.addSubWindow(sub)
            count = len(self._tool_overlays)
            sub.move(
                self._desktop.width() // 2 - 100 + (count * 20), 100 + (count * 20)
            )
            sub.show()
            self._tool_overlays[task.task_id] = (sub, widget)
        except ValueError as e:
            self._terminal_widget.append_error(str(e))

    def _on_tool_stop(self, task_id: int) -> None:
        task_engine.stop_task(self._engine.state, task_id)
        if task_id in self._tool_overlays:
            sub, _ = self._tool_overlays.pop(task_id)
            sub.close()

    # ------------------------------------------------------------------
    # Engine event processors
    # ------------------------------------------------------------------
    @Slot(int)
    def _on_tick(self, tick: int) -> None:
        pass  # Realtime UI updates via timer or direct event payload

    @Slot(list)
    def _on_task_progress(self, tasks: list) -> None:
        self._hud_cpu.update_cpu(tasks, self._engine.state.gateway.cpu_speed)
        for t in tasks:
            tid = t.get("task_id")
            if tid in self._tool_overlays:
                _, widget = self._tool_overlays[tid]
                widget.update_progress(t)

    @Slot(dict)
    def _on_task_completed(self, info: dict) -> None:
        tid = info.get("task_id")
        if tid in self._tool_overlays:
            sub, _ = self._tool_overlays.pop(tid)
            sub.close()
        self._server_view.refresh()
        self._sw_panel.refresh(self._engine.state)

    @Slot(dict)
    def _on_world_event(self, evt: dict) -> None:
        self._netlog_widget.append(f"<b>Event:</b> {evt.get('type')}")

    @Slot(str)
    def _on_game_over(self, reason: str) -> None:
        self._terminal_widget.append_error(f"GAME OVER: {reason}")

    def _on_map_maximize(self) -> None:
        """Move the map from sidebar to a large MDI window (toggle)."""
        from PySide6.QtGui import QResizeEvent

        if self._world_map.parent() == self._desktop:
            # Move to MDI
            self._world_map.setParent(None)
            self._map_sub = self._add_sub_window("World Map", self._world_map, 800, 500)
            self._map_sub.show()
            self._map_sub.raise_()
        else:
            # Move back to sidebar
            for sub in self._mdi.subWindowList():
                if sub.widget() == self._world_map:
                    sub.setWidget(QWidget())  # release the widget
                    sub.close()
                    break
            self._world_map.setParent(self._desktop)
            self._world_map.setFixedSize(300, 200)
            self._world_map.show()
            self.updateGeometry()
            # Force a resize event to reposition
            self.resizeEvent(QResizeEvent(self.size(), self.size()))

    def _on_node_clicked(self, ip: str) -> None:
        pass

    def _on_cpu_allocation(self, task_id: int, pct: float) -> None:
        for t in self._engine.state.tasks:
            if t.task_id == task_id:
                t.cpu_cost_ghz = t.cpu_cost_ghz * pct
                break

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------
    @Slot(str)
    def _dispatch_command(self, cmd: str) -> None:
        print(f"DEBUG: Dispatching command: {cmd}")
        term = self._terminal_widget
        parts = cmd.lower().split()
        if not parts:
            return
        action = parts[0]

        if action == "status":
            self._hw_hud.refresh(self._engine.state)
            self._right_stack.setCurrentWidget(self._hw_hud)
            term.append_info("Accessing Hardware Status...")
        elif action == "clear":
            term._output.clear()
        elif action == "disconnect":
            self._do_disconnect()
        elif action == "hardware":
            self._hw_hud.refresh(self._engine.state)
            self._right_stack.setCurrentWidget(self._hw_hud)
        elif action == "news":
            self._news_widget.refresh(self._engine.state)
            self._right_stack.setCurrentWidget(self._news_widget)
        elif action == "rankings":
            self._rankings_widget.refresh(self._engine.state)
            self._right_stack.setCurrentWidget(self._rankings_widget)
        elif action == "missions":
            self._mission_widget.refresh(self._engine.state)
            self._right_stack.setCurrentWidget(self._mission_widget)
        elif action == "bank":
            self._finance_widget.refresh(self._engine.state)
            self._right_stack.setCurrentWidget(self._finance_widget)
        elif action == "messages":
            self._msg_widget.refresh(self._engine.state)
            self._right_stack.setCurrentWidget(self._msg_widget)
        elif action == "store":
            from core.game_state import SoftwareType

            self._sw_panel.set_filter(SoftwareType.CRACKERS)
            self._sw_panel.refresh(self._engine.state)
            self._right_stack.setCurrentWidget(self._sw_panel)
        elif action == "store_util":
            from core.game_state import SoftwareType

            self._sw_panel.set_filter(SoftwareType.FILE_UTIL)
            self._sw_panel.refresh(self._engine.state)
            self._right_stack.setCurrentWidget(self._sw_panel)
        elif action == "store_sec":
            from core.game_state import SoftwareType

            self._sw_panel.set_filter(SoftwareType.LOG_TOOLS)
            self._sw_panel.refresh(self._engine.state)
            self._right_stack.setCurrentWidget(self._sw_panel)
        elif action in ["0", "1", "5"]:
            pass  # speed commands mapped
        elif action == "speed" and len(parts) > 1:
            self._engine.set_speed(int(parts[1]))
        elif action == "nodes":
            self._world_map.update()
        else:
            term.append_error(f"Dispatched: {cmd}")

    @staticmethod
    def _global_style() -> str:
        return """
            QMainWindow, QMdiArea, QWidget { 
                background-color: #000000; 
                color: #FFFFFF; 
            }
            QMdiSubWindow {
                border: 1px solid #0000AA;
                background-color: #000000;
            }
            #remote_list {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #000022, stop:1 #000000);
                border: 1px solid #0000aa;
            }
            
            QScrollBar:horizontal { border: none; background: #000000; height: 10px; }
            QScrollBar::handle:horizontal { background: #0000aa; }
            QScrollBar:vertical { border: none; background: #000000; width: 10px; }
            QScrollBar::handle:vertical { background: #0000aa; }
        """
