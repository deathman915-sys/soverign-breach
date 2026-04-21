
from core.game_state import GameState, PersonStatus, VFSFile
from core.engine import GameEngine

def test_trigger_arrest_resets_player_and_gateway():
    engine = GameEngine()
    state = engine.state
    
    # Setup state
    state.player.balance = 10000
    state.player.uplink_rating = 5
    state.vfs.files.append(VFSFile(filename="hacker_tool.exe", size_gq=4))
    state.gateway.heat = 50.0
    
    # Trigger arrest (simulate investigator reaching localhost)
    from core.event_scheduler import trigger_arrest
    trigger_arrest(state, reason="PASSIVE TRACE REACHED GATEWAY")
    
    # Assertions
    assert state.player.status == PersonStatus.ARRESTED
    assert state.player.is_arrested is True
    assert state.player.balance == 5000, "Fine should be 50% of balance"
    assert state.player.uplink_rating == 1, "Rating should reset to 1"
    assert len(state.vfs.files) == 0, "VFS should be wiped"
    assert state.gateway.heat == 25.0, "Gateway should be cooled/reset"
    assert state.clock.speed_multiplier == 0, "Game should pause on arrest"

def test_jail_sentence_tick_progression():
    state = GameState()
    state.player.is_arrested = True
    state.player.status = PersonStatus.ARRESTED
    state.player.jail_sentence_ticks = 100

    # Simulate time passing in jail
    from core.event_scheduler import process_jail_time
    process_jail_time(state, ticks=50)

    assert state.player.jail_sentence_ticks == 50

    process_jail_time(state, ticks=60)
    assert state.player.jail_sentence_ticks == 0
    assert state.player.is_arrested is False
    assert state.player.status == PersonStatus.NONE
