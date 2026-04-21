"""
Onlink-Clone: Event Scheduler Tests

Tests event scheduling, processing, subscription fees,
and mission generation events.
"""

import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from core.game_state import GameState
from core.event_scheduler import (
    schedule_event,
    process_events,
    schedule_initial_events,
    schedule_trace_consequences,
    EVENT_SUBSCRIPTION,
    EVENT_MISSION_GENERATE,
    EVENT_WARNING,
    EVENT_FINE,
    EVENT_ARREST,
)


@pytest.fixture
def state():
    s = GameState()
    s.player.balance = 5000
    return s


class TestScheduleEvent:
    def test_schedule_creates_event(self, state):
        event = schedule_event(state, EVENT_WARNING, 100, {"message": "test"})
        assert event.id > 0
        assert event.event_type == EVENT_WARNING
        assert event.trigger_tick == 100
        assert len(state.scheduled_events) == 1

    def test_schedule_increments_id(self, state):
        e1 = schedule_event(state, EVENT_WARNING, 100)
        e2 = schedule_event(state, EVENT_WARNING, 200)
        assert e2.id > e1.id


class TestProcessEvents:
    def test_process_future_event(self, state):
        schedule_event(state, EVENT_WARNING, 1000, {"message": "future"})
        results = process_events(state, 50)
        assert len(results) == 0
        assert len(state.scheduled_events) == 1

    def test_process_due_event(self, state):
        schedule_event(state, EVENT_WARNING, 100, {"message": "due"})
        results = process_events(state, 100)
        assert len(results) == 1
        assert results[0]["type"] == "warning"

    def test_process_removes_processed(self, state):
        schedule_event(state, EVENT_WARNING, 100, {"message": "due"})
        process_events(state, 100)
        assert len(state.scheduled_events) == 0

    def test_process_keeps_pending(self, state):
        schedule_event(state, EVENT_WARNING, 100, {"message": "due"})
        schedule_event(state, EVENT_WARNING, 500, {"message": "pending"})
        process_events(state, 100)
        assert len(state.scheduled_events) == 1


class TestSubscriptionFee:
    def test_subscription_deducts_balance(self, state):
        schedule_event(state, EVENT_SUBSCRIPTION, 100, {"amount": 300})
        process_events(state, 100)
        assert state.player.balance == 5000 - 300

    def test_subscription_reschedules(self, state):
        schedule_event(
            state,
            EVENT_SUBSCRIPTION,
            100,
            {
                "amount": 300,
                "recurring_interval": 500,
            },
        )
        process_events(state, 100)
        assert len(state.scheduled_events) == 1
        assert state.scheduled_events[0].trigger_tick == 600


class TestFine:
    def test_fine_deducts_balance(self, state):
        schedule_event(state, EVENT_FINE, 100, {"amount": 500, "computer_name": "Test"})
        process_events(state, 100)
        assert state.player.balance == 5000 - 500

    def test_fine_creates_message(self, state):
        msg_before = len(state.messages)
        schedule_event(state, EVENT_FINE, 100, {"amount": 500, "computer_name": "Test"})
        process_events(state, 100)
        assert len(state.messages) == msg_before + 1


class TestMissionGenerate:
    def test_mission_generate_creates_missions(self, state):
        from core.world_generator import generate_world

        generate_world(state)
        mission_count_before = len(state.missions)
        schedule_event(state, EVENT_MISSION_GENERATE, 100, {"count": 3})
        process_events(state, 100)
        assert len(state.missions) == mission_count_before + 3

    def test_mission_generate_reschedules(self, state):
        from core.world_generator import generate_world

        generate_world(state)
        schedule_event(
            state,
            EVENT_MISSION_GENERATE,
            100,
            {
                "count": 3,
                "recurring_interval": 2000,
            },
        )
        process_events(state, 100)
        assert len(state.scheduled_events) == 1
        assert state.scheduled_events[0].trigger_tick == 2100


class TestScheduleInitialEvents:
    def test_schedules_subscription(self, state):
        schedule_initial_events(state, 0)
        sub_events = [
            e for e in state.scheduled_events if e.event_type == EVENT_SUBSCRIPTION
        ]
        assert len(sub_events) == 1
        assert sub_events[0].trigger_tick == 5000

    def test_schedules_mission_generate(self, state):
        schedule_initial_events(state, 0)
        mission_events = [
            e for e in state.scheduled_events if e.event_type == EVENT_MISSION_GENERATE
        ]
        assert len(mission_events) == 1
        assert mission_events[0].trigger_tick == 1000


class TestScheduleTraceConsequences:
    def test_low_difficulty_schedules_warning_and_fine(self, state):
        schedule_trace_consequences(state, "TargetComp", 1000, hack_difficulty=50.0)

        # Should have 2 events: warning and fine
        assert len(state.scheduled_events) == 2

        warning = next(
            e for e in state.scheduled_events if e.event_type == EVENT_WARNING
        )
        fine = next(e for e in state.scheduled_events if e.event_type == EVENT_FINE)

        assert warning.trigger_tick == 1000 + 50
        assert "TargetComp" in warning.data

        assert fine.trigger_tick == 1000 + 500

        fine_data = json.loads(fine.data)
        assert fine_data["amount"] == 1000  # max(500, 50 * 20)
        assert fine_data["computer_name"] == "TargetComp"

    def test_high_difficulty_schedules_arrest(self, state):
        schedule_trace_consequences(state, "TargetComp", 1000, hack_difficulty=150.0)

        # Should have 3 events: warning, fine, and arrest
        assert len(state.scheduled_events) == 3

        arrest = next(e for e in state.scheduled_events if e.event_type == EVENT_ARREST)
        assert arrest.trigger_tick == 1000 + 2000

        arrest_data = json.loads(arrest.data)
        assert arrest_data["computer_name"] == "TargetComp"

    def test_fine_amount_minimum(self, state):
        schedule_trace_consequences(state, "TargetComp", 1000, hack_difficulty=10.0)
        fine = next(e for e in state.scheduled_events if e.event_type == EVENT_FINE)

        fine_data = json.loads(fine.data)
        assert fine_data["amount"] == 500  # max(500, 10 * 20)
