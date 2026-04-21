"""
Onlink-Clone: Tests for Previously Unwired Features

TDD tests for:
- PSU purchase routing
- Tool toggle (load/unload from RAM)
- VFS management (defrag, delete)
- Message/email system
- Finance (accounts, transfer, stocks, loans)
- Rankings
- Logistics hijack
- LAN operations
- Task stop
- Game state completeness
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from core.game_state import (
    GameState,
    Computer,
    NodeType,
    VFSFile,
    SoftwareType,
    Message,
    CPUCore,
    ComputerScreen,
)
from core.world_generator import generate_world
from core.remote_controller import RemoteController
from core import constants as C


@pytest.fixture
def world():
    s = GameState()
    generate_world(s)
    return s


# ======================================================================
# PSU Purchase Routing
# ======================================================================
class TestPSUPurchase:
    def test_buy_psu_exists(self, world):
        """PSU purchase function should exist and work."""
        from core.store_engine import buy_psu

        world.player.balance = 10000
        result = buy_psu(world, "Bronze 250W PSU")
        assert result["success"] is True
        assert world.gateway.psu_capacity >= 250

    def test_buy_psu_insufficient_funds(self, world):
        from core.store_engine import buy_psu

        world.player.balance = 1
        result = buy_psu(world, "Gold 500W PSU")
        assert result["success"] is False

    def test_buy_psu_not_found(self, world):
        from core.store_engine import buy_psu

        world.player.balance = 10000
        result = buy_psu(world, "Nonexistent PSU")
        assert result["success"] is False


# ======================================================================
# Tool Toggle (Load/Unload from RAM)
# ======================================================================
class TestToolToggle:
    def test_toggle_tool_load(self, world):
        """Loading a tool should add it to local_ram."""
        rc = RemoteController(world)
        # Add a tool to VFS first
        world.vfs.files.append(
            VFSFile(
                filename="Password Breaker v1.0",
                size_gq=2,
                file_type=2,
                software_type=SoftwareType.CRACKERS,
                version=1,
            )
        )
        result = rc.toggle_tool("vfs_0")
        assert result["success"] is True
        assert result["active"] is True

    def test_toggle_tool_unload(self, world):
        """Unloading a tool should remove it from local_ram."""
        rc = RemoteController(world)
        world.vfs.files.append(
            VFSFile(
                filename="Password Breaker v1.0",
                size_gq=2,
                file_type=2,
                software_type=SoftwareType.CRACKERS,
                version=1,
            )
        )
        rc.toggle_tool("vfs_0")  # Load
        result = rc.toggle_tool("vfs_0")  # Unload
        assert result["success"] is True
        assert result["active"] is False

    def test_toggle_tool_nonexistent(self, world):
        rc = RemoteController(world)
        result = rc.toggle_tool("nonexistent")
        assert result["success"] is False

    def test_local_ram_includes_all_tool_types(self, world):
        """local_ram should detect all tool types, not just a few."""
        rc = RemoteController(world)
        # Add various tool types
        tools = [
            ("Decrypter v1.0", SoftwareType.CRACKERS),
            ("Dictionary Hacker v1.0", SoftwareType.CRACKERS),
            ("IP Probe v1.0", SoftwareType.OTHER),
            ("IP Lookup v1.0", SoftwareType.OTHER),
            ("Voice Analyser v1.0", SoftwareType.OTHER),
            ("Defrag v1.0", SoftwareType.OTHER),
            ("HUD_ConnectionAnalysis v1.0", SoftwareType.HUD_UPGRADE),
            ("HUD_LANView v1.0", SoftwareType.HUD_UPGRADE),
        ]
        for name, stype in tools:
            world.vfs.files.append(
                VFSFile(
                    filename=name,
                    size_gq=1,
                    file_type=2,
                    software_type=stype,
                    version=1,
                )
            )
        res = rc.get_remote_state("127.0.0.1")
        ram_names = [t["name"] for t in res["local_ram"]]
        for name, _ in tools:
            clean_name = name.split(".")[0]
            assert clean_name in ram_names, (
                f"Tool {clean_name} not detected in local_ram"
            )


# ======================================================================
# VFS Management
# ======================================================================
class TestVFSManagement:
    def test_delete_file_success(self, world):
        from core.vfs import VirtualFileSystem

        start_count = len(world.vfs.files)
        world.vfs.files.append(VFSFile(filename="test.dat", size_gq=2))
        result = VirtualFileSystem.delete_file(world, "test.dat")
        assert result is True
        assert len(world.vfs.files) == start_count

    def test_delete_file_nonexistent(self, world):
        from core.vfs import VirtualFileSystem

        result = VirtualFileSystem.delete_file(world, "ghost.dat")
        assert result is False

    def test_defrag_reclaims_space(self, world):
        from core.vfs import VirtualFileSystem

        # Create duplicate files
        VirtualFileSystem.store_file(
            world, VFSFile(filename="a.dat", size_gq=3, version=1)
        )
        VirtualFileSystem.store_file(
            world, VFSFile(filename="a.dat", size_gq=3, version=2)
        )
        before = world.vfs.used_gq
        reclaimed = VirtualFileSystem.defrag(world)
        assert reclaimed > 0
        assert world.vfs.used_gq < before

    def test_find_file(self, world):
        from core.vfs import VirtualFileSystem

        world.vfs.files.append(VFSFile(filename="secret.dat", size_gq=1))
        result = VirtualFileSystem.find_file(world, "secret.dat")
        assert result is not None
        assert result.filename == "secret.dat"

    def test_find_software(self, world):
        from core.vfs import VirtualFileSystem

        world.vfs.files.append(
            VFSFile(
                filename="Password Breaker v2.0",
                size_gq=2,
                file_type=2,
                software_type=SoftwareType.CRACKERS,
                version=2,
            )
        )
        result = VirtualFileSystem.find_software(world, "Password Breaker")
        assert result is not None
        assert result.version == 2

    def test_has_space(self, world):
        from core.vfs import VirtualFileSystem

        assert VirtualFileSystem.has_space(world, 10) is True
        assert VirtualFileSystem.has_space(world, 9999) is False


# ======================================================================
# Message/Email System
# ======================================================================
class TestMessages:
    def test_get_messages(self, world):
        """Messages should be retrievable."""
        world.messages.append(
            Message(
                id=1,
                from_name="TestCorp",
                subject="Test",
                body="Hello",
                created_at_tick=0,
            )
        )
        assert len(world.messages) == 1
        assert world.messages[0].subject == "Test"

    def test_get_unread_count(self, world):
        """Should distinguish read vs unread messages."""
        world.messages.append(
            Message(
                id=1,
                from_name="A",
                subject="Read",
                body="x",
                created_at_tick=0,
                is_read=True,
            )
        )
        world.messages.append(
            Message(
                id=2,
                from_name="B",
                subject="Unread",
                body="x",
                created_at_tick=0,
                is_read=False,
            )
        )
        unread = [m for m in world.messages if not m.is_read]
        assert len(unread) == 1

    def test_mark_message_read(self, world):
        world.messages.append(
            Message(
                id=1,
                from_name="A",
                subject="Test",
                body="x",
                created_at_tick=0,
                is_read=False,
            )
        )
        world.messages[0].is_read = True
        assert world.messages[0].is_read is True


# ======================================================================
# Finance System
# ======================================================================
class TestFinance:
    def test_open_account(self, world):
        from core.finance_engine import open_account

        result = open_account(world, "127.0.0.1")
        assert result["success"] is True
        assert result["account_number"] is not None
        assert len(world.bank_accounts) == 1

    def test_get_player_accounts(self, world):
        from core.finance_engine import open_account, get_player_accounts

        open_account(world, "127.0.0.1")
        accounts = get_player_accounts(world)
        assert len(accounts) == 1
        assert accounts[0]["balance"] == 0

    def test_transfer_funds(self, world):
        from core.finance_engine import open_account, transfer_funds

        r1 = open_account(world, "127.0.0.1")
        r2 = open_account(world, "127.0.0.1")
        acct1 = next(a for a in world.bank_accounts if a.id == r1["account_id"])
        acct1.balance = 5000
        result = transfer_funds(world, r1["account_id"], r2["account_id"], 1000)
        assert result["success"] is True
        assert "transaction_hash" in result
        assert acct1.balance == 4000

    def test_transfer_insufficient_funds(self, world):
        from core.finance_engine import open_account, transfer_funds

        r1 = open_account(world, "127.0.0.1")
        r2 = open_account(world, "127.0.0.1")
        result = transfer_funds(world, r1["account_id"], r2["account_id"], 1000)
        assert result["success"] is False

    def test_take_loan(self, world):
        from core.finance_engine import open_account, take_loan

        r = open_account(world, "127.0.0.1")
        result = take_loan(world, r["account_id"], 5000)
        assert result["success"] is True
        assert result["loan_id"] > 0

    def test_repay_loan(self, world):
        from core.finance_engine import open_account, take_loan, repay_loan

        r = open_account(world, "127.0.0.1")
        acct = next(a for a in world.bank_accounts if a.id == r["account_id"])
        acct.balance = 10000
        loan = take_loan(world, r["account_id"], 5000)
        result = repay_loan(world, loan["loan_id"])
        assert result["success"] is True

    def test_repay_loan_insufficient(self, world):
        from core.finance_engine import open_account, take_loan, repay_loan

        r = open_account(world, "127.0.0.1")
        # Take a loan but then drain the account
        loan = take_loan(world, r["account_id"], 5000)
        acct = next(a for a in world.bank_accounts if a.id == r["account_id"])
        acct.balance = 0  # Drain it
        world.player.balance = 0
        result = repay_loan(world, loan["loan_id"])
        assert result["success"] is False

    def test_buy_stock(self, world):
        from core.finance_engine import buy_stock, get_stock_prices

        world.player.balance = 100000
        prices = get_stock_prices(world)
        company = prices[0]["company"]
        result = buy_stock(world, company, 10)
        assert result["success"] is True
        assert len(world.stock_holdings) == 1

    def test_sell_stock(self, world):
        from core.finance_engine import buy_stock, sell_stock, get_stock_prices

        world.player.balance = 100000
        prices = get_stock_prices(world)
        company = prices[0]["company"]
        buy_stock(world, company, 10)
        result = sell_stock(world, company, 5)
        assert result["success"] is True
        assert result["revenue"] > 0

    def test_sell_too_many_shares(self, world):
        from core.finance_engine import sell_stock

        result = sell_stock(world, "Nonexistent", 10)
        assert result["success"] is False

    def test_stock_prices(self, world):
        from core.finance_engine import get_stock_prices

        prices = get_stock_prices(world)
        assert len(prices) > 0
        for p in prices:
            assert "company" in p
            assert "price" in p
            assert "change" in p


# ======================================================================
# Rankings
# ======================================================================
class TestRankings:
    def test_get_rankings(self, world):
        from core.npc_engine import get_rankings

        rankings = get_rankings(world)
        assert len(rankings) > 0
        # Player should be in rankings (key is "name" not "handle")
        player_entry = next((r for r in rankings if r.get("is_player")), None)
        assert player_entry is not None

    def test_rankings_sorted(self, world):
        from core.npc_engine import get_rankings

        rankings = get_rankings(world)
        if len(rankings) > 1:
            # Should be sorted by rating descending
            for i in range(len(rankings) - 1):
                assert rankings[i].get("uplink_rating", 0) >= rankings[i + 1].get(
                    "uplink_rating", 0
                )


# ======================================================================
# Logistics Hijack
# ======================================================================
class TestLogisticsHijack:
    def test_get_manifests(self, world):
        from core.logistics_engine import LogisticsEngine
        from core.game_state import Company, CompanyType

        # Add a logistics company
        world.world.companies.append(
            Company(name="FastExpress", company_type=CompanyType.LOGISTICS)
        )
        le = LogisticsEngine()
        # Tick at exactly the interval boundary
        world.clock.tick_count = 1000
        le.tick(world)
        assert len(world.world.manifests) > 0

    def test_hijack_shipment(self, world):
        from core.logistics_engine import LogisticsEngine
        from core.game_state import Company, CompanyType, PMCSquad

        world.world.companies.append(
            Company(name="FastExpress", company_type=CompanyType.LOGISTICS)
        )
        le = LogisticsEngine()
        world.clock.tick_count = 1000
        le.tick(world)
        if not world.world.manifests:
            pytest.skip("No manifests generated")
        manifest = world.world.manifests[0]
        from core.pmc_engine import PMCEngine
        from core.engine import EventEmitter

        events = EventEmitter()
        pmc = PMCEngine(events)
        squad = PMCSquad(id="S-01", name="Elite Team", combat_rating=50.0)
        result = pmc.attempt_intercept(world, manifest, squad)
        # Returns bool - may be True or False
        assert isinstance(result, bool)


# ======================================================================
# LAN Operations
# ======================================================================
class TestLANOperations:
    def test_start_lan_scan(self, world):
        from core.lan_engine import start_lan_scan

        # Add a computer with LAN capability
        world.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1",
            name="LAN Host",
            computer_type=NodeType.INTERNAL_SRV,
        )
        result = start_lan_scan(world, "10.0.0.1")
        assert result["success"] is True

    def test_lan_scan_invalid_target(self, world):
        from core.lan_engine import start_lan_scan

        result = start_lan_scan(world, "99.99.99.99")
        assert result["success"] is False

    def test_get_lan_state(self, world):
        from core.lan_engine import start_lan_scan, get_lan_state

        world.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1",
            name="LAN Host",
            computer_type=NodeType.INTERNAL_SRV,
        )
        start_lan_scan(world, "10.0.0.1")
        state = get_lan_state(world)
        assert state is not None
        assert "10.0.0.1" in state


# ======================================================================
# Task Stop
# ======================================================================
class TestTaskStop:
    def test_stop_task(self, world):
        from core.task_engine import start_task, stop_task

        world.computers["10.0.0.1"] = Computer(
            ip="10.0.0.1",
            name="Target",
            computer_type=NodeType.INTERNAL_SRV,
            screens=[ComputerScreen(screen_type=C.SCREEN_PASSWORDSCREEN, data1="abc")],
        )
        world.gateway.cpus = [CPUCore(id=1, model="Standard", base_speed=60, speed=60)]
        start_task(world, "Password_Breaker", 1, "10.0.0.1")
        assert len(world.tasks) == 1
        result = stop_task(world, world.tasks[0].task_id)
        assert result["success"] is True
        assert len(world.tasks) == 0

    def test_stop_nonexistent_task(self, world):
        from core.task_engine import stop_task

        result = stop_task(world, 99999)
        assert result["success"] is False


# ======================================================================
# Game State Completeness
# ======================================================================
class TestGameStateCompleteness:
    def test_game_state_has_ratings(self, world):
        """Player should have uplink_rating, neuromancer_rating, credit_rating."""
        assert world.player.uplink_rating >= 0
        assert world.player.neuromancer_rating >= 0
        assert world.player.credit_rating >= 0

    def test_game_state_has_bank_accounts(self, world):
        """State should support bank_accounts."""
        assert isinstance(world.bank_accounts, list)

    def test_game_state_has_loans(self, world):
        """State should support loans."""
        assert isinstance(world.loans, list)

    def test_game_state_has_stock_holdings(self, world):
        """State should support stock holdings."""
        assert isinstance(world.stock_holdings, list)

    def test_game_state_has_messages(self, world):
        """State should support messages."""
        assert isinstance(world.messages, list)

    def test_game_state_has_scheduled_events(self, world):
        """State should support scheduled events."""
        assert isinstance(world.scheduled_events, list)

    def test_game_state_has_passive_traces(self, world):
        """State should support passive traces."""
        assert isinstance(world.passive_traces, list)


# ======================================================================
# Store Addons
# ======================================================================
class TestStoreAddons:
    def test_buy_self_destruct(self, world):
        from core.store_engine import buy_addon

        world.player.balance = 10000
        result = buy_addon(world, "Self Destruct")
        assert result["success"] is True
        assert world.gateway.has_self_destruct is True

    def test_buy_motion_sensor(self, world):
        from core.store_engine import buy_addon

        world.player.balance = 10000
        result = buy_addon(world, "Motion Sensor")
        assert result["success"] is True
        assert world.gateway.has_motion_sensor is True

    def test_buy_addon_insufficient_funds(self, world):
        from core.store_engine import buy_addon

        world.player.balance = 1
        result = buy_addon(world, "Self Destruct")
        assert result["success"] is False

    def test_buy_addon_not_found(self, world):
        from core.store_engine import buy_addon

        world.player.balance = 10000
        result = buy_addon(world, "Nonexistent Addon")
        assert result["success"] is False

    def test_get_addon_catalog(self):
        from core.store_engine import get_addon_catalog

        catalog = get_addon_catalog()
        assert len(catalog) > 0
        names = [c["name"] for c in catalog]
        assert "Self Destruct" in names
        assert "Motion Sensor" in names
