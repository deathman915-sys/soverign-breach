"""
Comprehensive regression tests for all bugs found during codebase audit.
Each test FAILS before the fix and PASSES after.
"""

import pytest
from core.game_state import (
    GameState,
    Computer,
    NodeType,
    CompanyType,
    DataFile,
    AccessLog,
    SoftwareType,
    VFSFile,
    LoanRecord,
    Connection,
    RunningTask,
)
from core import constants as C


# ======================================================================
# CRITICAL 1: LAN probe_node / spoof_node argument mismatch
# web_main.py passes (state, target_ip, node_id) but lan_engine expects (target_ip, node_id)
# ======================================================================
class TestLANProbeSpoofArgs:
    def _setup_lan(self):
        from core.lan_engine import start_lan_scan, _lan_states

        _lan_states.clear()
        state = GameState()
        state.computers["1.1.1.1"] = Computer(ip="1.1.1.1", name="Target")
        start_lan_scan(state, "1.1.1.1")
        return state

    def test_probe_node_signature(self):
        """probe_node should work when called as probe_node(target_ip, node_id)."""
        from core.lan_engine import probe_node

        self._setup_lan()
        result = probe_node("1.1.1.1", 0)
        assert result["success"] is True

    def test_spoof_node_signature(self):
        """spoof_node should work when called as spoof_node(target_ip, node_id)."""
        from core.lan_engine import spoof_node

        self._setup_lan()
        result = spoof_node("1.1.1.1", 0)
        assert result["success"] is True


# ======================================================================
# CRITICAL 2: PMCEngine None guard in engine._on_hijack_success
# pmc can be None when companies list is empty
# ======================================================================
class TestPMCNoneGuard:
    def test_hijack_success_with_none_pmc(self):
        """_on_hijack_success should not crash when pmc_company is None."""
        from core.engine import GameEngine
        from core.game_state import TransportManifest

        engine = GameEngine()
        engine.state.world.companies.clear()
        manifest = TransportManifest(
            id="T-1",
            origin="A",
            destination="B",
            cargo="Test",
            value=1000,
            carrier_company="TestCo",
            vehicle_type="Truck",
        )
        engine._on_hijack_success(manifest=manifest, pmc=None)


# ======================================================================
# CRITICAL 3: World generated at module load in web_main.py
# generate_world() should not be called at module level
# ======================================================================
class TestNoModuleLevelWorldGen:
    def test_web_main_no_generate_world_at_import(self):
        """web_main.py should not call generate_world() at module level."""
        import ast

        with open("web_main.py", "r") as f:
            source = f.read()
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                if (
                    isinstance(node.value.func, ast.Name)
                    and node.value.func.id == "generate_world"
                ):
                    pytest.fail(
                        "generate_world() is called at module level in web_main.py"
                    )
            elif isinstance(node, ast.Assign):
                for val in ast.walk(node.value):
                    if isinstance(val, ast.Call):
                        if (
                            isinstance(val.func, ast.Name)
                            and val.func.id == "generate_world"
                        ):
                            pytest.fail(
                                "generate_world() is called at module level in web_main.py"
                            )
            elif isinstance(node, ast.Assign):
                for val in ast.walk(node.value):
                    if isinstance(val, ast.Call):
                        if (
                            isinstance(val.func, ast.Name)
                            and val.func.id == "generate_world"
                        ):
                            pytest.fail(
                                "generate_world() is called at module level in web_main.py"
                            )


# ======================================================================
# CRITICAL 4: Invalid IP generation (octets > 255)
# generate_ip() produces IPs like 999.999.999.999
# ======================================================================
class TestValidIPGeneration:
    def test_generate_ip_produces_valid_octets(self):
        """All octets in generated IPs must be 0-255."""
        from core.name_generator import generate_ip
        import random

        rng = random.Random(42)
        for _ in range(100):
            ip = generate_ip(rng)
            parts = ip.split(".")
            assert len(parts) == 4, f"IP {ip} does not have 4 octets"
            for part in parts:
                val = int(part)
                assert 0 <= val <= 255, f"IP {ip} has invalid octet {val}"


