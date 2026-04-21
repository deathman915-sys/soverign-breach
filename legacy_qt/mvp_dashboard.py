"""
Onlink-Clone: Heist MVP Debug Dashboard

Provides a simple PySide6 UI to click through the Heist Scenario sequence.
Sequence: Route -> Connect -> Crack -> Copy -> Disconnect -> Ghost (Clear Logs).
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTextEdit, QProgressBar
)
from PySide6.QtCore import QTimer

from core.engine import GameEngine
from core.scenario_heist import init_heist_scenario
from core import connection_manager

class MVPDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Onlink-Clone: Heist MVP Dashboard")
        self.resize(800, 600)

        # Init Engine and Scenario
        self.engine = GameEngine()
        init_heist_scenario(self.engine.state)
        
        self._setup_ui()
        self._wire_engine()
        
        # UI Update Timer (since engine is threaded)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._refresh_ui)
        self.update_timer.start(100) # 10Hz UI refresh

        self.engine.start()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Status HUD
        hud = QHBoxLayout()
        self.clock_lbl = QLabel("Tick: 0")
        self.conn_lbl = QLabel("Target: None")
        self.trace_bar = QProgressBar()
        self.trace_bar.setRange(0, 100)
        self.trace_bar.setFormat("Trace: %p%")
        hud.addWidget(self.clock_lbl)
        hud.addWidget(self.conn_lbl)
        hud.addWidget(self.trace_bar)
        layout.addLayout(hud)

        # Action Buttons
        btns = QHBoxLayout()
        self.btn_route = QPushButton("1. SET ROUTE (NIC->Proxy)")
        self.btn_connect = QPushButton("2. CONNECT TO TARGET")
        self.btn_crack = QPushButton("3. RUN CRACKER (5s)")
        self.btn_copy = QPushButton("4. COPY SECRET.DAT")
        self.btn_disconnect = QPushButton("5. DISCONNECT")
        self.btn_ghost = QPushButton("6. CLEAR NIC LOGS")
        
        for b in [self.btn_route, self.btn_connect, self.btn_crack, self.btn_copy, self.btn_disconnect, self.btn_ghost]:
            btns.addWidget(b)
        layout.addLayout(btns)

        # Console Output
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("background: black; color: #00ff00; font-family: Consolas;")
        layout.addWidget(self.log_view)

        # Data Views (Nodes and Logs)
        data_lay = QHBoxLayout()
        self.nodes_view = QTextEdit()
        self.nodes_view.setReadOnly(True)
        self.logs_view = QTextEdit()
        self.logs_view.setReadOnly(True)
        data_lay.addWidget(self.nodes_view)
        data_lay.addWidget(self.logs_view)
        layout.addLayout(data_lay)

        # Wire Buttons
        self.btn_route.clicked.connect(self._do_route)
        self.btn_connect.clicked.connect(self._do_connect)
        self.btn_crack.clicked.connect(self._do_crack)
        self.btn_copy.clicked.connect(self._do_copy)
        self.btn_disconnect.clicked.connect(self._do_disconnect)
        self.btn_ghost.clicked.connect(self._do_ghost)

    def _wire_engine(self):
        self.engine.events.connect("game_over", self._on_game_over)

    def _on_game_over(self, reason: str):
        # This is called from the engine thread
        print(f"GAME OVER: {reason}")
        self._append_log(f"*** GAME OVER: {reason} ***")
        # Lock the UI
        self.setEnabled(False)

    def _append_log(self, msg: str):
        self.log_view.append(msg)

    # --- Actions ---

    def _do_route(self):
        # Define the bounce chain
        self.engine.state._bounce_ips = ["100.100.100.1", "200.200.200.2"]
        self._append_log("Route established: Localhost -> InterNIC -> Proxy")

    def _do_connect(self):
        target_ip = "4.4.4.4"
        res = connection_manager.connect(self.engine.state, target_ip, self.engine.state._bounce_ips)
        if res.get("success"):
            self._append_log(f"Connected to {res['target_name']}")
        else:
            self._append_log(f"Connection Failed: {res.get('error')}")

    def _do_crack(self):
        if not self.engine.state.connection.is_active:
            self._append_log("Error: Not connected to target")
            return
        
        self._append_log("Password Breaker started (5s)...")
        # Start the trace (15s duration)
        self.engine.start_active_trace(15.0)
        self._append_log("ACTIVE TRACE DETECTED!")
        
        # Run cracker
        self.engine.run_password_breaker(5.0, lambda: self._append_log("Password Cracked! VFS Unlocked."))

    def _do_copy(self):
        if self.engine.copy_file_to_localhost("secret.dat"):
            self._append_log("File 'secret.dat' copied to Localhost VFS.")
        else:
            self._append_log("Copy Failed: Check connection or target files.")

    def _do_disconnect(self):
        connection_manager.disconnect(self.engine.state)
        self._append_log("Disconnected. Trace stopped.")

    def _do_ghost(self):
        # Connect to NIC to clear logs
        nic_ip = "100.100.100.1"
        connection_manager.connect(self.engine.state, nic_ip)
        self._append_log(f"Connected to {nic_ip} (InterNIC)")
        
        # Find log pointing to localhost
        target = self.engine.state.computers.get(nic_ip)
        for i, l in enumerate(target.logs):
            if l.from_ip == "127.0.0.1" and not l.is_deleted:
                self.engine.delete_log_on_target(i)
                self._append_log(f"Deleted connection log at index {i}")
        
        connection_manager.disconnect(self.engine.state)

    def _refresh_ui(self):
        s = self.engine.state
        self.clock_lbl.setText(f"Tick: {s.clock.tick_count}")
        
        conn = s.connection
        self.conn_lbl.setText(f"Target: {conn.target_ip or 'None'}")
        self.trace_bar.setValue(int(conn.trace_progress * 100))

        # Update Nodes view
        nodes_txt = "NETWORK NODES:\n"
        for c in s.computers.values():
            nodes_txt += f" - {c.name} ({c.ip})\n"
            if c.ip == "127.0.0.1":
                nodes_txt += f"   VFS: {[f.filename for f in s.vfs.files]}\n"
        self.nodes_view.setText(nodes_txt)

        # Update Logs view
        if conn.is_active:
            target = s.computers.get(conn.target_ip)
            logs_txt = f"LOGS ON {target.name}:\n"
            for i, l in enumerate(target.logs):
                status = "[DELETED]" if l.is_deleted else ""
                logs_txt += f" {i}. {l.from_ip} -> {l.subject} {status}\n"
            self.logs_view.setText(logs_txt)
        else:
            self.logs_view.setText("Not connected to see logs.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MVPDashboard()
    window.show()
    sys.exit(app.exec())
