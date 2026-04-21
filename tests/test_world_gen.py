"""
Onlink-Clone: World Generator Tests

Tests world generation, public server flags, mission generation on boot,
and initial player visibility.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from core.game_state import GameState, NodeType
from core.world_generator import generate_world


@pytest.fixture
def world():
    s = GameState()
    generate_world(s)
    return s


class TestWorldGeneration:
    def test_creates_computers(self, world):
        assert len(world.computers) >= 29

    def test_creates_companies(self, world):
        assert len(world.world.companies) > 10

    def test_creates_people(self, world):
        assert len(world.world.people) >= 25

class TestRecordKeeping:
    def test_academic_database_has_records(self, world):
        from core import constants as C
        acad = world.computers.get(C.IP_ACADEMICDATABASE)
        assert acad is not None
        assert len(acad.recordbank) > 0
        assert acad.recordbank[0].name != ""

    def test_criminal_database_has_records(self, world):
        from core import constants as C
        crim = world.computers.get(C.IP_GLOBALCRIMINALDATABASE)
        assert crim is not None
        assert len(crim.recordbank) > 0

    def test_social_security_database_has_records(self, world):
        from core import constants as C
        soc = world.computers.get(C.IP_SOCIALSECURITYDATABASE)
        assert soc is not None
        assert len(soc.recordbank) > 0

    def test_creates_localhost(self, world):
        assert "127.0.0.1" in world.computers
        assert world.computers["127.0.0.1"].computer_type == NodeType.GATEWAY

    def test_creates_internic(self, world):
        internic_ips = [
            ip
            for ip, c in world.computers.items()
            if c.computer_type == NodeType.INTERNIC
        ]
        assert len(internic_ips) >= 1

    def test_creates_public_servers(self, world):
        public = [
            c
            for c in world.computers.values()
            if c.computer_type == NodeType.PUBLIC_SERVER
        ]
        assert len(public) >= 1

    def test_creates_internal_servers(self, world):
        internal = [
            c
            for c in world.computers.values()
            if c.computer_type == NodeType.INTERNAL_SRV
        ]
        assert len(internal) >= 10

    def test_generates_missions(self, world):
        assert len(world.missions) >= 1

    def test_localhost_known(self, world):
        assert "127.0.0.1" in world.player.known_ips

    def test_starting_nodes_known(self, world):
        assert len(world.player.known_ips) >= 6

    def test_bounce_chain_initialized(self, world):
        assert "127.0.0.1" in world.bounce.hops


class TestPublicServerAuth:
    def test_public_server_no_accounts(self, world):
        public = [
            c
            for c in world.computers.values()
            if c.computer_type == NodeType.PUBLIC_SERVER
        ]
        for server in public:
            assert len(server.accounts) == 0, (
                f"Public server {server.ip} has accounts: {server.accounts}"
            )

    def test_internal_server_has_accounts(self, world):
        internal = [
            c
            for c in world.computers.values()
            if c.computer_type == NodeType.INTERNAL_SRV
        ]
        for server in internal:
            assert len(server.accounts) > 0, (
                f"Internal server {server.ip} has no accounts"
            )

    def test_government_server_has_accounts(self, world):
        gov = [
            c
            for c in world.computers.values()
            if c.computer_type == NodeType.GOVERNMENT
        ]
        for server in gov:
            assert len(server.accounts) > 0, (
                f"Government server {server.ip} has no accounts"
            )


class TestServerStructure:
    def test_servers_have_screens(self, world):
        for ip, comp in world.computers.items():
            if comp.computer_type != NodeType.GATEWAY:
                assert len(comp.screens) > 0, f"Server {ip} has no screens"

    def test_public_servers_no_password_screen(self, world):
        from core import constants as C

        public = [
            c
            for c in world.computers.values()
            if c.computer_type == NodeType.PUBLIC_SERVER
        ]
        for server in public:
            pw_screens = [
                s for s in server.screens if s.screen_type == C.SCREEN_PASSWORDSCREEN
            ]
            assert len(pw_screens) == 0, (
                f"Public server {server.ip} has password screen"
            )

    def test_internal_servers_have_password_screen(self, world):
        from core import constants as C

        internal = [
            c
            for c in world.computers.values()
            if c.computer_type == NodeType.INTERNAL_SRV
        ]
        for server in internal:
            pw_screens = [
                s for s in server.screens if s.screen_type == C.SCREEN_PASSWORDSCREEN
            ]
            assert len(pw_screens) > 0, (
                f"Internal server {server.ip} has no password screen"
            )

    def test_servers_have_console_screen(self, world):
        from core import constants as C

        for ip, comp in world.computers.items():
            if comp.computer_type != NodeType.GATEWAY:
                console_screens = [
                    s for s in comp.screens if s.screen_type == C.SCREEN_CONSOLESCREEN
                ]
                assert len(console_screens) > 0, f"Server {ip} has no console screen"


class TestProceduralContent:
    def test_internal_servers_linked_from_public(self, world):
        public = [
            c
            for c in world.computers.values()
            if c.computer_type == NodeType.PUBLIC_SERVER
        ]
        linked_internal = []
        for pub in public:
            for link_ip in pub.links:
                comp = world.computers.get(link_ip)
                if comp and comp.computer_type == NodeType.INTERNAL_SRV:
                    linked_internal.append(link_ip)
        assert len(linked_internal) > 0

    def test_internal_servers_have_files(self, world):
        internal = [
            c
            for c in world.computers.values()
            if c.computer_type == NodeType.INTERNAL_SRV
        ]
        with_files = [c for c in internal if len(c.files) > 0]
        assert len(with_files) > 0

    def test_academic_database_has_file(self, world):
        acad = [c for c in world.computers.values() if "Academic" in c.name]
        assert len(acad) > 0
        assert len(acad[0].files) > 0


def test_ip_constants_are_valid():
    """All hardcoded IP constants must have valid octets (0-255)."""
    from core import constants as C
    import ipaddress
    for name, value in vars(C).items():
        if name.startswith("IP_") and isinstance(value, str):
            ipaddress.IPv4Address(value)
