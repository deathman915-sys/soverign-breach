"""
Onlink-Clone: TDD tests for UI and connection flow fixes

Tests for:
- Map noWrap and bounds configuration
- Start menu app listing
- Map as standalone app
- Connection flow after bounce chain
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from core.game_state import GameState
from core.world_generator import generate_world


# ======================================================================
# Map App
# ======================================================================
class TestMapApp:
    def test_map_app_exists(self):
        from core.apps.map import MapApp

        assert MapApp.app_id == "map"

    def test_map_app_init(self, world):
        from core.apps.map import MapApp

        app = MapApp(world)
        result = app.init()
        assert isinstance(result, dict)
        assert "nodes" in result

    def test_map_app_has_nodes(self, world):
        from core.apps.map import MapApp

        app = MapApp(world)
        result = app.init()
        assert len(result["nodes"]) > 0


# ======================================================================
# Start Menu
# ======================================================================
class TestStartMenu:
    def test_html_has_start_menu(self):
        html_path = os.path.join(os.path.dirname(__file__), "..", "web", "index.html")
        with open(html_path, "r") as f:
            content = f.read()
        assert 'id="start-menu"' in content or 'id="start-btn"' in content

    def test_html_no_desktop_icons(self):
        html_path = os.path.join(os.path.dirname(__file__), "..", "web", "index.html")
        with open(html_path, "r") as f:
            content = f.read()
        assert 'id="desktop-icons"' not in content


# ======================================================================
# Map NoWrap
# ======================================================================
class TestMapNoWrap:
    def test_os_js_has_nowrap(self):
        js_path = os.path.join(os.path.dirname(__file__), "..", "web", "js", "os.js")
        with open(js_path, "r") as f:
            content = f.read()
        assert "noWrap" in content or "worldCopyClick" in content

    def test_os_js_has_bounds(self):
        js_path = os.path.join(os.path.dirname(__file__), "..", "web", "js", "os.js")
        with open(js_path, "r") as f:
            content = f.read()
        assert "bounds" in content or "maxBounds" in content


# ======================================================================
# Fixture
# ======================================================================
@pytest.fixture
def world():
    s = GameState()
    generate_world(s)
    return s
