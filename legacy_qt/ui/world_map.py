"""
Onlink-Clone: World Map Widget (High-Fidelity)

Interactive world map with detailed procedural continent outlines.
Shows Computer nodes, bounce routes, and active traces.
"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QMouseEvent, QPaintEvent, QPolygonF
)

from core.game_state import GameState


class WorldMapWidget(QWidget):
    """Interactive world map showing the network graph."""

    node_clicked = Signal(str)        # ip
    connect_requested = Signal(str)   # ip (double-click)
    maximize_requested = Signal()     # single-click empty space

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(300, 200)

        self._state: GameState | None = None
        self._selected_ip: str | None = None
        self._bounce_ips: list[str] = []
        self._hovered_ip: str | None = None
        self._node_positions: dict[str, QPointF] = {}

    def set_state(self, state: GameState) -> None:
        self._state = state
        self._rebuild_positions()
        self.update()

    def set_bounce_chain(self, ips: list[str]) -> None:
        self._bounce_ips = ips
        self.update()

    def _rebuild_positions(self) -> None:
        if not self._state: return
        self._node_positions.clear()
        ref_w, ref_h = 600.0, 300.0
        w, h = self.width() - 40, self.height() - 40

        nodes = {ip: c for ip, c in self._state.computers.items() if c.listed or ip == self._state.player.localhost_ip}
        for ip, comp in nodes.items():
            if hasattr(comp, 'x') and comp.x is not None:
                px = 20 + (comp.x / ref_w) * w
                py = 20 + (comp.y / ref_h) * h
            else:
                h1 = hash(ip) % 10000
                px = 20 + (h1 % 100) / 100.0 * w
                py = 20 + (h1 // 100) / 100.0 * h
            self._node_positions[ip] = QPointF(px, py)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._rebuild_positions()

    def paintEvent(self, event: QPaintEvent) -> None:
        if not self._state: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 10))

        self._draw_continents(painter)
        self._draw_grid(painter)
        self._draw_links(painter)
        self._draw_nodes(painter)
        painter.end()

    def _draw_continents(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor(0, 80, 200, 180), 1))
        painter.setBrush(QBrush(QColor(0, 40, 120, 60)))
        sx, sy = self.width() / 600.0, self.height() / 300.0
        
        # High-detail continent data
        continents = [
            # N. America
            [(40,60), (100,40), (160,45), (200,70), (220,120), (180,160), (140,170), (80,150), (50,100)],
            # S. America
            [(140,170), (190,175), (180,220), (160,280), (130,250), (120,200)],
            # Eurasia
            [(280,100), (320,50), (400,40), (500,50), (580,80), (570,150), (500,180), (420,160), (350,170), (300,140)],
            # Africa
            [(300,140), (360,150), (380,200), (360,260), (320,280), (280,220), (270,160)],
            # Australia
            [(500,200), (560,210), (550,260), (500,250)],
            # Greenland
            [(220,30), (260,35), (250,60), (210,55)]
        ]
        for shape in continents:
            poly = QPolygonF([QPointF(x * sx, y * sy) for x, y in shape])
            painter.drawPolygon(poly)

    def _draw_grid(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor(0, 100, 255, 40), 1))
        for x in range(0, self.width(), 50): painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 50): painter.drawLine(0, y, self.width(), y)

    def _draw_links(self, painter: QPainter) -> None:
        # Bounce / Connection lines
        conn = self._state.connection
        if conn.is_active and conn.nodes:
            painter.setPen(QPen(QColor(100, 200, 255), 2))
            for i in range(len(conn.nodes) - 1):
                p1, p2 = self._node_positions.get(conn.nodes[i].ip), self._node_positions.get(conn.nodes[i+1].ip)
                if p1 and p2: painter.drawLine(p1, p2)

    def _draw_nodes(self, painter: QPainter) -> None:
        for ip, pos in self._node_positions.items():
            comp = self._state.computers.get(ip)
            if not comp: continue
            
            color = QColor(0, 150, 255) # Default light blue
            if not comp.is_online: color = QColor(50, 50, 70)
            elif ip == self._selected_ip: color = Qt.GlobalColor.white
            elif ip == self._hovered_ip: color = QColor(150, 255, 255)
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(pos, 4, 4)
            
            if ip in (self._selected_ip, self._hovered_ip):
                painter.setPen(QPen(Qt.GlobalColor.white))
                painter.setFont(QFont("Consolas", 8))
                painter.drawText(int(pos.x()) + 8, int(pos.y()) + 4, comp.name)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            ip = self._hit_test(event.position())
            if ip:
                self._selected_ip = ip
                self.node_clicked.emit(ip)
                self.update()
            else:
                self.maximize_requested.emit()

    def _hit_test(self, pos: QPointF) -> str | None:
        for ip, node_pos in self._node_positions.items():
            if (pos - node_pos).manhattanLength() < 15: return ip
        return None
