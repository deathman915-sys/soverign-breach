from dataclasses import dataclass

@dataclass
class Notification:
    text: str
    level: str
    id: int

class OSLogic:
    def __init__(self):
        self.notifications = []
        self.next_notif_id = 1
        self.speed = 1
        self.windows = ["map", "remote"] # Z-order
        self.notif_limit = 5

    def add_notification(self, text, level="info"):
        self.notifications.append(Notification(text=text, level=level, id=self.next_notif_id))
        self.next_notif_id += 1
        if len(self.notifications) > self.notif_limit:
            self.notifications.pop(0)

    def handle_hotkey(self, key):
        if key == "Space":
            self.speed = 1 if self.speed == 0 else 0
        elif key == "Escape":
            if self.windows:
                self.windows.pop() # Close top window
        elif key == "Tab":
            if len(self.windows) > 1:
                top = self.windows.pop()
                self.windows.insert(0, top)

def test_notification_queue():
    os = OSLogic()
    os.add_notification("Test 1")
    os.add_notification("Test 2")
    os.add_notification("Test 3")
    os.add_notification("Test 4")
    os.add_notification("Test 5")
    os.add_notification("Test 6") # Should drop Test 1
    
    assert len(os.notifications) == 5
    assert os.notifications[0].text == "Test 2"
    assert os.notifications[-1].text == "Test 6"

def test_hotkey_speed_toggle():
    os = OSLogic()
    assert os.speed == 1
    os.handle_hotkey("Space")
    assert os.speed == 0
    os.handle_hotkey("Space")
    assert os.speed == 1

def test_hotkey_window_cycle():
    os = OSLogic()
    # windows = ["map", "remote"] (remote is top)
    os.handle_hotkey("Tab")
    # windows = ["remote", "map"] (map is top)
    assert os.windows[-1] == "map"
    os.handle_hotkey("Tab")
    assert os.windows[-1] == "remote"

def test_hotkey_escape_close():
    os = OSLogic()
    os.handle_hotkey("Escape")
    assert "remote" not in os.windows
    os.handle_hotkey("Escape")
    assert "map" not in os.windows
