
from core.game_state import Computer, GameState, Record
from core.persistence import _update_dataclass_from_dict


def test_computer_record_bank_storage():
    state = GameState()
    target = Computer(ip="1.1.1.1", name="International Academic Database")

    # Create an academic record
    rec = Record(name="John Doe", fields={
        "Degree": "Computer Science",
        "Grade": "A",
        "Status": "Graduated"
    })
    target.recordbank.append(rec)
    state.computers["1.1.1.1"] = target

    assert len(target.recordbank) == 1
    assert target.recordbank[0].name == "John Doe"
    assert target.recordbank[0].fields["Grade"] == "A"

def test_record_hydration_persistence():
    state = GameState()
    data = {
        "computers": {
            "1.1.1.1": {
                "ip": "1.1.1.1",
                "recordbank": [
                    {
                        "name": "Jane Smith",
                        "fields": {"Criminal Record": "None", "Status": "Clean"}
                    }
                ]
            }
        }
    }

    _update_dataclass_from_dict(state, data)

    target = state.computers["1.1.1.1"]
    assert isinstance(target.recordbank[0], Record)
    assert target.recordbank[0].name == "Jane Smith"
    assert target.recordbank[0].fields["Status"] == "Clean"

def test_world_gen_creates_all_database_records():
    from core import constants as C
    from core.world_generator import generate_world
    state = GameState()
    generate_world(state)

    databases = [
        C.IP_ACADEMICDATABASE,
        C.IP_GLOBALCRIMINALDATABASE,
        C.IP_SOCIALSECURITYDATABASE,
        C.IP_CENTRALMEDICALDATABASE
    ]

    for ip in databases:
        comp = state.computers.get(ip)
        assert comp is not None
        assert len(comp.recordbank) > 0, f"Database {ip} should have records"
        # Check player record exists in each
        player_rec = next((r for r in comp.recordbank if r.name == state.player.name), None)
        assert player_rec is not None, f"Player record missing from {ip}"