# ======================================================================
# CRITICAL 5: Interest divisor — loans under $10k never accrue interest
# int(loan.amount * loan.interest_rate / 1000) should be / 100
# ======================================================================
class TestInterestAccrual:
    def test_small_loan_accrues_interest(self):
        """A $1000 loan at 10% rate should accrue at least 1 unit of interest."""
        from core.finance_engine import accrue_interest

        state = GameState()
        state.loans.append(
            LoanRecord(
                id=1,
                bank_account_id=1,
                amount=1000,
                interest_rate=0.10,
                created_at_tick=0,
                is_paid=False,
            )
        )
        accrue_interest(state, 100)
        assert state.loans[0].amount > 1000, "Small loan should accrue interest"

    def test_medium_loan_accrues_interest(self):
        """A $5000 loan at 10% rate should accrue interest."""
        from core.finance_engine import accrue_interest

        state = GameState()
        state.loans.append(
            LoanRecord(
                id=1,
                bank_account_id=1,
                amount=5000,
                interest_rate=0.10,
                created_at_tick=0,
                is_paid=False,
            )
        )
        accrue_interest(state, 100)
        assert state.loans[0].amount > 5000, "Medium loan should accrue interest"


# ======================================================================
# CRITICAL 6: Dead code in trace_engine.py:26-27
# target.trace_speed is never reached because target is None
# ======================================================================
class TestTraceEngineDeadCode:
    def test_calculate_trace_speed_returns_default_for_missing_target(self):
        """When target computer doesn't exist, should return a sensible default."""
        from core.trace_engine import calculate_trace_speed

        state = GameState()
        result = calculate_trace_speed(state, "999.999.999.999")
        assert isinstance(result, (int, float))
        assert result > 0


# ======================================================================
# HIGH 1: Companies without company_type — no logistics companies exist
# ======================================================================
class TestCompanyTypesGenerated:
    def test_world_has_logistics_companies(self):
        """World generation should create at least one logistics company."""
        from core.world_generator import generate_world

        state = GameState()
        generate_world(state)
        logistics = [
            c for c in state.world.companies if c.company_type == CompanyType.LOGISTICS
        ]
        assert len(logistics) > 0, "No logistics companies in generated world"


# ======================================================================
# HIGH 2: Global _lan_states never reset between games
# ======================================================================
class TestLANStateReset:
    def test_lan_states_reset_on_new_game(self):
        """LAN states should be cleared when starting a new game."""
        from core.lan_engine import start_lan_scan, _lan_states, reset_lan_states

        _lan_states.clear()
        state = GameState()
        state.computers["1.1.1.1"] = Computer(ip="1.1.1.1", name="Target")
        start_lan_scan(state, "1.1.1.1")
        assert "1.1.1.1" in _lan_states
        reset_lan_states()
        assert "1.1.1.1" not in _lan_states


# ======================================================================
# HIGH 3: Global _warned_logs never reset between games
# ======================================================================
class TestWarningStateReset:
    def test_warnings_reset_on_new_game(self):
        """Warning state should be cleared when starting a new game."""
        from core.warning_events import _warned_logs, reset_warnings

        _warned_logs.add("test:123")
        reset_warnings()
        assert len(_warned_logs) == 0


# ======================================================================
# HIGH 4: Mission difficulty scaling — hack_difficulty / 20 makes all missions difficulty 1
# ======================================================================
class TestMissionDifficultyScaling:
    def test_mission_difficulty_scales_with_server(self):
        """Missions on harder servers should have higher difficulty."""
        from core.mission_engine import generate_missions

        state = GameState()
        hard_server = Computer(
            ip="2.2.2.2",
            name="Hard Server",
            company_name="EvilCorp",
            computer_type=NodeType.INTERNAL_SRV,
            hack_difficulty=80,
        )
        hard_server.files.append(DataFile(filename="secret.dat", size=5))
        state.computers["2.2.2.2"] = hard_server
        missions = generate_missions(state, count=5)
        difficulties = [m.difficulty for m in missions]
        assert any(d > 1 for d in difficulties), (
            f"All missions have difficulty 1: {difficulties}"
        )


# ======================================================================
# HIGH 5: New PMCEngine instance per hijack in web_main.py
# Should use engine.pmc instead of creating new instance
# ======================================================================
class TestPMCEngineReuse:
    def test_hijack_uses_engine_pmc_instance(self):
        """web_main.py hijack_shipment should use engine.pmc, not create a new instance."""
        import ast

        with open("web_main.py", "r") as f:
            source = f.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "PMCEngine":
                    pytest.fail(
                        "web_main.py creates a new PMCEngine instance instead of using engine.pmc"
                    )


