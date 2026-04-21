
from core.game_state import GameState, Computer, AccessLog
from core.task_engine import start_task, tick_task
from core.connection_manager import connect

def test_internal_logs_created_on_connection():
    state = GameState()
    state.computers["1.1.1.1"] = Computer(ip="1.1.1.1", name="Target")
    
    # Connect should create logs
    connect(state, "1.1.1.1")
    
    target = state.computers["1.1.1.1"]
    assert len(target.logs) > 0, "Public logs should be created"
    assert hasattr(target, "internal_logs"), "Computer should have internal_logs attribute"
    assert len(target.internal_logs) == len(target.logs), "Internal logs should mirror public logs on creation"
    assert target.internal_logs[0].subject == target.logs[0].subject

def test_log_deleter_does_not_affect_internal_logs():
    state = GameState()
    target = Computer(ip="1.1.1.1", name="Target")
    target.logs = [AccessLog(subject="Connection", from_ip="127.0.0.1")]
    # Manual setup of internal logs for this test
    target.internal_logs = [AccessLog(subject="Connection", from_ip="127.0.0.1")]
    state.computers["1.1.1.1"] = target
    
    # Start Log_Deleter v3 (Standard Delete All)
    start_task(state, "Log_Deleter", 3, "1.1.1.1", {"log_index": 0})
    task = state.tasks[0]
    task.ticks_remaining = 1.0
    
    # Tick to completion
    tick_task(state, task, 1.0)
    
    assert all(log_entry.is_deleted for log_entry in target.logs), "Public logs should be deleted"
    assert all(not log_entry.is_deleted for log_entry in target.internal_logs), "Internal logs should REMAIN untouched by v3"
    assert len(target.internal_logs) == 1, "Internal log count should be preserved"

def test_log_deleter_v4_purges_internal_logs():
    state = GameState()
    target = Computer(ip="1.1.1.1", name="Target")
    target.add_log(AccessLog(subject="Connection", from_ip="127.0.0.1"))
    state.computers["1.1.1.1"] = target
    
    # Start Log_Deleter v4 (Purge)
    start_task(state, "Log_Deleter", 4, "1.1.1.1", {})
    task = state.tasks[0]
    task.ticks_remaining = 1.0
    
    tick_task(state, task, 1.0)
    
    assert all(log_entry.is_deleted for log_entry in target.logs), "Public logs should be deleted"
    assert all(log_entry.is_deleted for log_entry in target.internal_logs), "Internal logs should be PURGED by v4"
