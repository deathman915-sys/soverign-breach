"""
Onlink-Clone: Mission Engine

Generates, tracks, and completes missions for the player.
Ported from the ajhenley fork — all SQLAlchemy replaced with GameState ops.
"""

from __future__ import annotations

import logging
import random

from core import constants as C
from core.game_state import DataFile, GameState, Message, Mission, NodeType
from core.name_generator import generate_company_name

log = logging.getLogger(__name__)

# Mission types
MISSION_STEALFILE = 0
MISSION_DELETEDATA = 1
MISSION_CHANGEACADEMIC = 2
MISSION_CHANGECRIMINAL = 3
MISSION_CHANGESOCIAL = 4
MISSION_CHANGEMEDICAL = 5
MISSION_TRACEUSER = 6
MISSION_FRAMEUSER = 7
MISSION_REMOVECOMPUTER = 8
MISSION_SPECIAL = 9

MISSION_DESCRIPTIONS = {
    MISSION_STEALFILE: "Steal the specified file from the target server.",
    MISSION_DELETEDATA: "Delete all data files on the target server.",
    MISSION_CHANGEACADEMIC: "Modify the academic records of a specific student.",
    MISSION_CHANGECRIMINAL: "Alter the criminal history of a specific individual.",
    MISSION_CHANGESOCIAL: "Update the social security details of a target person.",
    MISSION_CHANGEMEDICAL: "Edit the medical records of a patient.",
}


def generate_missions(state: GameState, count: int = 5) -> list[Mission]:
    """Generate count new missions and add them to state.missions."""
    rng = random.Random()
    generated = []

    # Valid targets for file missions
    target_computers = [
        comp for comp in state.computers.values()
        if comp.computer_type in (NodeType.INTERNAL_SRV, NodeType.MAINFRAME)
        and comp.company_name not in ("Player", "Uplink Corporation")
    ]

    for _ in range(count):
        m_type = rng.choice([MISSION_STEALFILE, MISSION_DELETEDATA, MISSION_CHANGEACADEMIC, MISSION_CHANGECRIMINAL, MISSION_CHANGESOCIAL, MISSION_CHANGEMEDICAL])
        employer = generate_company_name(rng)

        if m_type in (MISSION_CHANGEACADEMIC, MISSION_CHANGECRIMINAL, MISSION_CHANGESOCIAL, MISSION_CHANGEMEDICAL):
            mission = _generate_record_mission(state, rng, m_type, employer)
        else:
            mission = _generate_file_mission(state, rng, m_type, employer, target_computers)

        if mission:
            state.next_mission_id += 1
            state.missions.append(mission)
            generated.append(mission)

    return generated


def _generate_record_mission(state: GameState, rng: random.Random, m_type: int, employer: str) -> Mission | None:
    """Helper for record-based mission generation."""
    db_map = {
        MISSION_CHANGEACADEMIC: C.IP_ACADEMICDATABASE,
        MISSION_CHANGECRIMINAL: C.IP_GLOBALCRIMINALDATABASE,
        MISSION_CHANGESOCIAL: C.IP_SOCIALSECURITYDATABASE,
        MISSION_CHANGEMEDICAL: C.IP_CENTRALMEDICALDATABASE,
    }

    record_fields = {
        MISSION_CHANGEACADEMIC: [("University", "None", "MIT"), ("IQ", "90", "155"), ("Other", "None", "Graduated")],
        MISSION_CHANGECRIMINAL: [("Convictions", "None", "Robbery"), ("Convictions", "None", "Fraud")],
        MISSION_CHANGESOCIAL: [("Personal Status", "Employed", "Deceased"), ("Marital Status", "Single", "Married")],
        MISSION_CHANGEMEDICAL: [("Health Status", "Healthy", "Critical"), ("Allergies", "None", "Penicillin")],
    }

    db_ip = db_map[m_type]
    db = state.computers.get(db_ip)
    if not db or not db.recordbank:
        return None

    record = rng.choice(db.recordbank)
    field_options = record_fields.get(m_type, [])
    if not field_options:
        return None

    field_name, old_val, new_val = rng.choice(field_options)
    difficulty = max(1, int(db.hack_difficulty / 20))
    payment = int(difficulty * rng.randint(500, 1500))

    descriptions = {
        MISSION_CHANGEACADEMIC: f"Change {record.name}'s {field_name} from '{old_val}' to '{new_val}'.",
        MISSION_CHANGECRIMINAL: f"Add '{new_val}' to {record.name}'s criminal record.",
        MISSION_CHANGESOCIAL: f"Set {record.name}'s {field_name} to '{new_val}'.",
        MISSION_CHANGEMEDICAL: f"Change {record.name}'s {field_name} to '{new_val}'."
    }

    return Mission(
        id=state.next_mission_id, mission_type=m_type, description=descriptions[m_type],
        employer_name=employer, payment=payment, original_payment=payment, negotiated_payment=payment,
        difficulty=difficulty, min_rating=max(0, difficulty - 2),
        target_computer_ip=db_ip, completion_a=db_ip, completion_b=record.name,
        completion_c=field_name, completion_d=new_val, completion_e=new_val,
        created_at_tick=state.clock.tick_count,
        due_at_tick=state.clock.tick_count + rng.randint(2000, 8000)
    )


