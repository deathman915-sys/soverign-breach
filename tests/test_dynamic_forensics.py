
from core.game_state import Computer
from core.engine import GameEngine
from core.connection_manager import connect
from core.npc_engine import process_npc_investigations

def test_forensics_traces_dynamic_player_ip():
    engine = GameEngine()
    state = engine.state
    
    # 1. Setup Player with a specific session IP
    session_ip = "185.22.33.44"
    state.player.localhost_ip = session_ip
    
    # 2. Setup Target Computer
    target_ip = "1.1.1.1"
    state.computers[target_ip] = Computer(ip=target_ip, name="Bank", computer_type=3) # 3=BANK
    
    # 3. Create a high-suspicion log (Action: Hack)
    # connect() creates a connection log
    connect(state, target_ip)
    # Escalate its suspicion manually for testing
    target = state.computers[target_ip]
    target.internal_logs[0].suspicion_level = 3
    target.logs[0].suspicion_level = 3
    
    # 4. Run NPC investigation
    # Force a scan success
    from core import npc_engine
    # Mock scan_for_crimes to always succeed for test
    def mock_scan(s, c):
        for log_entry in c.internal_logs:
            if log_entry.suspicion_level >= 2:
                npc_engine._start_investigation(s, c.ip, log_entry)
    
    npc_engine._scan_for_crimes = mock_scan
    process_npc_investigations(state, 1.0)
    
    assert len(state.passive_traces) == 1
    trace = state.passive_traces[0]
    assert trace.target_ip == session_ip, f"Trace should target session IP {session_ip}, got {trace.target_ip}"
    
    # 5. Tick passive trace to reach player
    # Connection was direct, so 1 hop
    engine._tick_passive_traces()
    
    # Wait, _tick_passive_traces decrements ticks_until_next_hop
    trace.ticks_until_next_hop = 1

    # Mock events to catch game_over
    events = []
    engine.events.connect("game_over", lambda msg: events.append(msg))

    engine._tick_passive_traces()

    # trigger_arrest now returns a dict with type/reason, check accordingly
    def msg_contains(msg, text):
        if isinstance(msg, dict):
            return text in msg.get("reason", "")
        return text in str(msg)

    assert any(msg_contains(msg, "PASSIVE TRACE REACHED GATEWAY") for msg in events), "Player should be caught at their dynamic IP"