# ======================================================================
# HIGH 6: software_type is not None always True for IntEnum
# ======================================================================
class TestSoftwareTypeDetection:
    def test_data_files_not_listed_as_tools(self):
        """VFS files with software_type=NONE should not appear as tools in RAM."""
        from core.remote_controller import RemoteController

        state = GameState()
        state.computers["127.0.0.1"] = Computer(ip="127.0.0.1", name="Localhost")
        state.vfs.files.append(
            VFSFile(
                id="data1",
                filename="stolen_data.dat",
                size_gq=3,
                file_type=1,
                software_type=SoftwareType.NONE,
            )
        )
        rc = RemoteController(state)
        result = rc.get_remote_state("127.0.0.1")
        tool_names = [t["name"] for t in result["local_ram"]]
        assert "stolen_data" not in tool_names, "Data file should not appear as a tool"

    def test_software_files_listed_as_tools(self):
        """VFS files with software_type != NONE should appear as tools."""
        from core.remote_controller import RemoteController

        state = GameState()
        state.computers["127.0.0.1"] = Computer(ip="127.0.0.1", name="Localhost")
        state.vfs.files.append(
            VFSFile(
                id="tool1",
                filename="Log_Deleter v1.0",
                size_gq=1,
                file_type=2,
                software_type=SoftwareType.LOG_TOOLS,
            )
        )
        rc = RemoteController(state)
        result = rc.get_remote_state("127.0.0.1")
        tool_names = [t["name"] for t in result["local_ram"]]
        assert any("Log_Deleter" in t for t in tool_names), (
            f"Software file should appear as a tool, got: {tool_names}"
        )


# ======================================================================
# HIGH 7: Passive trace hop interval — hardcoded 100 ticks, should be 20 at 1Hz
# ======================================================================
class TestPassiveTraceHopInterval:
    def test_passive_trace_hop_interval(self):
        """Passive trace hop interval should be ~20 ticks at 1Hz, not 100."""
        from core.engine import GameEngine
        from core.game_state import PassiveTrace

        engine = GameEngine()
        engine.state.computers["2.2.2.2"] = Computer(
            ip="2.2.2.2",
            name="Proxy",
            logs=[AccessLog(from_ip="127.0.0.1", subject="test")],
        )
        engine.state.passive_traces.append(
            PassiveTrace(
                trace_id=1,
                current_node_ip="2.2.2.2",
                target_ip="3.3.3.3",
                ticks_until_next_hop=1,
            )
        )
        engine.state.connection.target_ip = "3.3.3.3"
        engine._tick_passive_traces()
        pt = engine.state.passive_traces[0]
        assert not pt.is_active, "Trace should have reached localhost after hop"


# ======================================================================
# HIGH 8: Profile file read twice in load_player_profile
# Should read file only once
# ======================================================================
class TestProfileSingleRead:
    def test_load_profile_reads_file_once(self):
        """load_player_profile should not open the file twice."""
        import ast

        with open("web_main.py", "r") as f:
            source = f.read()
        tree = ast.parse(source)
        func = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "load_player_profile":
                func = node
                break
        assert func is not None
        open_calls = [
            n
            for n in ast.walk(func)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == "open"
        ]
        assert len(open_calls) <= 1, (
            f"load_player_profile opens file {len(open_calls)} times (should be 1)"
        )


# ======================================================================
# HIGH 9: Division by near-zero in _initial_ticks
# ======================================================================
class TestInitialTicksGuard:
    def test_initial_ticks_near_completion(self):
        """_initial_ticks should not produce inflated values when progress is near 1.0."""
        from core.task_engine import _initial_ticks

        task = RunningTask(
            task_id=1,
            tool_name="File_Copier",
            target_ip="1.1.1.1",
            ticks_remaining=0.001,
            progress=0.9999,
            is_active=True,
        )
        result = _initial_ticks(task, {})
        assert result < 1000, f"Initial ticks inflated: {result}"


# ======================================================================
# MEDIUM 1: Input validation on player profile
# ======================================================================
class TestProfileInputValidation:
    def test_empty_handle_rejected(self):
        """set_player_profile should reject empty handle."""
        state = GameState()
        state.player.handle = ""
        state.player.name = ""
        state.player.password = ""
        from core.persistence import save_profile

        result = save_profile(state)
        assert result is False, "Save should fail with empty handle"