def _generate_file_mission(state: GameState, rng: random.Random, m_type: int, employer: str, target_computers: list) -> Mission | None:
    """Helper for file-based mission generation."""
    if not target_computers:
        return None
    target = rng.choice(target_computers)
    difficulty = max(1, int(target.hack_difficulty / 5))
    payment = int(difficulty * rng.randint(500, 1500))

    if m_type == MISSION_STEALFILE:
        if not target.files:
            target.files.append(DataFile(filename="secret_research.dat", size=5))
        filename = rng.choice(target.files).filename
        desc = f"Steal the file '{filename}' from {target.company_name}'s servers at {target.ip}."
        comp_b = filename
    elif m_type == MISSION_DELETEDATA:
        desc = f"Delete all data files on {target.company_name}'s system at {target.ip}."
        comp_b = "ALL_FILES"
    else:
        desc = MISSION_DESCRIPTIONS.get(m_type, "Complete a hacking task.")
        comp_b = None

    return Mission(
        id=state.next_mission_id, mission_type=m_type, description=desc,
        employer_name=employer, payment=payment, original_payment=payment, negotiated_payment=payment,
        difficulty=difficulty, min_rating=max(0, difficulty - 2),
        target_computer_ip=target.ip, completion_a=target.ip, completion_b=comp_b,
        created_at_tick=state.clock.tick_count,
        due_at_tick=state.clock.tick_count + rng.randint(2000, 8000)
    )

def get_available_missions(state: GameState) -> list[dict]:
    """Return missions the player can accept based on their rating."""
    available = []
    for m in state.missions:
        if m.is_accepted or m.is_completed:
            continue
        if m.min_rating > state.player.uplink_rating:
            continue
        available.append(
            {
                "id": m.id,
                "type": m.mission_type,
                "description": m.description,
                "employer": m.employer_name,
                "payment": m.payment,
                "original_payment": m.original_payment,
                "is_negotiated": m.is_negotiated,
                "difficulty": m.difficulty,
                "target_ip": m.target_computer_ip,
            }
        )
    return available


def accept_mission(state: GameState, mission_id: int) -> dict:
    """Accept a mission. Returns success/failure dict."""
    for m in state.missions:
        if m.id == mission_id and not m.is_accepted:
            m.is_accepted = True
            m.accepted_by = state.player.handle

            # Send acceptance email
            state.messages.append(
                Message(
                    id=state.next_message_id,
                    from_name=m.employer_name,
                    subject=f"Mission Accepted: {m.description[:50]}",
                    body=(
                        f"Dear {state.player.handle},\n\n"
                        f"Your acceptance of this mission has been recorded.\n\n"
                        f"Target: {m.target_computer_ip}\n"
                        f"Payment on completion: {m.payment}c\n\n"
                        f"Good luck.\n- {m.employer_name}"
                    ),
                    created_at_tick=state.clock.tick_count,
                )
            )
            state.next_message_id += 1

            return {"success": True, "mission_id": m.id}
    return {"success": False, "error": "Mission not found or already accepted"}


