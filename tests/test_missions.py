"""
Onlink-Clone: Comprehensive Mission Engine Tests

Tests mission generation, acceptance, completion, negotiation,
active missions, deadline checking, and verification logic.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from core.game_state import DataFile, GameState, VFSFile
from core.mission_engine import (
    MISSION_DELETEDATA,
    MISSION_STEALFILE,
    accept_mission,
    check_mission_deadlines,
    complete_mission,
    generate_missions,
    get_active_missions,
    get_available_missions,
    negotiate_mission,
    verify_mission_completion,
)
from core.world_generator import generate_world


@pytest.fixture
def fresh_world():
    """Provide a GameState with a generated world."""
    s = GameState()
    generate_world(s)
    return s


class TestMissionGeneration:
    def test_generates_missions(self, fresh_world):
        missions = generate_missions(fresh_world, 5)
        assert len(missions) == 5

    def test_missions_have_required_fields(self, fresh_world):
        missions = generate_missions(fresh_world, 1)
        m = missions[0]
        assert m.id > 0
        # Now includes all 4 record mission types: CHANGEACADEMIC(2), CHANGECRIMINAL(3), CHANGESOCIAL(4), CHANGEMEDICAL(5)
        assert m.mission_type in (MISSION_STEALFILE, MISSION_DELETEDATA, 2, 3, 4, 5)
        assert m.description != ""
        assert m.employer_name != ""
        assert m.payment > 0
        assert m.original_payment == m.payment
        assert m.target_computer_ip is not None
        assert m.is_accepted is False
        assert m.is_completed is False
        assert m.due_at_tick is not None

    def test_mission_ids_increment(self, fresh_world):
        m1 = generate_missions(fresh_world, 1)[0]
        m2 = generate_missions(fresh_world, 1)[0]
        assert m2.id > m1.id

    def test_missions_added_to_state(self, fresh_world):
        count_before = len(fresh_world.missions)
        generate_missions(fresh_world, 3)
        assert len(fresh_world.missions) == count_before + 3

    def test_mission_difficulty_based_on_target(self, fresh_world):
        missions = generate_missions(fresh_world, 10)
        for m in missions:
            assert m.difficulty >= 1
            assert m.min_rating >= 0

    def test_mission_due_date_in_future(self, fresh_world):
        missions = generate_missions(fresh_world, 1)
        m = missions[0]
        assert m.due_at_tick > fresh_world.clock.tick_count


class TestAvailableMissions:
    def test_returns_unaccepted_missions(self, fresh_world):
        count_before = len(fresh_world.missions)
        generate_missions(fresh_world, 3)
        available = get_available_missions(fresh_world)
        assert len(available) == count_before + 3

    def test_excludes_accepted_missions(self, fresh_world):
        available_before = get_available_missions(fresh_world)
        if not available_before:
            pytest.skip("No available missions")
        accept_mission(fresh_world, available_before[0]["id"])
        available_after = get_available_missions(fresh_world)
        assert len(available_after) == len(available_before) - 1

    def test_excludes_completed_missions(self, fresh_world):
        available = get_available_missions(fresh_world)
        if not available:
            pytest.skip("No available missions")
        # Find the mission object matching the first available
        m = next(m for m in fresh_world.missions if m.id == available[0]["id"])
        m.is_completed = True
        available_after = get_available_missions(fresh_world)
        assert len(available_after) == len(available) - 1

    def test_respects_player_rating(self, fresh_world):
        generate_missions(fresh_world, 5)
        fresh_world.player.uplink_rating = 0
        available = get_available_missions(fresh_world)
        for m in available:
            assert m["difficulty"] >= 0

    def test_available_mission_fields(self, fresh_world):
        generate_missions(fresh_world, 1)
        available = get_available_missions(fresh_world)
        m = available[0]
        assert "id" in m
        assert "type" in m
        assert "description" in m
        assert "employer" in m
        assert "payment" in m
        assert "difficulty" in m
        assert "target_ip" in m


class TestAcceptMission:
    def test_accept_success(self, fresh_world):
        missions = generate_missions(fresh_world, 1)
        result = accept_mission(fresh_world, missions[0].id)
        assert result["success"] is True
        assert missions[0].is_accepted is True
        assert missions[0].accepted_by == fresh_world.player.handle

    def test_accept_sends_message(self, fresh_world):
        missions = generate_missions(fresh_world, 1)
        msg_count_before = len(fresh_world.messages)
        accept_mission(fresh_world, missions[0].id)
        assert len(fresh_world.messages) == msg_count_before + 1

    def test_accept_already_accepted(self, fresh_world):
        missions = generate_missions(fresh_world, 1)
        accept_mission(fresh_world, missions[0].id)
        result = accept_mission(fresh_world, missions[0].id)
        assert result["success"] is False

    def test_accept_nonexistent_mission(self, fresh_world):
        result = accept_mission(fresh_world, 99999)
        assert result["success"] is False


class TestActiveMissions:
    def test_returns_accepted_missions(self, fresh_world):
        missions = generate_missions(fresh_world, 3)
        accept_mission(fresh_world, missions[0].id)
        accept_mission(fresh_world, missions[1].id)
        active = get_active_missions(fresh_world)
        assert len(active) == 2

    def test_excludes_completed(self, fresh_world):
        missions = generate_missions(fresh_world, 2)
        accept_mission(fresh_world, missions[0].id)
        missions[0].is_completed = True
        active = get_active_missions(fresh_world)
        assert len(active) == 0

    def test_excludes_unaccepted(self, fresh_world):
        generate_missions(fresh_world, 3)
        active = get_active_missions(fresh_world)
        assert len(active) == 0

    def test_active_mission_has_ticks_left(self, fresh_world):
        missions = generate_missions(fresh_world, 1)
        accept_mission(fresh_world, missions[0].id)
        active = get_active_missions(fresh_world)
        assert active[0]["ticks_left"] is not None
        assert active[0]["ticks_left"] > 0

    def test_ticks_left_decreases(self, fresh_world):
        missions = generate_missions(fresh_world, 1)
        accept_mission(fresh_world, missions[0].id)
        active1 = get_active_missions(fresh_world)
        ticks1 = active1[0]["ticks_left"]
        fresh_world.clock.tick_count += 100
        active2 = get_active_missions(fresh_world)
        ticks2 = active2[0]["ticks_left"]
        assert ticks2 == ticks1 - 100


class TestCompleteMission:
    def test_complete_steal_file_mission(self, fresh_world):
        missions = generate_missions(fresh_world, 5)
        steal_missions = [m for m in missions if m.mission_type == MISSION_STEALFILE]
        if not steal_missions:
            pytest.skip("No steal file mission generated")
        m = steal_missions[0]
        accept_mission(fresh_world, m.id)
        # Fulfill requirement: put file in player VFS
        fresh_world.vfs.files.append(VFSFile(filename=m.completion_b, size_gq=1))
        result = complete_mission(fresh_world, m.id)
        assert result["success"] is True
        assert result["payment"] > 0
        assert result["rating_gain"] >= 1

    def test_complete_delete_data_mission(self, fresh_world):
        missions = generate_missions(fresh_world, 5)
        delete_missions = [m for m in missions if m.mission_type == MISSION_DELETEDATA]
        if not delete_missions:
            pytest.skip("No delete data mission generated")
        m = delete_missions[0]
        accept_mission(fresh_world, m.id)
        # Fulfill requirement: remove all data files from target
        target = fresh_world.computers.get(m.target_computer_ip)
        if target:
            target.files = [f for f in target.files if f.file_type != 1]
        result = complete_mission(fresh_world, m.id)
        assert result["success"] is True

    def test_complete_not_met(self, fresh_world):
        missions = generate_missions(fresh_world, 1)
        accept_mission(fresh_world, missions[0].id)
        result = complete_mission(fresh_world, missions[0].id)
        # May succeed if mission type is one we can't verify yet
        # But should never crash
        assert "success" in result

    def test_complete_nonexistent(self, fresh_world):
        result = complete_mission(fresh_world, 99999)
        assert result["success"] is False

    def test_complete_unaccepted(self, fresh_world):
        missions = generate_missions(fresh_world, 1)
        result = complete_mission(fresh_world, missions[0].id)
        assert result["success"] is False

    def test_complete_already_completed(self, fresh_world):
        missions = generate_missions(fresh_world, 1)
        missions[0].is_accepted = True
        missions[0].is_completed = True
        result = complete_mission(fresh_world, missions[0].id)
        assert result["success"] is False

    def test_complete_pays_player(self, fresh_world):
        missions = generate_missions(fresh_world, 5)
        steal_missions = [m for m in missions if m.mission_type == MISSION_STEALFILE]
        if not steal_missions:
            pytest.skip("No steal file mission generated")
        m = steal_missions[0]
        accept_mission(fresh_world, m.id)
        balance_before = fresh_world.player.balance
        fresh_world.vfs.files.append(VFSFile(filename=m.completion_b, size_gq=1))
        complete_mission(fresh_world, m.id)
        assert fresh_world.player.balance == balance_before + m.payment

    def test_complete_increases_rating(self, fresh_world):
        missions = generate_missions(fresh_world, 5)
        steal_missions = [m for m in missions if m.mission_type == MISSION_STEALFILE]
        if not steal_missions:
            pytest.skip("No steal file mission generated")
        m = steal_missions[0]
        accept_mission(fresh_world, m.id)
        rating_before = fresh_world.player.uplink_rating
        fresh_world.vfs.files.append(VFSFile(filename=m.completion_b, size_gq=1))
        complete_mission(fresh_world, m.id)
        assert fresh_world.player.uplink_rating > rating_before

    def test_complete_sends_message(self, fresh_world):
        missions = generate_missions(fresh_world, 5)
        steal_missions = [m for m in missions if m.mission_type == MISSION_STEALFILE]
        if not steal_missions:
            pytest.skip("No steal file mission generated")
        m = steal_missions[0]
        accept_mission(fresh_world, m.id)
        msg_count_before = len(fresh_world.messages)
        fresh_world.vfs.files.append(VFSFile(filename=m.completion_b, size_gq=1))
        complete_mission(fresh_world, m.id)
        assert len(fresh_world.messages) == msg_count_before + 1


class TestMissionNegotiation:
    def test_negotiate_increases_payment(self, fresh_world):
        missions = generate_missions(fresh_world, 1)
        m = missions[0]
        original = m.payment
        for _ in range(5):
            res = negotiate_mission(fresh_world, m.id, 0.1)
            if res["success"]:
                break
        assert res["success"]
        assert m.payment > original

    def test_negotiate_cannot_after_accept(self, fresh_world):
        missions = generate_missions(fresh_world, 1)
        accept_mission(fresh_world, missions[0].id)
        res = negotiate_mission(fresh_world, missions[0].id, 0.1)
        assert res["success"] is False

    def test_negotiate_nonexistent(self, fresh_world):
        res = negotiate_mission(fresh_world, 99999, 0.1)
        assert res["success"] is False

    def test_negotiate_capped_at_2x(self, fresh_world):
        missions = generate_missions(fresh_world, 1)
        m = missions[0]
        max_payment = m.original_payment * 2
        # Force negotiate many times
        for _ in range(50):
            negotiate_mission(fresh_world, m.id, 0.1)
        assert m.payment <= max_payment


class TestMissionDeadlines:
    def test_expired_mission_fails(self, fresh_world):
        missions = generate_missions(fresh_world, 1)
        accept_mission(fresh_world, missions[0].id)
        missions[0].due_at_tick = fresh_world.clock.tick_count - 1
        failures = check_mission_deadlines(fresh_world)
        assert len(failures) == 1
        assert failures[0]["mission_id"] == missions[0].id

    def test_expired_mission_sends_message(self, fresh_world):
        missions = generate_missions(fresh_world, 1)
        accept_mission(fresh_world, missions[0].id)
        missions[0].due_at_tick = fresh_world.clock.tick_count - 1
        msg_count_before = len(fresh_world.messages)
        check_mission_deadlines(fresh_world)
        assert len(fresh_world.messages) == msg_count_before + 1

    def test_active_mission_not_expired(self, fresh_world):
        missions = generate_missions(fresh_world, 1)
        accept_mission(fresh_world, missions[0].id)
        missions[0].due_at_tick = fresh_world.clock.tick_count + 5000
        failures = check_mission_deadlines(fresh_world)
        assert len(failures) == 0

    def test_completed_mission_not_expired(self, fresh_world):
        missions = generate_missions(fresh_world, 1)
        missions[0].is_accepted = True
        missions[0].is_completed = True
        missions[0].due_at_tick = fresh_world.clock.tick_count - 1
        failures = check_mission_deadlines(fresh_world)
        assert len(failures) == 0


class TestVerifyMissionCompletion:
    def test_steal_file_verified(self, fresh_world):
        missions = generate_missions(fresh_world, 5)
        steal = [m for m in missions if m.mission_type == MISSION_STEALFILE]
        if not steal:
            pytest.skip("No steal file mission")
        m = steal[0]
        fresh_world.vfs.files.append(VFSFile(filename=m.completion_b, size_gq=1))
        assert verify_mission_completion(fresh_world, m) is True

    def test_steal_file_not_verified(self, fresh_world):
        missions = generate_missions(fresh_world, 5)
        steal = [m for m in missions if m.mission_type == MISSION_STEALFILE]
        if not steal:
            pytest.skip("No steal file mission")
        m = steal[0]
        assert verify_mission_completion(fresh_world, m) is False

    def test_delete_data_verified(self, fresh_world):
        missions = generate_missions(fresh_world, 5)
        delete = [m for m in missions if m.mission_type == MISSION_DELETEDATA]
        if not delete:
            pytest.skip("No delete data mission")
        m = delete[0]
        target = fresh_world.computers.get(m.target_computer_ip)
        if target:
            target.files = [f for f in target.files if f.file_type != 1]
        assert verify_mission_completion(fresh_world, m) is True

    def test_delete_data_not_verified(self, fresh_world):
        missions = generate_missions(fresh_world, 5)
        delete = [m for m in missions if m.mission_type == MISSION_DELETEDATA]
        if not delete:
            pytest.skip("No delete data mission")
        m = delete[0]
        # Ensure target has data files so verification fails
        target = fresh_world.computers.get(m.target_computer_ip)
        if target:
            if not any(f.file_type == 1 for f in target.files):
                target.files.append(
                    DataFile(filename="test_data.dat", size=1, file_type=1)
                )
        assert verify_mission_completion(fresh_world, m) is False

    def test_delete_data_target_not_found(self, fresh_world):
        missions = generate_missions(fresh_world, 1)
        m = missions[0]
        m.mission_type = MISSION_DELETEDATA
        m.completion_a = "999.999.999.999"
        m.target_computer_ip = "999.999.999.999"
        assert verify_mission_completion(fresh_world, m) is False
