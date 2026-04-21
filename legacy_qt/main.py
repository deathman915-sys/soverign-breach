"""
Onlink-Clone: Entry Point

Launches the game engine and the QMdiArea-based test UI.
"""
import sys

from PySide6.QtWidgets import QApplication

from core.engine import GameEngine
from ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    engine = GameEngine()
    engine.new_game("TestPlayer", "NEO")

    window = MainWindow(engine)
    window.show()

    engine.start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
