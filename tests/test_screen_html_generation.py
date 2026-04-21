"""
Onlink-Clone: TDD tests for Python-generated screen HTML

All server screens should generate HTML from the backend (Python),
not the frontend (JS). This ensures a single source of truth for
UI logic and makes rendering testable.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from core.game_state import GameState
from core.world_generator import generate_world
from core import constants as C
from core.remote_controller import RemoteController


@pytest.fixture
def world():
    s = GameState()
    generate_world(s)
    return s


@pytest.fixture
def rc(world):
    return RemoteController(world)


# ======================================================================
# HTML Generation Helpers
# ======================================================================
class TestHTMLGenerationBasics:
    """Verify that all screen types return an 'html' key."""

    def test_menu_screen_has_html(self, rc, world):
        rc.connect(C.IP_INTERNIC)
        data = rc.get_screen_data(C.IP_INTERNIC)
        assert "html" in data, "Menu screen should return pre-generated HTML"
        assert isinstance(data["html"], str)
        assert len(data["html"]) > 0

    def test_bbs_screen_has_html(self, rc, world):
        # Find a server with BBS
        for comp in world.computers.values():
            if any(s.screen_type == C.SCREEN_BBSSCREEN for s in comp.screens):
                rc.connect(comp.ip)
                rc.navigate_screen(comp.ip, C.SCREEN_BBSSCREEN)
                data = rc.get_screen_data(comp.ip)
                assert "html" in data, "BBS screen should return pre-generated HTML"
                assert isinstance(data["html"], str)
                break

    def test_software_sales_screen_has_html(self, rc, world):
        # Find Uplink Internal Services (has software sales)
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_SWSALESSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        assert "html" in data, "Software sales screen should return pre-generated HTML"
        assert isinstance(data["html"], str)

    def test_hardware_sales_screen_has_html(self, rc, world):
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_HWSALESSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        assert "html" in data, "Hardware sales screen should return pre-generated HTML"
        assert isinstance(data["html"], str)

    def test_news_screen_has_html(self, rc, world):
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_NEWSSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        assert "html" in data, "News screen should return pre-generated HTML"
        assert isinstance(data["html"], str)

    def test_rankings_screen_has_html(self, rc, world):
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_RANKINGSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        assert "html" in data, "Rankings screen should return pre-generated HTML"
        assert isinstance(data["html"], str)

    def test_file_server_screen_has_html(self, rc, world):
        # Find a server with files
        for comp in world.computers.values():
            if comp.files and any(s.screen_type == C.SCREEN_FILESERVERSCREEN for s in comp.screens):
                rc.connect(comp.ip)
                rc.navigate_screen(comp.ip, C.SCREEN_FILESERVERSCREEN)
                data = rc.get_screen_data(comp.ip)
                assert "html" in data, "File server screen should return pre-generated HTML"
                assert isinstance(data["html"], str)
                break

    def test_logs_screen_has_html(self, rc, world):
        # Find a server with logs
        for comp in world.computers.values():
            if comp.logs and any(s.screen_type == C.SCREEN_LOGSCREEN for s in comp.screens):
                rc.connect(comp.ip)
                rc.navigate_screen(comp.ip, C.SCREEN_LOGSCREEN)
                data = rc.get_screen_data(comp.ip)
                assert "html" in data, "Logs screen should return pre-generated HTML"
                assert isinstance(data["html"], str)
                break

    def test_links_screen_has_html(self, rc, world):
        rc.connect(C.IP_INTERNIC)
        rc.navigate_screen(C.IP_INTERNIC, C.SCREEN_LINKSSCREEN)
        data = rc.get_screen_data(C.IP_INTERNIC)
        assert "html" in data, "Links screen should return pre-generated HTML"
        assert isinstance(data["html"], str)

    def test_console_screen_has_html(self, rc, world):
        # Find a server with console
        for comp in world.computers.values():
            if any(s.screen_type == C.SCREEN_CONSOLESCREEN for s in comp.screens):
                rc.connect(comp.ip)
                rc.navigate_screen(comp.ip, C.SCREEN_CONSOLESCREEN)
                data = rc.get_screen_data(comp.ip)
                assert "html" in data, "Console screen should return pre-generated HTML"
                assert isinstance(data["html"], str)
                break

    def test_password_screen_has_html(self, rc, world):
        # Find a server with password screen
        for comp in world.computers.values():
            if any(s.screen_type == C.SCREEN_PASSWORDSCREEN for s in comp.screens):
                rc.connect(comp.ip)
                rc.navigate_screen(comp.ip, C.SCREEN_PASSWORDSCREEN)
                data = rc.get_screen_data(comp.ip)
                assert "html" in data, "Password screen should return pre-generated HTML"
                assert isinstance(data["html"], str)
                break


# ======================================================================
# Software Sales Screen HTML
# ======================================================================
class TestSoftwareSalesHTML:
    def test_html_contains_software_names(self, rc, world):
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_SWSALESSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        html = data["html"]
        # Should contain at least one software name from catalog
        from core.store_engine import get_software_catalog
        catalog = get_software_catalog()
        found = any(item["name"] in html for item in catalog)
        assert found, f"HTML should contain software names from catalog. Got: {html[:200]}"

    def test_html_contains_prices(self, rc, world):
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_SWSALESSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        html = data["html"]
        from core.store_engine import get_software_catalog
        catalog = get_software_catalog()
        found = any(str(item["price"]) in html for item in catalog)
        assert found, f"HTML should contain prices. Got: {html[:200]}"

    def test_html_contains_buy_buttons(self, rc, world):
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_SWSALESSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        html = data["html"]
        assert "serverBuySoftware" in html, f"HTML should contain serverBuySoftware onclick handler. Got: {html[:200]}"

    def test_html_contains_version_info(self, rc, world):
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_SWSALESSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        html = data["html"]
        # Should show version for versioned software
        from core.store_engine import get_software_catalog
        catalog = get_software_catalog()
        versioned = [item for item in catalog if item.get("version", 1) > 1]
        if versioned:
            found = any(f"v{item['version']}" in html or f"v{item.get('version', 1)}" in html for item in versioned[:3])
            assert found, f"HTML should show version info. Got: {html[:200]}"


# ======================================================================
# Hardware Sales Screen HTML
# ======================================================================
class TestHardwareSalesHTML:
    def test_html_contains_gateway_names(self, rc, world):
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_HWSALESSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        html = data["html"]
        from core.store_engine import get_hardware_catalog
        gateways = get_hardware_catalog()
        found = any(gw["name"] in html for gw in gateways)
        assert found, f"HTML should contain gateway names. Got: {html[:200]}"

    def test_html_contains_cooling_names(self, rc, world):
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_HWSALESSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        html = data["html"]
        from core.store_engine import get_cooling_catalog
        cooling = get_cooling_catalog()
        found = any(c["name"] in html for c in cooling)
        assert found, f"HTML should contain cooling names. Got: {html[:200]}"

    def test_html_contains_psu_names(self, rc, world):
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_HWSALESSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        html = data["html"]
        from core.store_engine import get_psu_catalog
        psus = get_psu_catalog()
        found = any(p["name"] in html for p in psus)
        assert found, f"HTML should contain PSU names. Got: {html[:200]}"

    def test_html_contains_addon_names(self, rc, world):
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_HWSALESSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        html = data["html"]
        from core.store_engine import get_addon_catalog
        addons = get_addon_catalog()
        if addons:
            found = any(a["name"] in html for a in addons)
            assert found, f"HTML should contain addon names. Got: {html[:200]}"

    def test_html_contains_gateway_buy_button(self, rc, world):
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_HWSALESSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        html = data["html"]
        assert "serverBuyGateway" in html, f"HTML should contain serverBuyGateway onclick. Got: {html[:200]}"

    def test_html_contains_cooling_buy_button(self, rc, world):
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_HWSALESSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        html = data["html"]
        assert "serverBuyCooling" in html, f"HTML should contain serverBuyCooling onclick. Got: {html[:200]}"

    def test_html_contains_psu_buy_button(self, rc, world):
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_HWSALESSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        html = data["html"]
        assert "serverBuyPSU" in html, f"HTML should contain serverBuyPSU onclick. Got: {html[:200]}"

    def test_html_contains_addon_buy_button(self, rc, world):
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_HWSALESSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        html = data["html"]
        from core.store_engine import get_addon_catalog
        addons = get_addon_catalog()
        if addons:
            assert "serverBuyAddon" in html, f"HTML should contain serverBuyAddon onclick. Got: {html[:200]}"


# ======================================================================
# BBS Screen HTML
# ======================================================================
class TestBBSHTML:
    def test_html_contains_mission_info(self, rc, world):
        # Find server with BBS
        for comp in world.computers.values():
            if any(s.screen_type == C.SCREEN_BBSSCREEN for s in comp.screens):
                rc.connect(comp.ip)
                rc.navigate_screen(comp.ip, C.SCREEN_BBSSCREEN)
                data = rc.get_screen_data(comp.ip)
                html = data["html"]
                # BBS should either show missions or "no missions" message
                assert "ACCEPT" in html or "No missions" in html or "mission" in html.lower(), \
                    f"BBS HTML should show missions or placeholder. Got: {html[:200]}"
                break

    def test_html_contains_accept_button(self, rc, world):
        for comp in world.computers.values():
            if any(s.screen_type == C.SCREEN_BBSSCREEN for s in comp.screens):
                rc.connect(comp.ip)
                rc.navigate_screen(comp.ip, C.SCREEN_BBSSCREEN)
                data = rc.get_screen_data(comp.ip)
                html = data["html"]
                # Should have accept mission button or indicate no missions
                assert "serverAcceptMission" in html or "No missions" in html, \
                    f"BBS HTML should have accept button or no missions message. Got: {html[:200]}"
                break

    def test_html_contains_negotiate_button(self, rc, world):
        for comp in world.computers.values():
            if any(s.screen_type == C.SCREEN_BBSSCREEN for s in comp.screens):
                rc.connect(comp.ip)
                rc.navigate_screen(comp.ip, C.SCREEN_BBSSCREEN)
                data = rc.get_screen_data(comp.ip)
                html = data["html"]
                assert "serverNegotiateMission" in html or "No missions" in html, \
                    f"BBS HTML should have negotiate button or no missions message. Got: {html[:200]}"
                break


# ======================================================================
# File Server Screen HTML
# ======================================================================
class TestFileServerHTML:
    def test_html_contains_file_names(self, rc, world):
        for comp in world.computers.values():
            if comp.files and any(s.screen_type == C.SCREEN_FILESERVERSCREEN for s in comp.screens):
                rc.connect(comp.ip)
                rc.navigate_screen(comp.ip, C.SCREEN_FILESERVERSCREEN)
                data = rc.get_screen_data(comp.ip)
                html = data["html"]
                for f in comp.files[:3]:  # Check first 3 files
                    if f.filename:
                        assert f.filename in html, f"HTML should contain file name {f.filename}. Got: {html[:200]}"
                break

    def test_html_contains_copy_button(self, rc, world):
        for comp in world.computers.values():
            if comp.files and any(s.screen_type == C.SCREEN_FILESERVERSCREEN for s in comp.screens):
                rc.connect(comp.ip)
                rc.navigate_screen(comp.ip, C.SCREEN_FILESERVERSCREEN)
                data = rc.get_screen_data(comp.ip)
                html = data["html"]
                assert "serverCopyFile" in html or "No files" in html, \
                    f"File server HTML should have copy button. Got: {html[:200]}"
                break

    def test_html_contains_delete_button(self, rc, world):
        for comp in world.computers.values():
            if comp.files and any(s.screen_type == C.SCREEN_FILESERVERSCREEN for s in comp.screens):
                rc.connect(comp.ip)
                rc.navigate_screen(comp.ip, C.SCREEN_FILESERVERSCREEN)
                data = rc.get_screen_data(comp.ip)
                html = data["html"]
                assert "serverDeleteFile" in html or "No files" in html, \
                    f"File server HTML should have delete button. Got: {html[:200]}"
                break


# ======================================================================
# Logs Screen HTML
# ======================================================================
class TestLogsHTML:
    def test_html_contains_log_entries(self, rc, world):
        for comp in world.computers.values():
            if comp.logs and any(s.screen_type == C.SCREEN_LOGSCREEN for s in comp.screens):
                rc.connect(comp.ip)
                rc.navigate_screen(comp.ip, C.SCREEN_LOGSCREEN)
                data = rc.get_screen_data(comp.ip)
                html = data["html"]
                # Should show log entries or "Empty" message
                assert "interactWithIP" in html or "Empty" in html or "No logs" in html or "empty" in html.lower(), \
                    f"Logs HTML should show log entries or empty message. Got: {html[:200]}"
                break


# ======================================================================
# Links Screen HTML
# ======================================================================
class TestLinksHTML:
    def test_html_contains_links_or_empty(self, rc, world):
        rc.connect(C.IP_INTERNIC)
        rc.navigate_screen(C.IP_INTERNIC, C.SCREEN_LINKSSCREEN)
        data = rc.get_screen_data(C.IP_INTERNIC)
        html = data["html"]
        assert "interactWithIP" in html or "No outbound links identified" in html, \
            f"Links HTML should show links or empty message. Got: {html[:200]}"


# ======================================================================
# News Screen HTML
# ======================================================================
class TestNewsHTML:
    def test_html_shows_news_or_placeholder(self, rc, world):
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_NEWSSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        html = data["html"]
        # Should show articles or "No news" message
        assert "No news" in html or "NEWS" in html, \
            f"News HTML should show news or placeholder. Got: {html[:200]}"


# ======================================================================
# Rankings Screen HTML
# ======================================================================
class TestRankingsHTML:
    def test_html_shows_rankings_or_placeholder(self, rc, world):
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_RANKINGSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        html = data["html"]
        # Should show rankings or "No rankings" message
        assert "No rankings" in html or "RANKING" in html.upper() or "Rating" in html, \
            f"Rankings HTML should show rankings or placeholder. Got: {html[:200]}"


# ======================================================================
# Console Screen HTML
# ======================================================================
class TestConsoleHTML:
    def test_html_shows_console_prompt(self, rc, world):
        for comp in world.computers.values():
            if any(s.screen_type == C.SCREEN_CONSOLESCREEN for s in comp.screens):
                rc.connect(comp.ip)
                rc.navigate_screen(comp.ip, C.SCREEN_CONSOLESCREEN)
                data = rc.get_screen_data(comp.ip)
                html = data["html"]
                assert len(html) > 0, "Console HTML should not be empty"
                break


# ======================================================================
# Password Screen HTML
# ======================================================================
class TestPasswordHTML:
    def test_html_shows_password_prompt(self, rc, world):
        for comp in world.computers.values():
            if any(s.screen_type == C.SCREEN_PASSWORDSCREEN for s in comp.screens):
                rc.connect(comp.ip)
                rc.navigate_screen(comp.ip, C.SCREEN_PASSWORDSCREEN)
                data = rc.get_screen_data(comp.ip)
                html = data["html"]
                assert "PASSWORD" in html.upper() or "password" in html.lower(), \
                    f"Password HTML should show password prompt. Got: {html[:200]}"
                break


# ======================================================================
# Backward Compatibility: Data Keys Still Available
# ======================================================================
class TestDataKeysStillAvailable:
    """Ensure old data keys still exist for any code that depends on them."""

    def test_bbs_screen_also_has_missions_array(self, rc, world):
        for comp in world.computers.values():
            if any(s.screen_type == C.SCREEN_BBSSCREEN for s in comp.screens):
                rc.connect(comp.ip)
                rc.navigate_screen(comp.ip, C.SCREEN_BBSSCREEN)
                data = rc.get_screen_data(comp.ip)
                assert "missions" in data, "BBS screen should still expose missions array for backward compat"
                break

    def test_software_screen_also_has_items_array(self, rc, world):
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_SWSALESSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        assert "items" in data, "Software screen should still expose items array for backward compat"

    def test_hardware_screen_also_has_catalog_arrays(self, rc, world):
        rc.connect(C.IP_UPLINKINTERNALSERVICES)
        rc.navigate_screen(C.IP_UPLINKINTERNALSERVICES, C.SCREEN_HWSALESSCREEN)
        data = rc.get_screen_data(C.IP_UPLINKINTERNALSERVICES)
        assert "gateways" in data, "Hardware screen should still expose gateways array"
        assert "cooling" in data, "Hardware screen should still expose cooling array"
        assert "psu" in data, "Hardware screen should still expose psu array"
        assert "addons" in data, "Hardware screen should still expose addons array"