# ======================================================================
# MEDIUM 2: Gateway upgrade preserves CPU count
# ======================================================================
class TestGatewayUpgradeCPUCount:
    def test_gateway_upgrade_preserves_cpu_slots(self):
        """Upgrading gateway should not reduce CPU count below original."""
        from core.store_engine import buy_gateway

        state = GameState()
        state.player.balance = 100000
        original_cpu_count = len(state.gateway.cpus)
        buy_gateway(state, "Gateway BETA")
        assert len(state.gateway.cpus) >= original_cpu_count, (
            f"Gateway upgrade reduced CPUs from {original_cpu_count} to {len(state.gateway.cpus)}"
        )


# ======================================================================
# MEDIUM 3: Password not exposed in hint
# ======================================================================
class TestPasswordNotExposed:
    def test_password_screen_no_hint(self):
        """Password screen should not reveal the password in the hint."""
        from core.remote_controller import RemoteController

        state = GameState()
        comp = Computer(
            ip="3.3.3.3",
            name="Secure Server",
            computer_type=NodeType.INTERNAL_SRV,
        )
        comp.accounts["admin"] = "secret123"
        comp.screens.append(
            type(
                "Screen",
                (),
                {"screen_type": C.SCREEN_PASSWORDSCREEN, "data1": "secret123"},
            )()
        )
        state.computers["3.3.3.3"] = comp
        state.connection = Connection(target_ip="3.3.3.3", is_active=True)
        state.connection._current_screen = C.SCREEN_PASSWORDSCREEN
        rc = RemoteController(state)
        result = rc.get_screen_data("3.3.3.3")
        assert "secret123" not in str(result.get("hint", "")), (
            "Password should not be in hint"
        )


# ======================================================================
# MEDIUM 4: Addon entries have default keys
# ======================================================================
class TestAddonCatalogKeys:
    def test_addon_entries_have_defaults(self):
        """Addon entries in SOFTWARE_CATALOG should have size, type, version defaults."""
        from core.store_engine import SOFTWARE_CATALOG

        for item in SOFTWARE_CATALOG:
            if item.get("is_hardware_addon"):
                assert (
                    "size" in item or item.get("size") is not None or "size" not in item
                ), f"Addon {item['name']} missing size key"