def verify_mission_completion(state: GameState, mission: Mission) -> bool:
    """Check if the requirements for a mission have been met.
    Uses Uplink-style 5-completion-string verification for record missions.
    """
    if mission.mission_type == MISSION_STEALFILE:
        # completion_b is the filename. Check if it exists in player VFS.
        target_file = mission.completion_b
        for f in state.vfs.files:
            if f.filename == target_file:
                return True
        return False

    elif mission.mission_type == MISSION_DELETEDATA:
        # completion_a is the target IP. Check if all data files are gone.
        target_ip = mission.completion_a
        comp = state.computers.get(target_ip)
        if not comp:
            return False
        # Filter for data files (file_type == 1)
        data_files = [f for f in comp.files if f.file_type == 1]
        return len(data_files) == 0

    elif mission.mission_type in (
        MISSION_CHANGEACADEMIC,
        MISSION_CHANGECRIMINAL,
        MISSION_CHANGESOCIAL,
        MISSION_CHANGEMEDICAL,
    ):
        # completion_a = database IP
        # completion_b = target person name
        # completion_c = field name to check
        # completion_d = required substring (case-insensitive)
        # completion_e = required substring (case-insensitive, same as d in Uplink)
        db = state.computers.get(mission.completion_a)
        if not db:
            return False
        record = next((r for r in db.recordbank if r.name == mission.completion_b), None)
        if not record:
            return False
        field_value = record.fields.get(mission.completion_c)
        if not field_value:
            return False
        # Case-insensitive substring check (Uplink style)
        field_lower = field_value.lower()
        required_d = mission.completion_d.lower() if mission.completion_d else ""
        required_e = mission.completion_e.lower() if mission.completion_e else ""
        return required_d in field_lower and required_e in field_lower

    # For any other types, return True
    return True


def complete_mission(state: GameState, mission_id: int) -> dict:
    """Verify and mark a mission as completed."""
    for m in state.missions:
        if m.id == mission_id and m.is_accepted and not m.is_completed:
            if not verify_mission_completion(state, m):
                return {
                    "success": False,
                    "error": "Mission requirements not met. Check your objective.",
                }

            m.is_completed = True
            state.player.balance += m.payment

            # Rating boost
            rating_gain = max(1, m.difficulty // 3)
            state.player.uplink_rating = min(
                16, state.player.uplink_rating + rating_gain
            )

            # Payment notification
            state.messages.append(
                Message(
                    id=state.next_message_id,
                    from_name=m.employer_name,
                    subject="Mission Completed",
                    body=(
                        f"Congratulations, {state.player.handle}.\n\n"
                        f"Payment of {m.payment}c has been credited to your account.\n\n"
                        f"- {m.employer_name}"
                    ),
                    created_at_tick=state.clock.tick_count,
                )
            )
            state.next_message_id += 1

            log.info("Mission %d completed, payment: %d", m.id, m.payment)
            return {"success": True, "payment": m.payment, "rating_gain": rating_gain}

    return {"success": False, "error": "Mission not found or not accepted"}


def check_mission_deadlines(state: GameState) -> list[dict]:
    """Check for expired missions. Returns list of failure events."""
    failures = []
    for m in state.missions:
        if m.is_accepted and not m.is_completed and m.due_at_tick:
            if state.clock.tick_count >= m.due_at_tick:
                m.is_completed = True  # Mark as failed
                failures.append(
                    {
                        "type": "mission_failed",
                        "mission_id": m.id,
                        "description": m.description,
                    }
                )
                # Send failure email
                state.messages.append(
                    Message(
                        id=state.next_message_id,
                        from_name=m.employer_name,
                        subject="Mission Failed",
                        body=f"You failed to complete the mission in time.\n- {m.employer_name}",
                        created_at_tick=state.clock.tick_count,
                    )
                )
                state.next_message_id += 1
    return failures


def get_active_missions(state: GameState) -> list[dict]:
    """Return missions the player has accepted but not yet completed."""
    active = []
    for m in state.missions:
        if m.is_accepted and not m.is_completed:
            ticks_left = None
            if m.due_at_tick:
                ticks_left = max(0, m.due_at_tick - state.clock.tick_count)
            active.append(
                {
                    "id": m.id,
                    "type": m.mission_type,
                    "description": m.description,
                    "employer": m.employer_name,
                    "payment": m.payment,
                    "difficulty": m.difficulty,
                    "target_ip": m.target_computer_ip,
                    "completion_b": m.completion_b,
                    "ticks_left": ticks_left,
                    "is_negotiated": m.is_negotiated,
                }
            )
    return active


def negotiate_mission(
    state: GameState, mission_id: int, increase_percentage: float = 0.1
) -> dict:
    """
    Attempt to negotiate higher payment for a mission.
    Returns dict with success flag and new payment if successful.
    """
    for m in state.missions:
        if m.id == mission_id and not m.is_accepted and not m.is_completed:
            # Employer may refuse (20% chance)
            if random.random() < 0.2:
                return {"success": False, "msg": "Employer refuses to negotiate."}

            # Increase payment by percentage, but not more than 2x original
            new_payment = int(m.payment * (1.0 + increase_percentage))
            max_payment = m.original_payment * 2
            if new_payment > max_payment:
                new_payment = max_payment

            m.payment = new_payment
            m.is_negotiated = True
            return {"success": True, "new_payment": new_payment}

    return {"success": False, "msg": "Mission not found or already accepted."}
