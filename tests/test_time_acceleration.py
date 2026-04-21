
import time
from core.engine import GameEngine

def test_time_progression_speed_1():
    engine = GameEngine()
    engine.state.clock.speed_multiplier = 1
    engine.start()
    
    start_ticks = engine.state.clock.tick_count
    time.sleep(2.1) # Wait 2 seconds
    end_ticks = engine.state.clock.tick_count
    
    engine.stop()
    
    # At speed 1, should be ~2 ticks
    delta = end_ticks - start_ticks
    assert 1 <= delta <= 3, f"Expected ~2 ticks at speed 1, got {delta}"

def test_time_progression_speed_8():
    engine = GameEngine()
    engine.state.clock.speed_multiplier = 8
    engine.start()
    
    start_ticks = engine.state.clock.tick_count
    time.sleep(1.1) # Wait 1 second
    end_ticks = engine.state.clock.tick_count
    
    engine.stop()
    
    # At speed 8, should be ~8 ticks
    delta = end_ticks - start_ticks
    # Current broken logic might give 80 ticks
    assert 6 <= delta <= 10, f"Expected ~8 ticks at speed 8, got {delta}"

def test_trace_acceleration():
    engine = GameEngine()
    engine.state.clock.speed_multiplier = 8
    engine.state.connection.trace_active = True
    engine.state.connection.trace_progress = 0.0
    # Use small duration for test
    setattr(engine.state.connection, "_trace_duration", 2.0) 
    
    engine.start()
    time.sleep(0.5) # Should be 0.5 * 8 = 4 ticks of progress? 
    # If trace duration is 2.0 game seconds, it should be finished.
    
    prog = engine.state.connection.trace_progress
    engine.stop()
    
    assert prog >= 1.0, f"Trace should accelerate with game speed. Progress: {prog}"
