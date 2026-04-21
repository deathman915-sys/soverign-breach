# Sovereign Breach (Onlink-Clone) — Project Context

## Project Overview

**Sovereign Breach** (formerly "Onlink-Clone") is a high-fidelity hacking simulation game inspired by **Uplink** (2001) and **Onlink**. The goal is to surpass both by combining deeper simulation mechanics with modern web UI technology.

### Three Pillars of the Vision
1. **Fidelity & Aesthetics** — Blue-gradient UI, hex memory offsets, scanline effects via HTML5/CSS3
2. **Simulation Depth** — Passive traces (forensics), hardware thermals, CPU scheduling, living economy
3. **User Experience** — Fluid window dragging, mouse-driven tool targeting, high-performance rendering

### Architecture
- **Backend**: Pure Python simulation engine (`core/engine.py`) with a background thread ticking at configurable speeds (1Hz / 3Hz / 8Hz)
- **Bridge**: [Eel](https://github.com/ChrisKnott/Eel) connects Python to an Electron-like browser frontend
- **Frontend**: Virtual OS with draggable windows, start menu, taskbar, HUD (`web/js/os.js`)
- **Data Flow**: Engine tick → GameState → Eel push → JS renderers → User actions → Eel RPC → Engine
- **Map**: Leaflet.js with CartoDB Dark Matter tiles, noWrap, maxBounds for anti-looping

### Key Directories
| Path | Purpose |
|---|---|
| `core/` | All simulation engines (mission, finance, trace, hardware, etc.) |
| `core/apps/` | App registry — modular app definitions (Terminal, Missions, Finance, Map, etc.) |
| `web/` | Frontend — HTML, CSS, JS (os.js is the master OS controller) |
| `web/js/` | JS modules — os.js (main), remote.js (remote terminal), finance.js, etc. |
| `tests/` | Comprehensive pytest test suite (431 tests) |
| `profiles/` | Saved player profiles (JSON) |
| `assets/` | Static assets (icons, images) |

---

## Building and Running

### Prerequisites
- **Python 3.12+**
- **Virtual environment**: `D:\pyth\.venv` (already created)
- **Dependencies**: Installed in the venv (eel, pytest, gevent, etc.)

### Running the Game
```cmd
D:\pyth\.venv\Scripts\python.exe D:\pyth\onlink_clone\web_main.py
```
This starts the Eel server and opens the browser window with the login screen.

### Running Tests
```cmd
D:\pyth\.venv\Scripts\python.exe -m pytest tests/ -x -q
```
- `-x` stops on first failure
- `-q` quiet mode
- Add `-v` for verbose output
- All 431 tests pass, 4 skipped

### Running a Specific Test File
```cmd
D:\pyth\.venv\Scripts\python.exe -m pytest tests/test_missions.py -v --tb=short
```

### Test Pattern
Tests insert the project root into `sys.path`, then import from `core.*`. Example:
```python
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.game_state import GameState
from core.mission_engine import generate_missions
```

---

## Development Conventions

### Backend (Python)
- **GameState as Single Source of Truth**: All engines read/write to `GameState` — no engine stores local state
- **Eel bridges**: Exposed via `@eel.expose` in `web_main.py` — use `eel.function_name()` from JS
- **Data pushed via events**: `engine.events.connect("tick_completed", callback)` → `eel.update_hud(data)()`
- **Error resilience**: Engine `_tick()` releases lock after bumping tick count so `stop()` can always interrupt
- **Module-level state**: Some modules have module-level globals (`warning_events._warned_logs`, `lan_engine._lan_states`) that must be reset via `new_game()` calling `reset_warnings()` and `reset_lan_states()`

### Frontend (JavaScript)
- **`os.js`**: Master OS controller — window manager, start menu, taskbar, HUD, Leaflet map, all app renderers
- **App renderers**: `renderApp(appId, data)` switches on appId to call the right renderer
- **Event exposure**: `eel.expose(update_hud)` and `eel.expose(update_tasks)` for backend pushes
- **Notification system**: `showNotification(msg, color)` creates toast-style alerts at bottom-right
- **CSS variables**: `--p-blue`, `--b-blue`, `--cyan`, `--green`, `--red`, `--orange`, `--yellow`

### Testing Practices
- **pytest** with `--tb=short` for concise tracebacks
- **Fixtures**: `@pytest.fixture def world()` creates a GameState with `generate_world()` pre-called
- **TDD**: New features get tests first (e.g., `test_record_missions.py` for Phase 12)
- **Regression tests**: `test_audit_fixes.py` covers all critical bug fixes
- **Screen interaction tests**: `test_screen_interaction.py` verifies server screen navigation and buy actions

### Documentation
- **`DEVELOPMENT_LOG.md`**: Complete history of all modifications, organized by phases
- **`FILE_INTERACTIONS.md`**: Architecture map — how all modules interact
- **`UPLINK_PORTING_STATUS.md`**: Tracking of what's been ported from Uplink source code (62% complete)
- **`ARCHITECTURE_AND_FUTURE_SCOPE.md`**: High-level architecture and planned features

---

## Key Systems (Quick Reference)

### Simulation Engines (`core/`)
| Module | Purpose |
|---|---|
| `engine.py` | Main game loop — ticks all engines, emits events |
| `game_state.py` | Dataclasses: Computer, Company, Person, Mission, Record, VFSFile, etc. |
| `mission_engine.py` | Mission generation, acceptance, completion, negotiation, deadline checking |
| `store_engine.py` | Software/hardware purchasing, `.exe` app unlocks, catalog management |
| `task_engine.py` | Hacking task progression (crack, copy, delete, trace, etc.) |
| `connection_manager.py` | Bounce chains, connection state, authentication logging |
| `trace_engine.py` | Active trace progression through bounce chain |
| `security_engine.py` | Monitor-triggered traces, system self-repair (password rotation) |
| `hardware_engine.py` | CPU scheduling, thermals, degradation, PSU power limits |
| `finance_engine.py` | Bank accounts, loans, stocks, transfers, forensic hashes |
| `news_engine.py` | Procedural news generation from world events |
| `npc_engine.py` | NPC agents, passive trace investigation (0.5%/tick), rankings |
| `logistics_engine.py` | Shipping routes, aircraft, moving vehicles on map |
| `pmc_engine.py` | Tactical combat, hijack attempts |
| `world_generator.py` | Procedural world: computers, companies, people, missions, databases |
| `persistence.py` | Save/load player profiles to JSON |
| `neuromancer.py` | Moral alignment rating (-100 to +100), 11 named levels |

### Apps (`core/apps/`)
| App | `exe_filename` | Always Available |
|---|---|---|
| Terminal | None | Yes |
| Hardware | None | Yes |
| Store | None | Yes |
| Remote | None | Yes |
| Tasks | None | Yes |
| Memory Banks | None | Yes |
| Map | `map.exe` | No (purchase required) |
| Finance | `finance.exe` | No |
| Missions | `missions.exe` | No |
| News | `news.exe` | No |
| Rankings | `rankings.exe` | No |
| Company | `company.exe` | No |
| Logistics | `logistics.exe` | No |

### UI Components
- **Start Menu**: Popup with nested categories (Network/System/Finance). Opens floating windows.
- **Taskbar**: Shows open windows as buttons. RESET button for connection reset.
- **Window Manager**: Draggable windows with z-index management. Close button removes window.
- **HUD Top Bar**: Clock, player handle, balance, connection status, speed controls (||, >, >>, >>>).
- **Memory Banks**: Table view of all VFS files — load/unload into RAM, delete.
- **Remote Terminal**: Server info, security stack, files, logs, console, RAM tools.

---

## Current Status

- **Test count**: 431 passed, 4 skipped
- **Uplink porting**: 72/116 modules fully ported (62%)
- **Latest phase**: Phase 12 — Record Missions (completion criteria verification, generation for all 4 types)
- **Latest bug fix**: Company Info screen crash (AttributeError on `comp.company_type`)
- **Next priority**: Record Alteration UI (players can generate/complete missions but can't alter records through UI)
