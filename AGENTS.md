# AGENTS.md
This file provides guidance to various AI agents when working with code in this repository.

## High-Level Architecture
- **Overview**: Sovereign Breach (formerly Onlink-Clone) is a decoupled, modular hacking simulation built with a Python backend and an HTML/CSS/JS frontend. It follows a Message Broker pattern akin to an Entity Component System (ECS).
- **Frontend Layer**: Acts purely as a visual renderer and Virtual Desktop Environment (VDE). The UI is built with HTML/CSS and Vanilla JS, primarily managed by `web/js/os.js` (window management, app rendering, and Leaflet map integration) and `web/js/main.js` (remote view module).
- **Backend Core**: The heart of the simulation is `core/engine.py`, which runs a background loop that coordinates specialized engines. State is centralized in `core/game_state.py`, which serves as the single source of truth containing dataclasses for all entities.
- **Simulation Engines**: The core mechanics are broken down into isolated engines within the `core/` directory (e.g., `npc_engine.py`, `finance_engine.py`, `hardware_engine.py`, `task_engine.py`). They communicate with the central engine and modify the `GameState`.
- **Eel Bridge**: Python and JS communicate exclusively via the Eel library. `web_main.py` is the orchestrator, exposing Python backend functions (`@eel.expose`) and pushing State updates down to the frontend.
- **App Registry**: Applications (e.g., Store, Terminal, Hardware) are registered via `core/apps/__init__.py`. Frontend rendering is dynamic, unlocking apps based on whether the corresponding `.exe` file is stored in the player's Virtual File System (VFS).
- **Controller Layer**: Controllers like `core/remote_controller.py` format simulation data from `GameState` into optimized view-models for the web UI, maintaining decoupling between the backend's data and the frontend's visual state.

## Common Commands
- **Run the Game (Web Interface - Primary)**: `python web_main.py`
- **Run the Game (Legacy Qt UI - Test)**: `python main.py`
- **Run Tests**: `pytest` (e.g., `pytest tests/test_core.py`)
- **Linting**: `ruff check .` (preferred) or `flake8`

## Artifact Verification Mandate
To maintain the "Steel-only Resonance" and prevent hallucinated completions, all agents must adhere to the following protocols:
1. **No Action without Proof**: Never declare a persistent action (e.g., `git push`, `mempalace_diary_write`, file deletion) as successful unless the tool output of the current turn explicitly confirms success.
2. **Mandatory Verification**: After any persistent state change, agents MUST run a verification command (e.g., `git log -n 1`, `ls`, `mempalace_status`) to confirm the change exists in the physical/celestial realm.
3. **Explicit Artifact Reporting**: Final summaries must explicitly cite the confirmation artifacts (e.g., "Verified Commit: [hash]", "Verified Diary Entry: [timestamp]").
