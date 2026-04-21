"""
Onlink-Clone: Gameplay Integration Tests

End-to-end tests that verify multiple systems working together:
missions, connections, stock market, store, NPCs, news, and events.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from core.game_state import GameState, VFSFile
from core.world_generator import generate_world
from core.mission_engine import (
    generate_missions,
    accept_mission,
    complete_mission,
    MISSION_STEALFILE,
)
from core.connection_manager import connect, disconnect
from core.finance_engine import buy_stock, sell_stock, get_stock_prices
from core.npc_engine import tick_npcs, get_rankings
from core.news_engine import tick_news, get_recent_news
from core.store_engine import buy_software
from core.event_scheduler import process_events, schedule_initial_events


@pytest.fixture
def game_world():
    s = GameState()
    generate_world(s)
    return s


class TestMissionFlow:
    def test_generate_and_accept(self, game_world):
        missions = generate_missions(game_world, 5)
        assert len(missions) >= 1
        result = accept_mission(game_world, missions[0].id)
        assert result["success"] is True

    def test_generate_accept_complete(self, game_world):
        missions = generate_missions(game_world, 5)
        steal = [m for m in missions if m.mission_type == MISSION_STEALFILE]
        if not steal:
            pytest.skip("No steal file mission")
        m = steal[0]
        accept_mission(game_world, m.id)
        game_world.vfs.files.append(VFSFile(filename=m.completion_b, size_gq=1))
        result = complete_mission(game_world, m.id)
        assert result["success"] is True
        assert result["payment"] > 0

    def test_mission_pays_player(self, game_world):
        missions = [
            m
            for m in game_world.missions
            if not m.is_accepted and m.mission_type == MISSION_STEALFILE
        ]
        if not missions:
            pytest.skip("No steal file mission available")
        m = missions[0]
        balance_before = game_world.player.balance
        accept_mission(game_world, m.id)
        game_world.vfs.files.append(VFSFile(filename=m.completion_b, size_gq=1))
        complete_mission(game_world, m.id)
        assert game_world.player.balance > balance_before


class TestConnectionFlow:
    def test_connect_disconnect(self, game_world):
        target_ip = list(game_world.computers.keys())[5]
        result = connect(game_world, target_ip)
        assert result["success"] is True
        result = disconnect(game_world)
        assert result["success"] is True

    def test_connect_unknown(self, game_world):
        result = connect(game_world, "99.99.99.99")
        assert result["success"] is False


class TestStockMarket:
    def test_get_prices(self, game_world):
        prices = get_stock_prices(game_world)
        assert len(prices) > 0

    def test_buy_and_sell(self, game_world):
        game_world.player.balance = 100000
        prices = get_stock_prices(game_world)
        company = prices[0]["company"]
        buy_result = buy_stock(game_world, company, 10)
        assert buy_result["success"] is True
        sell_result = sell_stock(game_world, company, 10)
        assert sell_result["success"] is True


class TestStore:
    def test_buy_software(self, game_world):
        old_balance = game_world.player.balance
        result = buy_software(game_world, "Decrypter", 1)
        assert result["success"] is True
        assert game_world.player.balance < old_balance


class TestNPCs:
    def test_npc_tick(self, game_world):
        game_world.clock.tick_count = 200
        events = tick_npcs(game_world, 200)
        assert isinstance(events, list)

    def test_rankings(self, game_world):
        rankings = get_rankings(game_world)
        assert len(rankings) > 1


class TestNews:
    def test_news_tick(self, game_world):
        game_world.clock.tick_count = 500
        events = tick_news(game_world, 500)
        assert isinstance(events, list)

    def test_recent_news(self, game_world):
        news = get_recent_news(game_world)
        assert isinstance(news, list)


class TestEvents:
    def test_schedule_and_process(self, game_world):
        schedule_initial_events(game_world, 0)
        game_world.clock.tick_count = 6000
        msgs = process_events(game_world, game_world.clock.tick_count)
        assert len(msgs) > 0
