from dataclasses import dataclass


@dataclass
class WindowState:
    app_id: str
    is_minimized: bool = False
    is_focused: bool = False
    z_index: int = 0
    x: int = 0
    y: int = 0
    width: int = 600
    height: int = 400

class VDELogic:
    """Mock logic for testing VDE window management."""
    def __init__(self):
        self.windows = {}
        self.z_counter = 1000

    def open_window(self, app_id, w, h):
        self.windows[app_id] = WindowState(app_id=app_id, width=w, height=h, z_index=self.z_counter)
        self.focus_window(app_id)

    def focus_window(self, app_id):
        if app_id not in self.windows:
            return
        for win in self.windows.values():
            win.is_focused = False
        self.z_counter += 1
        self.windows[app_id].is_focused = True
        self.windows[app_id].z_index = self.z_counter
        self.windows[app_id].is_minimized = False # Un-minimize on focus

    def toggle_minimize(self, app_id):
        if app_id not in self.windows:
            return
        win = self.windows[app_id]
        win.is_minimized = not win.is_minimized
        if not win.is_minimized:
            self.focus_window(app_id)
        else:
            win.is_focused = False

    def snap_to_grid(self, app_id, screen_w, screen_h, position):
        """Position: 'left', 'right', 'top', 'bottom'."""
        if app_id not in self.windows:
            return
        win = self.windows[app_id]
        if position == 'left':
            win.x, win.y = 0, 0
            win.width, win.height = screen_w // 2, screen_h
        elif position == 'right':
            win.x, win.y = screen_w // 2, 0
            win.width, win.height = screen_w // 2, screen_h

def test_window_focus_logic():
    vde = VDELogic()
    vde.open_window("map", 800, 600)
    vde.open_window("remote", 600, 400)

    assert vde.windows["remote"].is_focused is True
    assert vde.windows["map"].is_focused is False
    assert vde.windows["remote"].z_index > vde.windows["map"].z_index

def test_minimize_logic():
    vde = VDELogic()
    vde.open_window("map", 800, 600)

    vde.toggle_minimize("map")
    assert vde.windows["map"].is_minimized is True
    assert vde.windows["map"].is_focused is False

    vde.toggle_minimize("map")
    assert vde.windows["map"].is_minimized is False
    assert vde.windows["map"].is_focused is True

def test_snap_logic():
    vde = VDELogic()
    vde.open_window("map", 800, 600)
    vde.snap_to_grid("map", 1200, 800, 'left')

    assert vde.windows["map"].x == 0
    assert vde.windows["map"].width == 600
    assert vde.windows["map"].height == 800