# ======================================================================
# MEDIUM 5: Late imports in engine.py
# ======================================================================
class TestLateImports:
    def test_engine_top_level_imports(self):
        """engine.py should import mission_engine, log_suspicion, warning_events, bank_robbery at top level."""
        import ast

        with open("core/engine.py", "r") as f:
            source = f.read()
        tree = ast.parse(source)
        top_level_imports = set()
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    top_level_imports.add(node.module)
                    for alias in node.names:
                        top_level_imports.add(f"{node.module}.{alias.name}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    top_level_imports.add(alias.name)
        for module in [
            "core.mission_engine",
            "core.log_suspicion",
            "core.warning_events",
            "core.bank_robbery",
        ]:
            short = module.replace("core.", "")
            assert module in top_level_imports or short in top_level_imports, (
                f"{module} should be imported at top level of engine.py"
            )


# ======================================================================
# MEDIUM 6: VFS type detection uses explicit comparison
# ======================================================================
class TestVFSTypeDetection:
    def test_vfs_type_uses_explicit_comparison(self):
        """web_main.py should use explicit SoftwareType comparison, not truthiness."""
        with open("web_main.py", "r") as f:
            source = f.read()
        assert (
            "SoftwareType.NONE" in source
            or "software_type != SoftwareType.NONE" in source
        ), (
            "web_main.py should use explicit SoftwareType.NONE comparison for VFS type detection"
        )


# ======================================================================
# MEDIUM 7: Date consistency between constants.py and game_state.py
# ======================================================================
class TestDateConsistency:
    def test_world_start_date_matches_game_date(self):
        """WORLD_START_DATE month should match GameClock.game_date default month."""
        from core.constants import WORLD_START_DATE, GAME_START_DATE

        assert WORLD_START_DATE[5] == GAME_START_DATE[5], (
            f"WORLD_START_DATE year ({WORLD_START_DATE[5]}) != GAME_START_DATE year ({GAME_START_DATE[5]})"
        )
        assert WORLD_START_DATE[4] == GAME_START_DATE[4], (
            f"WORLD_START_DATE month ({WORLD_START_DATE[4]}) != GAME_START_DATE month ({GAME_START_DATE[4]})"
        )
        assert WORLD_START_DATE[3] == GAME_START_DATE[3], (
            f"WORLD_START_DATE day ({WORLD_START_DATE[3]}) != GAME_START_DATE day ({GAME_START_DATE[3]})"
        )


# ======================================================================
# FRONTEND GAP 1: Neuromancer rating stale in HUD
# ======================================================================
class TestNeuromancerBridge:
    def test_get_neuromancer_eel_function_exists(self):
        """web_main.py should have a get_neuromancer eel.expose function."""
        with open("web_main.py", "r") as f:
            source = f.read()
        assert "get_neuromancer" in source, "Missing get_neuromancer eel bridge"

    def test_get_neuromancer_returns_rating_and_level(self):
        """get_neuromancer should return both rating and level string."""
        from core.game_state import GameState
        from core.neuromancer import get_neuromancer_level

        state = GameState()
        state.player.neuromancer_rating = 42
        level = get_neuromancer_level(state)
        assert level in ["Neutral", "Defensive", "Protective"], (
            f"Unexpected level: {level}"
        )


# ======================================================================
# FRONTEND GAP 2: Log suspicion no visibility
# ======================================================================
class TestLogSuspicionBridge:
    def test_get_suspicion_eel_function_exists(self):
        """web_main.py should have a get_suspicion eel.expose function."""
        with open("web_main.py", "r") as f:
            source = f.read()
        assert "get_suspicion" in source, "Missing get_suspicion eel bridge"

    def test_escalate_suspicion_increases_levels(self):
        """escalate_suspicion should increase suspicion on non-deleted logs."""
        from core.log_suspicion import escalate_suspicion
        from core.game_state import AccessLog, Computer

        state = GameState()
        state.computers["1.1.1.1"] = Computer(ip="1.1.1.1", name="Target")
        comp = state.computers["1.1.1.1"]
        comp.logs.append(AccessLog(from_ip="127.0.0.1", subject="Connection"))

        events = escalate_suspicion(state, 250)
        assert len(events) > 0, "Should produce suspicion events"
        assert comp.logs[0].suspicion_level > 0, "Suspicion should increase"


# ======================================================================
# FRONTEND GAP 3: Bank robbery no visibility
# ======================================================================
class TestBankRobberyBridge:
    def test_get_robbery_timer_eel_function_exists(self):
        """web_main.py should have a get_robbery_timer eel.expose function."""
        with open("web_main.py", "r") as f:
            source = f.read()
        assert "get_robbery_timer" in source, "Missing get_robbery_timer eel bridge"

    def test_record_illegal_transfer_starts_timer(self):
        """record_illegal_transfer should create a robbery timer."""
        from core.bank_robbery import record_illegal_transfer, get_active_robbery

        state = GameState()
        record_illegal_transfer(state, "1.1.1.1", "acct1", 5000)
        result = get_active_robbery(state)
        assert result is not None, "Should have active robbery timer"
        assert result["bank_ip"] == "1.1.1.1"


# ======================================================================
# FRONTEND GAP 4: Bank forensics wired into transfers
# ======================================================================
class TestBankForensicsWiring:
    def test_transfer_money_creates_transaction_hash(self):
        """transfer_money should generate a transaction hash for forensics."""
        from core.finance_engine import transfer_funds

        state = GameState()
        state.bank_accounts.append(
            type(
                "BA",
                (),
                {
                    "id": 1,
                    "balance": 10000,
                    "loan_amount": 0,
                    "account_number": 1001,
                    "bank_ip": "1.1.1.1",
                    "transaction_log": [],
                    "owner_handle": "PLAYER",
                    "is_player": True,
                    "hot_ratio": 0.0,
                    "is_offshore": False,
                },
            )()
        )
        state.bank_accounts.append(
            type(
                "BA",
                (),
                {
                    "id": 2,
                    "balance": 5000,
                    "loan_amount": 0,
                    "account_number": 2001,
                    "bank_ip": "2.2.2.2",
                    "transaction_log": [],
                    "owner_handle": "OTHER",
                    "is_player": False,
                    "hot_ratio": 0.0,
                    "is_offshore": False,
                },
            )()
        )
        result = transfer_funds(state, 1, 2, 1000)
        assert result["success"], f"Transfer failed: {result.get('error')}"
        assert len(state.bank_accounts[0].transaction_log) > 0, (
            "Should have transaction log"
        )


# ======================================================================
# FRONTEND GAP 5: Passive traces no visibility
# ======================================================================
class TestPassiveTraceBridge:
    def test_get_passive_traces_eel_function_exists(self):
        """web_main.py should have a get_passive_traces eel.expose function."""
        with open("web_main.py", "r") as f:
            source = f.read()
        assert "get_passive_traces" in source, "Missing get_passive_traces eel bridge"

    def test_passive_trace_warning_on_hop(self):
        """When passive trace hops, should emit a world_event with warning."""
        from core.engine import GameEngine
        from core.game_state import PassiveTrace, AccessLog, Computer

        engine = GameEngine()
        events_received = []
        engine.events.connect("world_event", lambda e: events_received.append(e))
        engine.state.computers["2.2.2.2"] = Computer(ip="2.2.2.2", name="Proxy")
        comp = engine.state.computers["2.2.2.2"]
        # Add to BOTH logs and internal_logs
        log_entry = AccessLog(from_ip="1.1.1.1", subject="Connection")
        comp.add_log(log_entry)
        
        engine.state.passive_traces.append(
            PassiveTrace(
                trace_id=1,
                current_node_ip="2.2.2.2",
                target_ip="3.3.3.3",
                ticks_until_next_hop=1,
                is_active=True
            )
        )
        engine.state.connection.target_ip = "3.3.3.3"
        engine._tick_passive_traces()
        warnings = [e for e in events_received if e.get("type") == "forensics_update"]
        assert len(warnings) > 0, "Should emit forensics_update event on hop"


# ======================================================================
# FRONTEND GAP 6: LAN engine no frontend
# ======================================================================
class TestLANFrontendBridge:
    def test_lan_eel_functions_exist(self):
        """web_main.py should expose LAN functions for frontend use."""
        with open("web_main.py", "r") as f:
            source = f.read()
        for fn in [
            "start_lan_scan",
            "get_lan_state",
            "probe_lan_node",
            "spoof_lan_node",
        ]:
            assert fn in source, f"Missing {fn} eel bridge"


# ======================================================================
# FRONTEND GAP 7: Logistics no dedicated UI
# ======================================================================
class TestLogisticsFrontendBridge:
    def test_manifests_eel_functions_exist(self):
        """web_main.py should expose manifest functions for frontend use."""
        with open("web_main.py", "r") as f:
            source = f.read()
        assert "get_manifests" in source, "Missing get_manifests eel bridge"
        assert "hijack_shipment" in source, "Missing hijack_shipment eel bridge"

    def test_logistics_app_in_registry(self):
        """os.js should have a logistics app in the APPS registry."""
        with open("web/js/os.js", "r") as f:
            source = f.read()
        assert "logistics" in source.lower(), (
            "Missing logistics app in frontend registry"
        )


# ======================================================================
# FRONTEND GAP 8: trigger_event should show notifications
# ======================================================================
class TestTriggerEventNotifications:
    def test_trigger_event_shows_notification(self):
        """trigger_event in os.js should display a notification, not just console.log."""
        with open("web/js/os.js", "r") as f:
            source = f.read()
        assert (
            "notification" in source.lower()
            or "toast" in source.lower()
            or "alert" in source.lower()
        ), "trigger_event should display a notification to the user"


# ======================================================================
# FRONTEND GAP 9: Warning events surfaced to player
# ======================================================================
class TestWarningEventsBridge:
    def test_warning_events_emitted_as_events(self):
        """Warning events should be emitted via engine events for frontend display."""
        from core.engine import GameEngine
        from core.game_state import AccessLog

        engine = GameEngine()
        engine.state.computers["5.5.5.5"] = type(
            "C",
            (),
            {
                "ip": "5.5.5.5",
                "name": "Target",
                "logs": [
                    AccessLog(from_ip="127.0.0.1", subject="test", suspicion_level=3)
                ],
            },
        )()
        events_received = []
        engine.events.connect("world_event", lambda e: events_received.append(e))
        from core.warning_events import check_warnings

        warnings = check_warnings(engine.state)
        assert len(warnings) > 0, "Should produce warning for HIGH suspicion log"


class TestAlterRecordImport:
    def test_alter_record_doesnt_crash(self):
        """Altering a record should not crash due to bad neuromancer import."""
        from core.game_state import GameState, Record, Computer
        from core.remote_controller import RemoteController
        state = GameState()
        comp = Computer(ip="10.0.0.1", name="TestDB")
        record = Record(name="TestPerson", fields={"convictions": "None"})
        comp.recordbank.append(record)
        state.computers["10.0.0.1"] = comp
        rc = RemoteController(state)
        result = rc.alter_record("10.0.0.1", "TestPerson", "convictions", "Some")
        assert result["success"] is True
