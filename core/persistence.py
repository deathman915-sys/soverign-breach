"""
Onlink-Clone: Persistence & Profile Management

Handles saving and loading the complete GameState to/from JSON.
"""

from __future__ import annotations

import os
import json
import logging
from dataclasses import asdict, is_dataclass, fields
from typing import Any, TypeVar, TYPE_CHECKING, get_args, get_type_hints

if TYPE_CHECKING:
    from core.game_state import GameState

log = logging.getLogger(__name__)

T = TypeVar("T")

# Use absolute path relative to project root (where web_main.py lives)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILES_DIR = os.path.join(BASE_DIR, "profiles")


def save_profile(state: GameState, file_path: str | None = None) -> bool:
    """Serialize the entire GameState to a JSON file."""
    if not state.player.handle or not state.player.handle.strip():
        log.error("Cannot save profile: handle is empty")
        return False
    
    if not os.path.exists(PROFILES_DIR):
        os.makedirs(PROFILES_DIR)
        
    if file_path is None:
        file_path = os.path.join(PROFILES_DIR, f"{state.player.handle}.json")

    try:
        data = asdict(state)
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        log.info(f"Profile saved: {file_path}")
        return True
    except Exception as e:
        log.error(f"Failed to save profile {file_path}: {e}")
        return False


def load_profile(state: GameState, file_path: str) -> bool:
    """Load JSON data into an existing GameState instance."""
    if not os.path.exists(file_path):
        log.error(f"Save file not found: {file_path}")
        return False

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        return load_profile_from_data(state, data)
    except Exception as e:
        log.error(f"Failed to load profile {file_path}: {e}", exc_info=True)
        return False


def load_profile_from_data(state: GameState, data: dict) -> bool:
    """Load a pre-parsed dict into an existing GameState instance."""
    try:
        _update_dataclass_from_dict(state, data)
        log.info("Profile loaded from data")
        return True
    except Exception as e:
        log.error(f"Failed to load profile from data: {e}", exc_info=True)
        return False


def list_profiles() -> list[str]:
    """Returns a list of handles (filenames without .json) in the profiles dir."""
    if not os.path.exists(PROFILES_DIR):
        log.warning(f"Profiles directory '{PROFILES_DIR}' not found.")
        return []

    profiles = []
    for f in os.listdir(PROFILES_DIR):
        if f.lower().endswith(".json"):
            handle = f[:-5] # remove .json
            if handle: # Skip empty filenames like ".json"
                profiles.append(handle)
    
    log.info(f"Listed {len(profiles)} profiles: {profiles}")
    return sorted(profiles)


def delete_profile(handle: str) -> bool:
    """Deletes a profile file (used for Disavowed/Game Over)."""
    file_path = os.path.join(PROFILES_DIR, f"{handle}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        log.info(f"Profile deleted: {file_path}")
        return True
    return False


def _update_dataclass_from_dict(obj: Any, data: dict):
    """
    Recursively updates a dataclass instance from a dictionary.
    Handles nested dataclasses, lists of dataclasses, and primitive types.
    """
    if not is_dataclass(obj) or not isinstance(data, dict):
        return

    # Use get_type_hints to resolve string annotations (due to from __future__ import annotations)
    try:
        type_hints = get_type_hints(type(obj))
    except Exception:
        type_hints = {}

    obj_fields = {f.name: f for f in fields(obj)}

    for key, value in data.items():
        if key not in obj_fields:
            continue

        attr = getattr(obj, key)
        field_type = type_hints.get(key, obj_fields[key].type)

        # 1. Nested Dataclass
        if is_dataclass(attr):
            _update_dataclass_from_dict(attr, value)

        # 2. List of Items
        elif isinstance(attr, list) and isinstance(value, list):
            # Try to get the item type from the field definition (e.g., list[Computer])
            args = get_args(field_type)
            item_type = args[0] if args else None
            
            new_list = []
            for item_data in value:
                if isinstance(item_data, dict):
                    # 1. Try identified dataclass type
                    if is_dataclass(item_type):
                        try:
                            item_obj = item_type()
                            _update_dataclass_from_dict(item_obj, item_data)
                            new_list.append(item_obj)
                        except Exception:
                            # Fallback if instantiation fails
                            fallback = _instantiate_model_from_dict(key, item_data)
                            new_list.append(fallback if fallback else item_data)
                    else:
                        # 2. Fallback to name-based mapping
                        item_obj = _instantiate_model_from_dict(key, item_data)
                        new_list.append(item_obj if item_obj else item_data)
                else:
                    new_list.append(item_data)
            setattr(obj, key, new_list)

        # 3. Dict of Items (e.g., dict[str, Computer])
        elif isinstance(attr, dict) and isinstance(value, dict):
            # Try to get the value type from the field definition (e.g., dict[str, Computer])
            args = get_args(field_type)
            val_type = args[1] if len(args) >= 2 else None

            new_dict = {}
            for k, v in value.items():
                if isinstance(v, dict):
                    # 1. Try identified dataclass type
                    if is_dataclass(val_type):
                        try:
                            item_obj = val_type()
                            _update_dataclass_from_dict(item_obj, v)
                            new_dict[k] = item_obj
                        except Exception:
                            # Fallback
                            fallback = _instantiate_model_from_dict(key, v)
                            new_dict[k] = fallback if fallback else v
                    else:
                        # 2. Fallback to name-based mapping
                        item_obj = _instantiate_model_from_dict(key, v)
                        new_dict[k] = item_obj if item_obj else v
                else:
                    new_dict[k] = v
            setattr(obj, key, new_dict)

        # 4. Primitive
        else:
            setattr(obj, key, value)


def _instantiate_model_from_dict(field_name: str, data: dict) -> Any:
    """Instantiates the correct GameState dataclass using the provided data."""
    from core import game_state as gs

    mapping = {
        "cpus": gs.CPUCore,
        "tasks": gs.RunningTask,
        "vfs_files": gs.VFSFile, # VFSState uses 'files' but we should check context
        "files": gs.DataFile,    # Computer uses 'files' for DataFile
        "computers": gs.Computer,
        "logs": gs.AccessLog,
        "security_systems": gs.SecuritySystem,
        "screens": gs.ComputerScreen,
        "missions": gs.Mission,
        "bank_accounts": gs.BankAccount,
        "loans": gs.LoanRecord,
        "stock_holdings": gs.StockHolding,
        "news": gs.NewsItem,
        "people": gs.Person,
        "manifests": gs.TransportManifest,
        "companies": gs.Company,
        "scheduled_events": gs.ScheduledEvent,
        "passive_traces": gs.PassiveTrace,
        "nodes": gs.ConnectionNode,
        "recordbank": gs.Record,
    }

    cls = mapping.get(field_name)
    if cls:
        try:
            # First create with provided data as kwargs for positional support
            instance = cls(**data)
            # Then perform deep update for any nested structures
            _update_dataclass_from_dict(instance, data)
            return instance
        except TypeError:
            # Fallback for complex nesting if direct instantiation fails
            instance = cls()
            _update_dataclass_from_dict(instance, data)
            return instance
    return None
