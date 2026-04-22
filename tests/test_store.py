"""
Onlink-Clone: Store Engine Tests

Tests software and hardware purchasing, balance deduction,
and VFS updates.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.game_state import GameState
from core.store_engine import (
    buy_cooling,
    buy_gateway,
    buy_psu,
    buy_software,
    get_cooling_catalog,
    get_hardware_catalog,
    get_psu_catalog,
    get_software_catalog,
)


class TestSoftwareCatalog:
    def test_catalog_not_empty(self):
        catalog = get_software_catalog()
        assert len(catalog) > 0

    def test_catalog_has_required_fields(self):
        catalog = get_software_catalog()
        for item in catalog:
            assert "name" in item
            assert "price" in item
            assert "version" in item


class TestBuySoftware:
    def test_buy_success(self):
        s = GameState()
        s.player.balance = 10000
        result = buy_software(s, "Decrypter", 1)
        assert result["success"] is True
        assert result["cost"] > 0
        assert s.player.balance < 10000

    def test_buy_insufficient_funds(self):
        s = GameState()
        s.player.balance = 1
        result = buy_software(s, "Decrypter", 1)
        assert result["success"] is False

    def test_buy_adds_to_vfs(self):
        s = GameState()
        s.player.balance = 10000
        vfs_before = len(s.vfs.files)
        buy_software(s, "Decrypter", 1)
        assert len(s.vfs.files) == vfs_before + 1

    def test_buy_deducts_balance(self):
        s = GameState()
        s.player.balance = 10000
        result = buy_software(s, "Decrypter", 1)
        assert s.player.balance == 10000 - result["cost"]

    def test_buy_nonexistent_software(self):
        s = GameState()
        s.player.balance = 10000
        result = buy_software(s, "Nonexistent Tool", 1)
        assert result["success"] is False

    def test_buy_same_software_twice(self):
        s = GameState()
        s.player.balance = 20000
        r1 = buy_software(s, "Decrypter", 1)
        r2 = buy_software(s, "Decrypter", 1)
        assert r1["success"] is True
        assert r2["success"] is True
        assert (
            len([f for f in s.vfs.files if "Decrypter" in f.filename]) == 2
        )  # same version = separate copies


class TestBuyGateway:
    def test_catalog_not_empty(self):
        catalog = get_hardware_catalog()
        assert len(catalog) > 0

    def test_buy_success(self):
        s = GameState()
        s.player.balance = 50000
        catalog = get_hardware_catalog()
        gw_name = catalog[0]["name"]
        result = buy_gateway(s, gw_name)
        assert result["success"] is True

    def test_buy_insufficient_funds(self):
        s = GameState()
        s.player.balance = 1
        catalog = get_hardware_catalog()
        gw_name = catalog[-1]["name"]  # Most expensive
        result = buy_gateway(s, gw_name)
        assert result["success"] is False


class TestBuyCooling:
    def test_catalog_not_empty(self):
        catalog = get_cooling_catalog()
        assert len(catalog) > 0

    def test_buy_success(self):
        s = GameState()
        s.player.balance = 10000
        catalog = get_cooling_catalog()
        cooling_name = catalog[0]["name"]
        result = buy_cooling(s, cooling_name)
        assert result["success"] is True


class TestBuyPSU:
    def test_catalog_not_empty(self):
        catalog = get_psu_catalog()
        assert len(catalog) > 0

    def test_buy_success(self):
        s = GameState()
        s.player.balance = 10000
        catalog = get_psu_catalog()
        psu_name = catalog[0]["name"]
        result = buy_psu(s, psu_name)
        assert result["success"] is True
