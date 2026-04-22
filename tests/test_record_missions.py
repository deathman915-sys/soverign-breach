"""
TDD tests for record mission generation and completion verification.
Phase 1 of porting Uplink record systems.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from core.game_state import Computer, GameState, Mission, NodeType, Record
from core.mission_engine import (
    MISSION_CHANGEACADEMIC,
    MISSION_CHANGECRIMINAL,
    MISSION_CHANGEMEDICAL,
    MISSION_CHANGESOCIAL,
    generate_missions,
    verify_mission_completion,
)


@pytest.fixture
def world():
    s = GameState()
    # Create an academic database server with records
    acad = Computer(
        ip="10.0.1.1",
        name="Academic Database",
        computer_type=NodeType.INTERNAL_SRV,
        hack_difficulty=90,
    )
    acad.recordbank.append(
        Record(
            name="John Doe",
            fields={
                "Name": "John Doe",
                "IQ": "145",
                "University": "None",
                "Other": "",
            },
            photo_index=1,
        )
    )
    acad.recordbank.append(
        Record(
            name="Jane Smith",
            fields={
                "Name": "Jane Smith",
                "IQ": "110",
                "University": "Harvard",
                "Other": "None",
            },
            photo_index=2,
        )
    )
    s.computers["10.0.1.1"] = acad

    # Create a criminal database server
    crim = Computer(
        ip="10.0.2.1",
        name="Criminal Database",
        computer_type=NodeType.INTERNAL_SRV,
        hack_difficulty=180,
    )
    crim.recordbank.append(
        Record(
            name="Alice",
            fields={"Name": "Alice", "Convictions": "None"},
            photo_index=3,
        )
    )
    s.computers["10.0.2.1"] = crim

    # Create a social security database server
    soc = Computer(
        ip="10.0.3.1",
        name="Social Security Database",
        computer_type=NodeType.INTERNAL_SRV,
        hack_difficulty=120,
    )
    soc.recordbank.append(
        Record(
            name="Bob",
            fields={
                "Name": "Bob",
                "Social Security": "12345678",
                "Marital Status": "Single",
                "Personal Status": "Employed",
            },
            photo_index=4,
        )
    )
    s.computers["10.0.3.1"] = soc

    # Create a medical database server
    med = Computer(
        ip="10.0.4.1",
        name="Medical Database",
        computer_type=NodeType.INTERNAL_SRV,
        hack_difficulty=120,
    )
    med.recordbank.append(
        Record(
            name="Carol",
            fields={
                "Name": "Carol",
                "Blood Type": "O+",
                "Allergies": "None",
                "Health Status": "Healthy",
            },
            photo_index=5,
        )
    )
    s.computers["10.0.4.1"] = med

    return s


class TestRecordMissionCompletion:
    def test_change_academic_verify_unaltered(self, world):
        """Mission should NOT complete if the record field hasn't been changed."""
        mission = Mission(
            id=1,
            mission_type=MISSION_CHANGEACADEMIC,
            completion_a="10.0.1.1",  # Academic DB IP
            completion_b="John Doe",  # target name
            completion_c="University",  # field to check
            completion_d="MIT",  # required substring
            completion_e="MIT",  # required substring (redundant in Uplink)
        )
        assert verify_mission_completion(world, mission) is False

    def test_change_academic_verify_altered(self, world):
        """Mission SHOULD complete if the record field contains the required substring."""
        # Simulate player altering the record
        rec = world.computers["10.0.1.1"].recordbank[0]
        rec.fields["University"] = "MIT, Class 1"

        mission = Mission(
            id=1,
            mission_type=MISSION_CHANGEACADEMIC,
            completion_a="10.0.1.1",
            completion_b="John Doe",
            completion_c="University",
            completion_d="MIT",
            completion_e="MIT",
        )
        assert verify_mission_completion(world, mission) is True

    def test_change_criminal_verify_unaltered(self, world):
        """Criminal record mission should not complete if convictions not changed."""
        mission = Mission(
            id=1,
            mission_type=MISSION_CHANGECRIMINAL,
            completion_a="10.0.2.1",
            completion_b="Alice",
            completion_c="Convictions",
            completion_d="Robbery",
            completion_e="Robbery",
        )
        assert verify_mission_completion(world, mission) is False

    def test_change_criminal_verify_altered(self, world):
        """Criminal record mission should complete if convictions contain the target."""
        rec = world.computers["10.0.2.1"].recordbank[0]
        rec.fields["Convictions"] = "None\nRobbery"

        mission = Mission(
            id=1,
            mission_type=MISSION_CHANGECRIMINAL,
            completion_a="10.0.2.1",
            completion_b="Alice",
            completion_c="Convictions",
            completion_d="Robbery",
            completion_e="Robbery",
        )
        assert verify_mission_completion(world, mission) is True

    def test_change_social_verify_unaltered(self, world):
        """Social security mission should not complete if status not changed."""
        mission = Mission(
            id=1,
            mission_type=MISSION_CHANGESOCIAL,
            completion_a="10.0.3.1",
            completion_b="Bob",
            completion_c="Personal Status",
            completion_d="Deceased",
            completion_e="Deceased",
        )
        assert verify_mission_completion(world, mission) is False

    def test_change_social_verify_altered(self, world):
        """Social security mission should complete if status contains the target."""
        rec = world.computers["10.0.3.1"].recordbank[0]
        rec.fields["Personal Status"] = "Deceased"

        mission = Mission(
            id=1,
            mission_type=MISSION_CHANGESOCIAL,
            completion_a="10.0.3.1",
            completion_b="Bob",
            completion_c="Personal Status",
            completion_d="Deceased",
            completion_e="Deceased",
        )
        assert verify_mission_completion(world, mission) is True

    def test_change_medical_verify_unaltered(self, world):
        """Medical record mission should not complete if health status not changed."""
        mission = Mission(
            id=1,
            mission_type=MISSION_CHANGEMEDICAL,
            completion_a="10.0.4.1",
            completion_b="Carol",
            completion_c="Health Status",
            completion_d="Critical",
            completion_e="Critical",
        )
        assert verify_mission_completion(world, mission) is False

    def test_change_medical_verify_altered(self, world):
        """Medical record mission should complete if health status contains the target."""
        rec = world.computers["10.0.4.1"].recordbank[0]
        rec.fields["Health Status"] = "Critical Condition"

        mission = Mission(
            id=1,
            mission_type=MISSION_CHANGEMEDICAL,
            completion_a="10.0.4.1",
            completion_b="Carol",
            completion_c="Health Status",
            completion_d="Critical",
            completion_e="Critical",
        )
        assert verify_mission_completion(world, mission) is True

    def test_missing_database_returns_false(self, world):
        """If the target database doesn't exist, mission cannot complete."""
        mission = Mission(
            id=1,
            mission_type=MISSION_CHANGEACADEMIC,
            completion_a="99.99.99.99",  # non-existent IP
            completion_b="John Doe",
            completion_c="University",
            completion_d="MIT",
            completion_e="MIT",
        )
        assert verify_mission_completion(world, mission) is False

    def test_missing_record_returns_false(self, world):
        """If the target person's record doesn't exist, mission cannot complete."""
        mission = Mission(
            id=1,
            mission_type=MISSION_CHANGEACADEMIC,
            completion_a="10.0.1.1",
            completion_b="Nonexistent Person",
            completion_c="University",
            completion_d="MIT",
            completion_e="MIT",
        )
        assert verify_mission_completion(world, mission) is False

    def test_missing_field_returns_false(self, world):
        """If the target field doesn't exist, mission cannot complete."""
        mission = Mission(
            id=1,
            mission_type=MISSION_CHANGEACADEMIC,
            completion_a="10.0.1.1",
            completion_b="John Doe",
            completion_c="Nonexistent Field",
            completion_d="MIT",
            completion_e="MIT",
        )
        assert verify_mission_completion(world, mission) is False

    def test_case_insensitive_match(self, world):
        """Field matching should be case-insensitive."""
        rec = world.computers["10.0.1.1"].recordbank[0]
        rec.fields["University"] = "mit, class 1"

        mission = Mission(
            id=1,
            mission_type=MISSION_CHANGEACADEMIC,
            completion_a="10.0.1.1",
            completion_b="John Doe",
            completion_c="University",
            completion_d="MIT",
            completion_e="MIT",
        )
        assert verify_mission_completion(world, mission) is True


