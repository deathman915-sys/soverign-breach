"""
TDD tests for record screen UI rendering and HTML generation.
Phase 2 of porting Uplink record systems.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from core.game_state import Computer, GameState, NodeType, Record
from core.remote_controller import RemoteController, ScreenHTMLBuilder


@pytest.fixture
def world_with_db():
    """A GameState with an academic database server populated with records."""
    s = GameState()
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
    return s


@pytest.fixture
def rc(world_with_db):
    return RemoteController(world_with_db)


class TestRecordScreenRenderers:
    def test_academic_screen_returns_html(self, rc):
        """Academic screen should return HTML with record names."""
        comp = rc.state.computers["10.0.1.1"]
        data = rc._render_academic_screen(comp)
        assert "html" in data
        assert "John Doe" in data["html"]
        assert "Jane Smith" in data["html"]
        assert "Academic Records" in data["html"]

    def test_criminal_screen_returns_html(self, rc):
        """Criminal screen should return HTML with record data."""
        comp = rc.state.computers["10.0.1.1"]
        data = rc._render_criminal_screen(comp)
        assert "html" in data
        assert "Criminal Records" in data["html"]

    def test_social_security_screen_returns_html(self, rc):
        """Social security screen should return HTML."""
        comp = rc.state.computers["10.0.1.1"]
        data = rc._render_social_security_screen(comp)
        assert "html" in data
        assert "Social Security Records" in data["html"]

    def test_medical_screen_returns_html(self, rc):
        """Medical screen should return HTML."""
        comp = rc.state.computers["10.0.1.1"]
        data = rc._render_medical_screen(comp)
        assert "html" in data
        assert "Medical Records" in data["html"]

    def test_record_screen_has_clickable_entries(self, rc):
        """HTML should have onclick handlers for viewRecord()."""
        comp = rc.state.computers["10.0.1.1"]
        data = rc._render_academic_screen(comp)
        assert 'onclick="viewRecord(0' in data["html"]
        assert 'onclick="viewRecord(1' in data["html"]

    def test_record_screen_has_record_data_script(self, rc):
        """HTML should include window._recordData for JS access."""
        comp = rc.state.computers["10.0.1.1"]
        data = rc._render_academic_screen(comp)
        assert 'window._recordData' in data["html"]
        assert '"John Doe"' in data["html"]

    def test_record_screen_empty_records(self, rc):
        """Screen with no records should show 'No records found'."""
        comp = rc.state.computers["10.0.1.1"]
        comp.recordbank.clear()
        data = rc._render_academic_screen(comp)
        assert "No records found" in data["html"]


class TestRecordScreenHTMLBuilder:
    def test_build_record_screen_with_records(self):
        """Builder should produce valid HTML for records."""
        records = [
            {"name": "Test User", "fields": {"Name": "Test User", "IQ": "100"}, "photo_index": 1},
        ]
        html = ScreenHTMLBuilder.build_record_screen_html("Test Records", records, "cyan")
        assert "Test User" in html
        assert "viewRecord" in html
        assert "window._recordData" in html

    def test_build_record_screen_empty(self):
        """Builder should handle empty record list."""
        html = ScreenHTMLBuilder.build_record_screen_html("Test Records", [], "cyan")
        assert "No records found" in html


class TestRecordAlteration:
    def test_alter_record_updates_field(self, rc):
        """alter_record() should update the specified field."""
        comp = rc.state.computers["10.0.1.1"]
        # Verify initial state
        assert comp.recordbank[0].fields["University"] == "None"

        result = rc.alter_record("10.0.1.1", "John Doe", "University", "MIT")
        assert result["success"] is True

        # Verify the field was updated
        assert comp.recordbank[0].fields["University"] == "MIT"

    def test_alter_record_nonexistent_computer(self, rc):
        """alter_record() should fail for non-existent computer."""
        result = rc.alter_record("99.99.99.99", "John Doe", "University", "MIT")
        assert result["success"] is False
        assert "Computer not found" in result["error"]

    def test_alter_record_nonexistent_record(self, rc):
        """alter_record() should fail for non-existent record."""
        result = rc.alter_record("10.0.1.1", "Nobody", "University", "MIT")
        assert result["success"] is False
        assert "Record not found" in result["error"]

    def test_alter_record_end_to_end_flow(self, rc):
        """Full flow: alter record → verify mission completion."""
        from core.mission_engine import MISSION_CHANGEACADEMIC, Mission, verify_mission_completion

        # Create a mission requiring "University" to contain "MIT"
        mission = Mission(
            id=1,
            mission_type=MISSION_CHANGEACADEMIC,
            completion_a="10.0.1.1",
            completion_b="John Doe",
            completion_c="University",
            completion_d="MIT",
            completion_e="MIT",
        )

        # Initially should not be complete
        assert verify_mission_completion(rc.state, mission) is False

        # Alter the record
        rc.alter_record("10.0.1.1", "John Doe", "University", "MIT, Class 1")

        # Now should be complete
        assert verify_mission_completion(rc.state, mission) is True
