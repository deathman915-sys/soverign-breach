from core.apps import get_registry
from core.game_state import GameState, VFSFile


def test_app_registry_exe_gating():
    """Apps should require .exe files in VFS to be available."""
    state = GameState()
    # Initially, only built-ins without exe_filename should be available
    reg = get_registry(state)
    available = reg.list_apps(state)
    app_ids = [a["app_id"] for a in available]

    # Built-in apps (no exe required) should be available
    assert "terminal" in app_ids
    assert "hardware" in app_ids
    assert "store" in app_ids
    assert "remote" in app_ids
    assert "tasks" in app_ids
    assert "memory_banks" in app_ids

    # Apps requiring .exe should NOT be available initially
    assert "map" not in app_ids
    assert "finance" not in app_ids
    assert "missions" not in app_ids

    # Add map.exe to VFS
    state.vfs.files.append(VFSFile(filename="map.exe", size_gq=1, file_type=2))

    # Now map should be available
    available_new = reg.list_apps(state)
    app_ids_new = [a["app_id"] for a in available_new]
    assert "map" in app_ids_new, "Map should now be available with map.exe"

def test_app_registry_categories():
    state = GameState()
    reg = get_registry(state)

    # Filter by category
    system_apps = reg.list_apps(state, category="system")
    for app in system_apps:
        assert app["category"] == "system"

def test_app_initialization_data():
    state = GameState()
    reg = get_registry(state)

    terminal_cls = reg.get("terminal")
    app = terminal_cls(state)
    data = app.init()

    assert "prompt" in data
    assert state.player.handle in data["prompt"]
