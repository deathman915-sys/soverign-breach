"""
Onlink-Clone: App Registry

Central registry for all applications. Each app is a self-contained module
with a backend class and frontend JS file. Apps can be added/removed by
simply adding/removing a file from core/apps/ and web/js/apps/.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.game_state import GameState


class BaseApp:
    """Base class for all applications."""

    app_id: str = ""
    name: str = ""
    category: str = ""  # system, network, finance, tools
    icon: str = "?"
    window_size: tuple = (600, 450)
    # The filename in VFS required to run this app (e.g. "map.exe")
    # If None, app is built-in and always available
    exe_filename: str | None = None

    def __init__(self, state: GameState):
        self.state = state

    def is_available(self) -> bool:
        """Checks if the app is available to the player."""
        if self.exe_filename is None:
            return True
        return any(f.filename.lower() == self.exe_filename.lower() for f in self.state.vfs.files)

    def init(self) -> dict:
        """Called when app is first opened. Return initial data for the frontend."""
        return {}

    def expose_functions(self) -> dict:
        """Return dict of function_name -> callable for eel exposure."""
        return {}


class AppRegistry:
    """Central registry for all applications."""

    def __init__(self):
        self.apps: dict[str, type[BaseApp]] = {}

    def register(self, app_class: type[BaseApp]) -> None:
        """Register an app class."""
        self.apps[app_class.app_id] = app_class

    def unregister(self, app_id: str) -> None:
        """Remove an app from the registry."""
        self.apps.pop(app_id, None)

    def get(self, app_id: str) -> type[BaseApp] | None:
        """Get an app class by ID."""
        return self.apps.get(app_id)

    def list_apps(self, state: GameState, category: str | None = None) -> list[dict]:
        """List all registered apps that are currently available to the player."""
        result = []
        for cls in self.apps.values():
            if category and cls.category != category:
                continue

            # Check availability (VFS contents)
            # We instantiate temporarily to check
            app_instance = cls(state)
            if not app_instance.is_available():
                continue

            result.append(
                {
                    "app_id": cls.app_id,
                    "name": cls.name,
                    "category": cls.category,
                    "icon": cls.icon,
                    "window_size": cls.window_size,
                }
            )
        return result


# Global registry instance
_registry: AppRegistry | None = None


def get_registry(state: GameState) -> AppRegistry:
    """Get or create the global app registry."""
    global _registry
    if _registry is None:
        _registry = AppRegistry()
        _register_builtin_apps(_registry, state)
    return _registry


def reset_registry() -> None:
    """Reset the global registry (for testing)."""
    global _registry
    _registry = None


def _register_builtin_apps(reg: AppRegistry, state: GameState) -> None:
    """Register all built-in apps."""
    from core.apps.company import CompanyApp
    from core.apps.finance import FinanceApp
    from core.apps.hardware import HardwareApp
    from core.apps.logistics import LogisticsApp
    from core.apps.map import MapApp
    from core.apps.memory_banks import MemoryBanksApp
    from core.apps.messages import MessagesApp
    from core.apps.missions import MissionsApp
    from core.apps.news import NewsApp
    from core.apps.rankings import RankingsApp
    from core.apps.remote import RemoteApp
    from core.apps.store import StoreApp
    from core.apps.tasks import TasksApp
    from core.apps.terminal import TerminalApp
    from core.apps.tutorial import TutorialApp

    for cls in [
        TerminalApp,
        MissionsApp,
        FinanceApp,
        MessagesApp,
        HardwareApp,
        StoreApp,
        NewsApp,
        RankingsApp,
        RemoteApp,
        MapApp,
        TasksApp,
        LogisticsApp,
        CompanyApp,
        MemoryBanksApp,
        TutorialApp,
    ]:
        reg.register(cls)