class TestRecordMissionGeneration:
    def test_generates_all_record_types(self, world):
        """Generation should produce all 4 record mission types."""
        mission_types_found = set()
        # Generate many missions to ensure we get all types
        for _ in range(50):
            world.next_mission_id = len(world.missions) + 1
            missions = generate_missions(world, count=20)
            for m in missions:
                mission_types_found.add(m.mission_type)
            world.missions.clear()

        assert MISSION_CHANGEACADEMIC in mission_types_found
        assert MISSION_CHANGECRIMINAL in mission_types_found
        assert MISSION_CHANGESOCIAL in mission_types_found
        assert MISSION_CHANGEMEDICAL in mission_types_found

    def test_record_mission_has_completion_criteria(self, world):
        """Record missions should have completion_a through completion_e set."""
        world.next_mission_id = 1
        # Generate until we get a record mission
        for _ in range(100):
            missions = generate_missions(world, count=50)
            for m in missions:
                if m.mission_type in (
                    MISSION_CHANGEACADEMIC,
                    MISSION_CHANGECRIMINAL,
                    MISSION_CHANGESOCIAL,
                    MISSION_CHANGEMEDICAL,
                ):
                    assert m.completion_a is not None, "completion_a (DB IP) should be set"
                    assert m.completion_b is not None, "completion_b (person name) should be set"
                    assert m.completion_c is not None, "completion_c (field name) should be set"
                    assert m.completion_d is not None, "completion_d (required value) should be set"
                    assert m.completion_e is not None, "completion_e (required value) should be set"
                    return
            world.missions.clear()

        pytest.fail("No record missions generated after 100 attempts")

    def test_record_mission_target_exists(self, world):
        """Record mission's target person should exist in the database."""
        world.next_mission_id = 1
        for _ in range(50):
            missions = generate_missions(world, count=50)
            for m in missions:
                if m.mission_type in (
                    MISSION_CHANGEACADEMIC,
                    MISSION_CHANGECRIMINAL,
                    MISSION_CHANGESOCIAL,
                    MISSION_CHANGEMEDICAL,
                ):
                    db = world.computers.get(m.completion_a)
                    assert db is not None, f"Database {m.completion_a} should exist"
                    record = next(
                        (r for r in db.recordbank if r.name == m.completion_b), None
                    )
                    assert record is not None, f"Record {m.completion_b} should exist in DB"
                    return
            world.missions.clear()

        pytest.fail("No record missions generated after 50 attempts")
