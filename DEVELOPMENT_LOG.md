# Sovereign Breach Development Log & Architectural Vision

This document tracks all modifications and the evolving vision for the Sovereign Breach (formerly Onlink-Clone) project, specifically for synchronization between different AI models.

## 1. Project Vision: "The Ultimate Hacking Simulation"
Our goal is to surpass both **Uplink** and **Onlink** by creating a more immersive, reactive, and high-fidelity experience, newly christened as **Sovereign Breach**.

### Ambiguous Goal Interpretation: "Better than Onlink and Uplink"
As an AI, I interpret "better" through three pillars:
1.  **Fidelity & Aesthetics**: Replicating the "lost" high-fidelity UI elements from original screenshots (blue gradients, hex memory offsets, scanline effects) using modern Web Technologies (Eel/HTML5/CSS3).
2.  **Simulation Depth**: Moving beyond simple timers. This includes "Passive Traces" (forensics), realistic hardware thermals, CPU scheduling, and a living economy.
3.  **User Experience (UX)**: Modernizing clunky 2001-era mechanics with web-native features like fluid window dragging, mouse-driven tool targeting, and high-performance canvas rendering.

---

## 2. Completed Modifications (Historical)

### The Great Architectural Pivot (Qt to Web)
- **Engine Decoupling**: Refactored `core/engine.py` to be 100% pure Python. Replaced `PySide6.QtCore.Signal` with a custom `EventEmitter` and `QTimer` with a background `threading.Thread` loop.
- **Eel Integration**: Implemented **Eel** as the bridge between the Python simulation and the UI.
- **High-Fidelity Web UI**: Abandoned `QMdiArea` in favor of a modern HTML/CSS/JS stack for pixel-perfect rendering.

### Standalone Module "Labs" (The Modular Milestone)
To ensure maximum fidelity and logic stability, we successfully built and perfected four core standalone prototypes:

1.  **World Map Lab (`map_prototype.py` / `web/map_prototype.html`)**: 
    - **WebGIS Integration**: Transitioned from custom HTML5 canvas to a high-fidelity **Leaflet.js** implementation.
    - **Geopolitical Borders**: Integrated `countries.geojson` for vector-based, interactive country borders (foundation for the Conflict module).
    - **Street-Level Fidelity**: Layered CartoDB Dark Matter tiles with brightness filters to provide micro-scale (street-level) detail for home IP and vehicle tracking.
    - **Map Integrity**: Enforced `noWrap` and strict coordinate bounds to prevent world repetition.
    - **Node Visibility**: Implemented "Saved IPs" logic where nodes only appear after discovery/saving.
2.  **World Simulation & Micro-Data Lab (`world_sim_prototype.py`)**:
    - **Logistics & PMC Engines**: Created specialized engines for ambient world activity (shipping routes, tactical interceptions).
    - **Moving Targets**: Implemented Aircraft and Ships as temporary, moving `Computer` nodes that interpolate coordinates across the map in real-time.
    - **Procedural People**: Every NPC now has a "Digital Footprint" (Employer, Job Role, SSN, Home IP, Bank Account).
    - **Personnel Databases**: Automatically generates `personnel_records.db` on company internal servers based on the procedural employee list.
    - **Event Ripples**: Integrated a "Hijack -> Finance Crash -> News Report" loop where world events dynamically affect stock prices and news feeds.
3.  **Hardware & VFS Lab (`hardware_prototype.py`)**:
    - **VFS Storage vs RAM**: Implemented the dual-storage loop where tools are stored on disk (Gq) but must be loaded into RAM slots to execute.
    - **CPU Scheduler**: Created a priority-based GHz allocation system (0.1x to 5.0x) that affects task progress.
    - **Engineering Depth**: Integrated individual CPU overclocking, real-time thermal damage (over 90°C), and PSU power draw limits.
    - **Physical VFS Map**: Created a block-based grid with fragmentation and live defragmentation mechanics.
4.  **Remote Interface Lab (`remote_prototype.py`)**:
    - **Interactive Hacking**: Developed the "Targeting" interaction (Select tool -> Click remote target).
    - **Security Stack**: Created real-time visualizers for Proxy, Firewall, and Monitor levels.
    - **Heist Logic**: Implemented the "Crack -> Unlock -> Copy -> Wipe Logs" sequence.
    - **Advanced Active Trace**: Integrated a real-time trace that is **invisible** unless the `Trace_Tracker` tool is active in RAM. 
    - **RAM Workflow**: Implemented a "Toggle-to-Load" system where tools must be active in execution space (indicated by green LEDs) before they can be applied to targets.
5.  **Store & Upgrade Lab (`store_prototype.py`)**:
    - **Modular Hardware**: Implemented purchasing logic for independent components (Cooling systems, PSUs).
    - **Software Versioning**: Handles tiered software licenses (v1.0 to v4.0) with varying sizes and performance impacts.
    - **Trade-in Economy**: Integrated a part-exchange system for Gateway upgrades (50% value retention).

### Unified OS Integration (The "Web OS" Milestone)
- **Primary Entry Point**: Launched `web_main.py` as the consolidated launcher.
- **Window Management**: Implemented a draggable, multi-window environment within `index.html`.
- **Integrated Logic**: Linked the standalone labs so that clicking a node on the Map background opens the Remote Terminal, and hardware purchases in the Store immediately affect the Task Engine speeds.

### Remote Interface Integration (The Controller Milestone)
- **API/Controller Pattern**: Introduced `core/remote_controller.py` to bridge the high-fidelity UI with the core `GameState`, `TaskEngine`, and `TraceEngine`.
- **Frontend Modularization**: Refactored the advanced remote interface logic into a dedicated `web/js/remote.js` module, ensuring clean separation from the main OS controller.
- **Live Hacking Loop**: Successfully integrated the "Prototype" hacking visuals (progress bars, block grids, log targeting) with the real simulation engines. The `TaskEngine` now drives all remote UI updates.

### News & Mission Engine Integration (The Reference Milestone)
- **Procedural News Port**: Ported the full multi-part template system from the Uplink reference code into `core/news_engine.py`. News stories are now procedurally built from `[Headline] + [Intro] + [Impact]` segments, making the world feel reactive to player and NPC actions.
- **Robust Mission Verification**: Updated `core/mission_engine.py` to use "Comparison Strings" (Uplink-style `completion_a` through `e`). Missions now require actual state-based verification (e.g., verifying a stolen file is in the player's VFS or that target data has been deleted) rather than simple ID-based completion.
- **Deep Reference Porting Strategy**: Formally adopted a strategy to analyze and adapt high-value logic from the original Uplink source code (and its modern Python forks) to our decoupled `GameState` architecture.

### Canonical World Generation & Node Interaction (The Simulation Milestone)
- **Server Porting**: Migrated the canonical Uplink node list (InterNIC, Databases, internal services) into our `world_generator.py`, effectively phasing out the hardcoded 4-node 'heist' mockup. Nodes now start mostly hidden, requiring player discovery.
- **Username-Based Login**: Evolved the simple ID/Password check into a comprehensive `accounts` dictionary mapping usernames to passwords (e.g., Admin, ReadWrite, Guest).
- **Node Interaction Depth**: Implemented Onlink-style automatic saved passwords (players don't re-crack known nodes) and conditional traces. Real-time tracing now properly respects the target server's Monitor active state, allowing players to turn off security from the admin panel for safe operations.

### High-Fidelity UI Paradigm Shift (The "Onlink Fidelity" Milestone)
- **Floating Tool Widgets**: Replaced the static sidebar with independent, draggable tool windows. Spawning a tool from the "Memory Banks" creates a dedicated widget for that task, allowing players to manage multiple concurrent hacks visually on the workspace.
- **Manual Targeting Interaction**: Implemented strict manual targeting. Players must arm their cursor with a specific tool widget before clicking on remote targets (Passwords, Files, Logs), matching Onlink's hardcore interaction model.
- **Memory Banks Redesign**: Overhauled the tool sidebar into a detailed "Memory Banks" view, displaying tool versioning, memory footprint (GQ), and load state (VFS vs RAM).
- **Real-time State Push**: Integrated `eel.expose(update_tasks)` and `update_clock` to handle direct backend pushes. This eliminates UI desyncs during hacking operations by allowing the `TaskEngine` to directly animate progress bars within the floating widgets.
- **InterNIC Discovery System**: Implemented a contextual "LINKS" view for directory servers. Players can now connect to InterNIC, browse a directory of public servers, and click to save new IPs to their map, restoring the core world-discovery loop.

### Advanced Hardware & VFS Integration (The "Engineering" Milestone)
- **Modular Hardware Engine**: Created a standalone `HardwareEngine` class to handle all physical constraints (Power, Heat, CPU Scheduling). The main engine now purely delegates to this module, preserving strict architectural separation.
- **CPU Core Scheduling**: Implemented multi-core CPU support with individual health and overclocking. Hacking tasks now draw speed from a dynamic CPU cycle pool; over-allocating priority or overclocking too hard leads to thermal degradation and PSU trips.
- **Component Thermals & Degradation**: Integrated a realistic heat model where power draw generates thermal load. Exceeding `max_heat` permanently damages component health, reducing their effective GHz output and eventually leading to "Melted" hardware failure.
- **Physical VFS Map System**: Migrated to a block-based physical VFS storage model. Every file (tool or data) now occupies specific block ranges. This lays the foundation for future fragmentation and manual file movement mechanics.
- **Hardware BIOS Dashboard**: Developed a dedicated "HARDWARE STATUS" terminal. This UI provides real-time gauges for Thermal Load, PSU Draw, RAM slot allocation, and interactive sliders for individual CPU core overclocking.

### Verification & Stabilization (The "Robustness" Milestone)
- **Comprehensive Test Suite**: Developed 33 automated unit tests using `pytest` covering core state logic, simulation engines, and advanced hardware mechanics.
- **World Generation Refinement**: Updated `world_generator.py` to populate the `WorldState` with 25+ NPC Agents and Company entities, ensuring the Stock Market and NPC Rankings systems function immediately on boot.
- **Mission Engine Stabilization**: Resolved critical `NameError` and `TypeError` bugs in the mission generation logic. Implemented a verification system for "Steal File" and "Delete Data" mission types.
- **Modular Interface Validation**: Verified that all simulation modules (Finance, PMC, Logistics, Hardware) can be independently tested and swapped, fulfilling the "basis for other projects" design mandate.

### Economy & Security Integration (The "Forensics" Milestone)
- **Cryptographic Bank Tracing**: Ported and upgraded the legacy Uplink bank logic. Created `core/bank_forensics.py` to generate secure SHA-256 hashes for all financial transactions.
- **Transaction Logs**: `BankAccount` entities now maintain an immutable `transaction_log` of `TransactionRecord` objects, allowing player/NPC investigators to trace funds across multiple bounce accounts.

### Advanced Onlink Hardware & Forensics (The "High-Fidelity" Milestone)
- **VFS Bus Speed (Storage OC)**: Implemented `storage_overclock` as a performance multiplier for I/O-bound tasks (File Copier, Log Deleter, Decrypter). CPU-bound tasks (Password Breakers) remain unaffected.
- **Hardware App High-Fidelity Data**:
  - `HardwareApp.init()` now returns a complete dataset: `vfs_map` (block-level mapping), `psu_capacity`, `storage_overclock`, and individual component health.
  - Unified backend to ensure the main OS interface matches standalone prototype detail.
- **Bank Transaction Logs & Forensics**:
  - `FinanceEngine` now includes full `transaction_log` (hashes, IPs, amounts) in account summaries.
  - Implemented `delete_transaction_log` Eel bridge, allowing players to "scrub" their financial trail.
- **High-Fidelity UI Overhaul**:
  - **Hardware App**: 2-column layout with visual **VFS Physical Sector Map**, **RAM Slot Grid**, and interactive Bus/CPU OC controls.
  - **Finance App**: Added **HISTORY** tab for viewing and deleting forensic transaction logs.
- **System Stability & Bug Fixes**:
  - Performed an **Atomic Rewrite of `os.js`**, eliminating massive variable collisions and duplicated legacy logic that caused "Frozen Time" and broken app menus.
  - Resolved `list_profiles` and profile loading reliability:
    - Fixed missing `password` field and outdated schema in the default **TESTER** profile.
    - Implemented **Resilient Loading Logic** in `web_main.py` with graceful error fallbacks for incompatible profile versions.
    - Added a manual **REFRESH** button and defensive "Loading..." placeholders to the login screen.
    - Switched to **Absolute Paths** for profile management to ensure consistency across different launch environments.
  - Implemented a race-condition guard in `os.js` that waits for the Eel bridge to be established before attempting to fetch the initial profile list.
  - Implemented type-aware recursive hydration in `core/persistence.py` using `get_type_hints` to resolve string annotations and accurately instantiate nested dataclasses.
  - Fixed "Frozen Time" bug by ensuring the `GameEngine` loop is correctly restarted after profile loads.
  - Fixed missing Eel bridges for Neuromancer level, suspicion, robbery timers, and passive traces.
  - Resolved regression in `test_audit_fixes.py` by improving mock data consistency (BankAccount, Computer, PassiveTrace).
  - Ensured task progress is updated for all task types (e.g., File Copier) during simulation ticks.

### Phase 8: Architectural Refinement (The "Backend-Driven UI" Milestone)
- **Dynamic App Registry**:
  - Moved the application registry (metadata, icons, window sizes) from JavaScript (`os.js`) to the **Python Backend** (`core/apps/__init__.py`).
  - Implemented **VFS-based Availability**: Applications now only appear in the Start Menu if the corresponding software (e.g., `map.exe`, `finance.exe`) is present in the player's gateway storage.
- **Backend View-Models**:
  - Transitioned HUD formatting logic (Clock strings, Currency formatting, Neuromancer level names) to the backend.
  - The `on_tick` loop now pushes a "Screen Packet" of pre-formatted strings, making the frontend a lightweight renderer and reducing the risk of UI-halting script errors.
- **Improved UI Resilience**:
  - Eliminated hardcoded registries in the frontend to reduce `SyntaxError` risks and variable collisions.
  - Refactored `openApp` and `buildStartMenu` to use dynamic RPC calls for app definitions.

### Phase 9: Consequences & Finality (The "Arrest" Milestone)
- **Standardized Arrest Logic**:
  - Implemented `trigger_arrest` in `core/event_scheduler.py`. Standardized the failure state for traces and heists.
  - **Consequences**: Immediate 50% deduction of balance, Uplink Rating reset to Level 1, and complete wipe of Gateway VFS.
- **Disavowed UI Overlay**:
  - Developed a high-fidelity **Arrest Screen** in `os.js` with terminal-style visual effects and an "Official Notice of Arrest."
  - Clicking "RESTART" now automatically deletes the compromised profile from disk and reloads the interface.
- **TDD Verification**: Added `tests/test_arrest.py` to confirm financial penalties and state resets are mathematically correct.

### Phase 10: Logistics & Corporate Ownership (The "Founder" Milestone)
- **Company Founding**:
  - Implemented `core/company_engine.py` allowing players to found their own Private Military or Logistics corporation (cost: 10,000c).
  - Added company ownership tracking to `PlayerState` and `Company` objects.
- **Enhanced Logistics Simulation**:
  - Transitioned to a **Persistent Vehicle** model. Ships and Aircraft are now owned assets that interpolation across the map in real-time.
  - Fulfilled contracts now grant bonuses to player-owned companies, creating a "Tycoon" style loop.
- **Company Manager App**: Integrated a backend-driven app for managing corporate assets and monitoring the fleet.
- **TDD Verification**: Added `tests/test_player_company.py` to verify founding costs and ownership registration.

---

## 3. Current & Ongoing Changes

### Recent Improvements (April 2026)
- **Screen-Based Server Interaction**: Complete rewrite of remote interface to use Uplink-style screen navigation. Connect to server → shows first screen → navigate between screens (Menu, File Server, Logs, BBS, Links, Console, Software/Hardware Sales, News, Rankings, Company Info). Each screen renders typed data with appropriate UI.
- **Connection Routing Fix**: Fixed map double-click connection — bounce chain now properly used when connecting from map nodes. Target IP excluded from bounce chain to prevent self-bouncing. Connection logs created on both target and proxy servers.
- **Time Scale Fix**: Speed 1 = 1 real second per tick (was 0.2s). SPEED_MAP: `{0: pause, 1: 1.0s normal, 3: 0.33s fast, 8: 0.1s mega fast}`.
- **Log Suspicion Escalation**: New `core/log_suspicion.py` module. Access logs escalate through 4 levels (Not Suspicious → Suspicious → Suspicious and Noticed → Under Investigation). Authentication logs escalate 2x faster. Connection logs escalate 0.5x slower. Deleted logs stop escalating. Hooked into game engine tick (every 50 ticks).
- **Gateway Nuke**: New `core/gateway_nuke.py` module. Emergency self-destruct destroys all VFS files, melts gateway, crashes all CPUs/RAM/storage, clears tasks, disconnects, and triggers game over. Last resort when about to be traced.
- **Neuromancer Rating**: New `core/neuromancer.py` module. 11 levels from Revolutionary (-100) to Paragon (+100). Actions modify rating: steal_file (+2), delete_data (+3), trace_user (-8), frame_user (-15), remove_computer (+5), get_caught (-10). Bounded -100 to +100.
- **Visual Improvements (April 2026)**:
  - **Dotted Connection Path**: The World Map now renders a dynamic, dotted orange polyline connecting nodes in the player's bounce chain.
  - **High-Fidelity Server Interface**: Overhauled the Remote app with a dual-pane layout. The left sidebar provides real-time security stack gauges and execution (RAM) tools, while the right panel hosts high-fidelity screen content (Login, Files, Logs, Console).
  - **Improved Map Interactivity**: Single-click toggles nodes in the bounce chain with immediate visual feedback on the map and route indicator.
- **BBS Screens on Servers**: Public servers now have BBS screens for mission browsing. Uplink Internal Services has BBS, Software Upgrades, Hardware Upgrades, News, Rankings, Company Info screens. InterNIC has Links and Company Info screens.
- **Store/Finance Connection Requirements**: Store app shows "Connect to Uplink Internal Services" prompt when not connected. Finance app shows "Connect to bank server" prompt when not connected.
- **Comprehensive Codebase Audit & Bug Fixes**: 370 tests (up from 348), with 25 new regression tests covering all audit findings:
    - **CRITICAL: PMCEngine None Guard** — `_on_hijack_success` now guards against `pmc=None` when companies list is empty.
    - **CRITICAL: Module-Level World Generation** — Removed `generate_world()` from `web_main.py` module scope; world now only generated on profile load/create.
    - **CRITICAL: Valid IP Generation** — `generate_ip()` now produces valid IPv4 octets (0-255) instead of 100-999.
    - **CRITICAL: Loan Interest Accrual** — Fixed divisor from 1000 to 100 so loans under $10k actually accrue interest.
    - **CRITICAL: Trace Engine Dead Code** — Removed unreachable `target.trace_speed` reference when `target` is `None`.
    - **HIGH: Logistics Company Types** — World generation now assigns random `CompanyType` to companies, guaranteeing at least one LOGISTICS company for shipment spawns.
    - **HIGH: LAN State Reset** — Added `reset_lan_states()` function for clearing stale LAN scan data between games.
    - **HIGH: Warning State Reset** — Fixed `reset_warnings()` to clear in-place instead of reassigning, ensuring imported references see the cleared set.
    - **HIGH: Mission Difficulty Scaling** — Changed divisor from 20 to 5 so missions on harder servers have meaningful difficulty values.
    - **HIGH: PMCEngine Reuse** — `hijack_shipment` now uses `engine.pmc` singleton instead of creating a new instance per call.
    - **HIGH: Software Type Detection** — Fixed `software_type is not None` (always True for IntEnum) to `software_type != SoftwareType.NONE` so data files don't appear as hacking tools.
    - **HIGH: Passive Trace Hop Interval** — Changed from 100 ticks to 20 ticks to match documented 20-second NPC trace speed at 1Hz.
    - **HIGH: Profile Double-Read** — `load_player_profile` now passes pre-parsed JSON data to `persistence.load_profile_from_data()` instead of reading the file twice.
    - **MEDIUM: Input Validation** — `save_profile()` now rejects empty player handles.
    - **MEDIUM: Gateway Upgrade CPU Count** — Gateway upgrades now preserve the original number of CPU cores instead of collapsing to a single core.
    - **MEDIUM: Late Imports** — Moved `mission_engine`, `log_suspicion`, `warning_events`, `bank_robbery` imports to top level of `engine.py`.
    - **MEDIUM: VFS Type Detection** — Changed truthiness check to explicit `SoftwareType.NONE` comparison in `web_main.py`.
    - **MEDIUM: Date Consistency** — Aligned `WORLD_START_DATE` month (Feb→Mar) with `GAME_START_DATE`.
    - **MEDIUM: Addon Catalog Defaults** — Added `size`, `type`, `version` keys to hardware addon entries in `SOFTWARE_CATALOG`.
    - **MEDIUM: Passive Trace Game Over** — Set `pt.is_active = False` before emitting game_over when passive trace reaches localhost.

### Comprehensive Codebase Audit & Thread Fix (April 2026)
- **Engine Thread Lifecycle** — `_tick()` now releases `self._lock` after bumping tick count, allowing `stop()` to interrupt. `stop()` skips join when called from tick thread (self-join deadlock guard).
- **Duplicate Function** — Removed duplicate `reset_lan_states()` in `core/lan_engine.py`.
- **App Registry Refresh** — `load_player_profile` now calls `reset_registry()` after loading state so apps are filtered by correct VFS.
- **Missing Renderers** — Added `renderMissions()` and `renderNews()` to `web/js/os.js` (were referenced but undefined).
- **Hardware Renderer** — Fixed `renderHardware()` to consume flat data structure from `HardwareApp.init()` instead of nested `{gateway, tasks}`.
- **Store Renderer** — Replaced stub `renderStore()` with full catalog display (software, gateways, cooling, PSU, addons).
- **Map Renderer** — Added Leaflet `invalidateSize()` call and container dimension enforcement for proper tile rendering.
- **Leaflet Container** — Added `invalidateSize()` with setTimeout for proper tile rendering after DOM layout.

### TDD Audit Fixes (April 2026) — 10 issues fixed, 382 tests
- **CRITICAL: Invalid IP Constants** — Fixed 8 hardcoded IPs in `core/constants.py` with octets >255 (e.g., `"458.615.48.651"` → `"10.0.0.1"`). Added regression test `test_ip_constants_are_valid`.
- **CRITICAL: Bad Neuromancer Import** — Fixed `adjust_neuromancer_rating` → `adjust_neuromancer` in `remote_controller.py`. Removed dead neuromancer call in `alter_record`.
- **CRITICAL: Missing Logger** — Added `import logging; log = logging.getLogger(__name__)` to `logistics_engine.py`.
- **CRITICAL: Undefined interactWithIP** — Added `interactWithIP(ip)` function to `web/js/os.js` (called by log/links screen click handlers).
- **HIGH: reset_warnings Never Called** — `new_game()` now calls `reset_warnings()` and `reset_lan_states()` to clear module-level state between sessions.
- **MEDIUM: NPC Investigation Rate** — Reduced crime scan chance from 5% to 0.5% per tick to prevent passive trace spam.
- **MEDIUM: renderTerminal Ignores Data** — Now uses `data.prompt` for terminal prompt instead of hardcoded `$`.
- **MEDIUM: Leftover Diagnostic Log** — Removed `log.info(f"GameTick loop EXITED...")` from `engine.py` `_loop`.
- **REGRESSION: viewRecord photoUrl** — Confirmed `photoUrl` IS properly defined in scope (false positive).

### Uplink Features Ported (Complete)
- **Log Suspicion Escalation** — 4-level system giving players a window to delete logs before being caught
- **Gateway Nuke** — Emergency self-destruct as last resort when about to be traced
- **Neuromancer Rating** — 11-level moral alignment track affecting available missions
- **Trace Speed Modifiers** — Access level affects how fast traces progress (0.1x to 1.6x)
- **Warning Events** — High suspicion logs trigger investigation warnings
- **Bank Robbery Event** — Illegal transfers start a 2-minute timer; delete logs or get caught

---

## 4. The "Better Than Both" Roadmap

### Phase 1: High-Fidelity Foundation (Complete)
- [x] Decouple backend from Qt.
- [x] Launch Web-based UI Engine.
- [x] Master Geography & Physical VFS rendering.

### High-Fidelity Integration & Interaction Logic (April 2026 - CURRENT)
- **Unified High-Fidelity Hardware**: Ported the standalone `UltimateHardwarePrototype` into the core `HardwareEngine`.
    - **CPU Core Scheduling**: Multi-core support with individual health, base speed, and overclocking.
    - **Resource-Based Task Progress**: Hacking speed now scales linearly with allocated GHz, modified by core health and global RAM overclock.
    - **Thermal & Power Dynamics**: Realistic heat generation and PSU draw limits; exceeding capacity trips breakers (pauses tasks), while overheating causes permanent component damage.
    - **VFS Block Mapping**: Automated physical block allocation for all files stored in the player's gateway.
- **Manual Bounce Route Building**: Restored the core Uplink/Onlink strategic loop.
    - **Map Interaction**: Players now click nodes on the World Map to manually construct a bounce chain (highlighted in orange).
    - **Dynamic Routing**: The Remote app now displays the active route and allows "Clear Chain" operations.
    - **Manual vs Auto**: Backend `connect()` logic now prioritizes the manually built `state.bounce.hops` over the previous auto-routing behavior.
- **System Self-Repair (The "Cat and Mouse" Loop)**:
    - **Security Recovery**: Bypassed Proxy/Firewall/Monitor systems now automatically re-enable after a period (~5 minutes real-time).
    - **Admin Password Rotation**: Compromised admin accounts now rotate their passwords periodically (~2.7 hours real-time), forcing players to maintain access.
    - **Compromise Tracking**: New `GameState.compromised_ips` dictionary tracks hack times for all servers.
- **Codebase Consolidation**: 
    - **Engine Refactoring**: Streamlined `core/engine.py` by delegating all hardware, thermal, and task performance logic to `HardwareEngine`.
    - **TDD Verification**: Added 10+ specialized tests for hardware performance, manual routing, and system recovery.

### Uplink Feature Porting (Phase 2): Advanced Economy (April 2026 - CURRENT)
- **Detailed Bank & Stock Logic**:
    - **Loan Interest Accrual**: Implemented `accrue_interest` in `FinanceEngine`. Unpaid loans now grow over time, increasing the total `loan_amount` on bank accounts.
    - **Event-Driven Stock Crashes**: Added `trigger_stock_crash` to `FinanceEngine`.
    - **Stock Manipulation**: Integrated stock crashes into `TaskEngine`.
        - **Mainframe Destruction**: Formatting/Deleting all files on a corporate Internal Server now causes a 50% stock price crash.
        - **Research Theft**: Copying sensitive data (`research_data.dat`, `corporate_secrets.dat`) causes a 20% stock price dip.
- **Procedural Records & Population**:
    - **NPC Civilians**: Added 50+ civilian NPCs to the world, each with full digital footprints.
    - **Record Banks**: Implemented government databases (Criminal, Academic, Social Security) that store and manage `Record` objects for all entities.
- **TDD Verification**: Added 15+ new tests for world generation, record persistence, and financial mechanics.

### Phase 11: Onlink-Style UI Restoration (The "Floating Windows" Milestone — April 2026)
- **Floating Window System Restored**: Reverted the broken fixed 3-panel layout back to a draggable, multi-window environment. Apps open as floating windows with z-index management, close buttons, and taskbar integration.
- **Nested Start Menu**: START button opens categorized popup menu (Network/System/Finance). Click any app to open as floating window. Click outside to close.
- **App Purchasing via .exe Files**: Apps now require `.exe` files in VFS to unlock. The store sells free `.exe` files (`map.exe`, `finance.exe`, `missions.exe`, `news.exe`, `rankings.exe`, `company.exe`, `logistics.exe`, `memory_banks.exe`) that add to VFS and unlock the corresponding app.
- **Memory Banks App**: New `memory_banks.exe` app shows all VFS files in a table layout organized by software type (Crackers, File Utilities, Log Tools, etc.). Each file shows name, version, size, loaded state. Actions: toggle load/unload into RAM, delete. Holds both hacking tools AND mission data (e.g., stolen `ufcdata557`).
- **Backend-Driven Server Screens**: All server screens (software/hardware sales, BBS, news, rankings) now generate HTML from Python (`ScreenHTMLBuilder` class in `remote_controller.py`). Frontend consumes pre-built HTML directly — single source of truth for UI logic. 38 TDD tests verify HTML output.
- **TDD Verification**: 416 tests pass. Added tests for `.exe` gating, Memory Banks app, HTML generation, Start Menu structure.

### Phase 12: Record Missions Implemented (The "Completion Criteria" Milestone — April 2026)
- **Record Mission Completion Verification**: Ported Uplink's 5-completion-string verification system. `verify_mission_completion()` now checks record fields using `completion_a` (database IP), `completion_b` (person name), `completion_c` (field name), `completion_d/e` (required substring, case-insensitive). Missions only complete when the actual record field contains the required value.
- **Record Mission Generation**: All 4 record mission types now generate with proper completion criteria:
  - **CHANGEACADEMIC** — Change University/IQ/Other fields (targets Academic Database at 10.0.1.1)
  - **CHANGECRIMINAL** — Add convictions like Robbery/Fraud/Hacking (targets Criminal Database at 10.0.2.1)
  - **CHANGESOCIAL** — Mark as Deceased, change Marital Status (targets Social Security Database at 10.0.3.1)
  - **CHANGEMEDICAL** — Change Health Status, add Allergies (targets Medical Database at 10.0.4.1)
- **TDD Verification**: Added 15 tests in `tests/test_record_missions.py` covering completion verification (unaltered/altered records, missing databases/records/fields, case-insensitive matching) and generation (all 4 types generated, completion criteria populated, target persons exist). Test count: 431 passed, 4 skipped.

### Bug Fix: Company Info Screen Crash (April 2026)
- **Company Info AttributeError**: Fixed `_render_company_info()` in `remote_controller.py` which crashed with `AttributeError: 'Computer' object has no attribute 'company_type'` when viewing Company Info screens on servers. The method was accessing `comp.company_type`, `comp.size`, `comp.stock_price`, and `comp.owner_id` — none of which exist on the `Computer` dataclass (it only has `company_name`). Fixed by looking up the company by name from `self.state.world.companies` and using the `Company` object's attributes instead.

### Phase 13: Record Alteration UI (The "Playable Missions" Milestone — April 2026)
- **Backend Screen Renderers**: Added 4 dedicated screen renderers in `remote_controller.py` (`_render_academic_screen`, `_render_criminal_screen`, `_render_social_security_screen`, `_render_medical_screen`). Each returns structured record data + pre-built HTML via `ScreenHTMLBuilder.build_record_screen_html()`.
- **HTML Generation**: `build_record_screen_html()` produces a two-panel layout: left panel has clickable record names with `onclick="viewRecord(idx, theme)"`, right panel is the detail view. Records are serialized into `window._recordData` for JS access.
- **Frontend UI**: Updated `viewRecord()` in `os.js` to use `window._recordData` instead of `el.dataset.records`. Each field now has an ALTER button that calls `alterField(recordName, fieldName, theme)` → prompts for new value → calls `eel.alter_record()` → refreshes screen.
- **TDD Verification**: Added 13 tests in `tests/test_record_ui.py` covering screen rendering, HTML structure, empty records, field alteration, non-existent computers/records, and end-to-end mission completion flow. Test count: 445 passed, 3 skipped.

### Phase 14: LogModifier / Framing System (The "Frame Others" Milestone — April 2026)
- **Log Modification Tool**: Added `Log_Modifier` (v1/v2) to the software catalog. When used on a server's logs, it changes the `from_ip` field to frame another agent. The `internal_logs` parallel backup array remains untouched, preserving forensic evidence.
- **Detection & Recovery**: Added `log_modified(index)` and `recover_log(index)` methods to `Computer`. Investigators with sufficient skill can detect tampering and recover original values from the internal backup.
- **UI**: Log screens now show a `MODIFY` button per log entry. Clicking it prompts for a new IP, calls `eel.modify_log()`, and refreshes the screen. Modified logs display a `[MODIFIED]` indicator in orange.
- **Suspicion**: Modifying logs increases the log's suspicion level, making it more likely to trigger an investigation.
- **TDD Verification**: Added 13 tests in `tests/test_log_modifier.py` covering modification, internal backup preservation, tampering detection, recovery, non-existent computers/indices, and HTML output. Test count: 455 passed, 5 skipped.

### Phase 15: Full Arrest Flow (The "Consequences" Milestone — April 2026)
- **Arrest Consequences**: `trigger_arrest()` now generates arrest news articles, reduces credit rating by 20, drifts neuromancer rating toward neutral, and tracks `arrest_count`. All magic numbers extracted to `constants.py` (`ARREST_BALANCE_SEIZURE_PERCENT`, `ARREST_JAIL_TICKS_MIN/MAX`, `ARREST_CREDIT_RATING_PENALTY`, etc.).
- **Disavowed Flow**: After `ARREST_MAX_COUNT_BEFORE_DISAVOWED` (3) arrests, player transitions to `PersonStatus.DISAVOWED` with a countdown timer. When countdown expires, profile is permanently deleted via `persistence.delete_profile()`.
- **Jail Time Processing**: Integrated `process_jail_time()` into engine tick loop. Non-disavowed players are released when jail ticks reach 0. Disavowed players enter countdown phase before profile deletion.
- **Arrest/Disavowed UI Overlays**: New `showArrestOverlay()` and `showDisavowedOverlay()` functions in `os.js` display high-fidelity terminal-style overlays with arrest details, jail sentence, balance seized, and arrest count. Disavowed overlay includes a "DELETE & RESTART" button.
- **Event System**: Added `on_game_over()` handler in `web_main.py` to properly dispatch arrest/disavowed/profile_deleted events to the frontend via `trigger_event()`.
- **TDD Verification**: Added 15 tests in `tests/test_arrest_flow.py` covering balance seizure, rating reset, credit rating penalty, VFS wipe, gateway reset, simulation pause, arrest count, news generation, jail tick decrement, jail release, disavowed threshold, disavow countdown, profile deletion, and result dict structure. Test count: 470 passed, 5 skipped.

### Phase 16: Bail/Buyout System (The "Second Chance" Milestone — April 2026)
- **Bail Calculation**: When arrested, bail is calculated based on jail time (`jail_ticks * BAIL_RATE_PER_TICK`), clamped between `BAIL_MINIMUM` (1000c) and `BAIL_MAXIMUM` (50000c). Bail amount is stored in `PlayerState.bail_amount` and displayed in the arrest overlay.
- **Pay Bail Function**: `pay_bail()` deducts bail amount from player balance and reduces jail time by 50% (`BAIL_JAIL_REDUCTION_PERCENT`). For disavowed players, bail reduces the disavow countdown by 50% instead. Bail can only be paid once per arrest cycle.
- **UI Integration**: Arrest overlay now shows bail amount with a "PAY BAIL" button. Clicking it calls `eel.pay_bail()`, shows success/failure notifications, and removes the overlay. Updated `trigger_event()` to handle bail payment flow.
- **Constants**: Added `BAIL_RATE_PER_TICK`, `BAIL_MINIMUM`, `BAIL_MAXIMUM`, `BAIL_JAIL_REDUCTION_PERCENT`, `BAIL_DISAVOW_REDUCTION_PERCENT` to `constants.py`.
- **TDD Verification**: Added 10 tests in `tests/test_bail.py` covering bail calculation, range clamping, jail time reduction, balance deduction, bail reset after payment, insufficient funds, not arrested, already paid, and disavowed countdown reduction. Test count: 478 passed, 7 skipped.

### Codebase Audit & Bug Fixes (April 2026)
- **CRITICAL: `pay_bail()` returned `bail_paid: 0`** — Fixed by capturing `paid_amount = p.bail_amount` before zeroing the field. The return dict now correctly reports the actual amount deducted.
- **CRITICAL: `on_game_over()` called `eel.trigger_event()` without checking existence** — Added `hasattr(eel, "trigger_event")` guard to prevent `AttributeError` if the frontend hasn't exposed the function.
- **CRITICAL: Bare `except: pass` in `on_game_over()`** — Replaced with proper `except Exception as e:` that logs the error with full traceback for debugging.
- **MEDIUM: Unnecessary `hasattr(comp, 'log_modified')` check** — Removed from `_render_log_screen()` since `Computer` always has this method.
- **MEDIUM: Misleading bail error message** — Changed `"No bail available"` to `"Bail already paid or not available"` for clarity.
- **Test updates**: Updated `test_pay_bail_already_paid` to match new error message. All 478 tests pass.

### Comprehensive Codebase Audit & TDD Fixes (April 2026 - Part 2)
- **Code Quality**: Performed a full-codebase `flake8` audit, fixing multiple unused imports, local variables, and bare except statements.
- **CRITICAL Bug Fixes**: Fixed `_complete_log_undeleter` undefined function reference in `core/task_engine.py` (which previously would have caused a runtime error when Log UnDeleter completed). Fixed a global `_warned_logs` scope issue in `core/warning_events.py`. Masked exception handling via bare `except` blocks in `web_main.py` and `core/remote_controller.py` were replaced with proper catching or removed.
- **TDD Test Suite Repair**: Discovered and resolved numerous minor logic errors in the test suite itself (such as unused variables, `== True` comparisons instead of `is True`, and invalid `is` comparisons).
- **Test Results**: Expanded and stabilized test count. The test suite now passes with **481 passing tests**, fully verifying the fix for the `Log_UnDeleter` logic and improved error resiliency.

### Phase 17: Interactive Tutorial & Codebase Refinement (April 2026)
- **Interactive Tutorial System**: Implemented a modular training module (`core/apps/tutorial.py`) that guides players through their first steps.
  - **Modular Verification**: Backend logic verifies player actions (connections, link browsing, bouncing, hacking) via `verify_step()` using the central `GameState`.
  - **VFS Gating**: Access is tied to `tutorial.exe` in the player's gateway storage, allowing it to be managed (deleted/reinstalled) like standard software.
  - **Dynamic App RPC**: Added `call_app_func` to `web_main.py`, enabling frontend components to invoke specialized backend methods for per-app logic beyond standard initialization.
- **Structural Cleanup**:
  - **Repository Organization**: Moved experimental scripts and mockups to `prototypes/` and deprecated Qt-based UI code to `legacy_qt/`, focusing the root directory on the active Web-based simulation.
  - **PEP 8 Compliance**: Resolved `E402` (imports not at top), `E701/E702` (multiple statements per line), and naming ambiguity (`E741`) across `engine.py`, `remote_controller.py`, and simulation engines.
- **TDD Verification**: Added `tests/test_tutorial.py` to verify step-by-step logic. Total test count reached **491 items**, with 484 passing and 7 skipped.

### Phase 18: Enhanced Logistics & PMC Mechanics (April 2026)
- **Advanced Transport Simulation**:
  - **Variable Speeds**: Aircraft (0.002), Ships (0.0005), and Trucks (0.001) now move at realistic relative speeds, modified by vehicle-specific multipliers.
  - **Persistent Vehicles**: Ships and Aircraft are now owned assets tracked via the `Vehicle` dataclass.
  - **Hacking Transports**: Implemented the ability to connect to moving transports and access their internal systems.
  - **Route Redirection**: Players can now hack into a vehicle's Logistics Control system to redirect it to a new destination, altering its interpolation path in real-time.
  - **Security Sabotage**: Added a "Sabotage External Security" hack that permanently reduces a shipment's security rating, making it significantly easier for PMC squads to intercept.
- **Improved PMC Engine**:
  - **Squad-Based Intercepts**: Refactored the hijacking logic to use `PMCSquad` combat ratings vs shipment security levels, replacing fixed percentage rolls with skill-based combat math.
  - **Combat Rating Dynamics**: Squads now have individual ratings for Combat, Stealth, and Tech.
- **TDD Verification**: Added 3 new tests in `tests/test_advanced.py` covering redirection, sabotage, and intercept math. Total test count reached **494 items**, with 489 passing and 5 skipped.

### Phase 19: Virtual OS (VDE) Improvements (April 2026)
- **Advanced Window Management**:
    - **Minimize/Restore**: Windows can now be minimized to the taskbar, with visual scaling/opacity transitions. Minimized apps are highlighted in the taskbar with reduced opacity.
    - **Smart Taskbar**: Clicking a taskbar button now intelligently cycles between Focus, Minimize, and Restore depending on the current window state.
    - **Edge Snapping**: Improved `startDrag` logic with a "Snap-to-Grid" feature that locks windows to screen edges (30px/36px offsets for HUD/Taskbar) when within 40px proximity.
- **Visual Fidelity & Aesthetics**:
    - **CRT Overlay**: Added a fixed full-screen overlay providing a retro radial gradient (curvature) and scanning line effect, significantly enhancing the "lost hacker terminal" aesthetic.
    - **High-Fidelity Transitions**: Integrated CSS transitions for window state changes, matching modern OS fluidness.
- **Desktop Interactivity**:
    - **Context Menu**: Implemented a Right-Click context menu on the desktop for quick access to Map, VFS Manager, and workspace cleanup tools.
    - **HUD Hotlinks**: Elements in the HUD are now interactive (Click Balance -> Finance, Click Clock -> News).
- **Notification & Audio Engines**:
    - **Notification Queue**: Developed a slide-in notification stack with severity-based styling (Info, Warning, Critical) and auto-dismissal.
    - **Sound Synthesis**: Implemented an oscillator-based UI Audio Engine for immersive feedback on clicks and system alerts.
- **Keyboard Accelerators**:
    - Global hotkeys: `Space` (Pause/Resume), `Esc` (Close top window), `Tab` (Cycle focus), `Alt+1-9` (Quick focus by taskbar index).
- **Visual VFS Browser**:
    - Overhauled `MemoryBanksApp` with a grid-based icon layout and active-state highlighting.
- **TDD Verification**: Added `tests/test_vde_logic.py` and `tests/test_os_extended.py` to verify the core window state transition and snapping logic. Total test count reached **502 items**, with 496 passing and 6 skipped.

### Phase 20: Protocol Restoration (The "High Fidelity" Milestone — April 2026)
- **OS & Bridge Healing**:
    - Resolved a critical "fragmentation" error in the Unified Core (`os.js`). Re-implemented missing logical nerves: `refreshApp`, `interactWithIP`, `applyTool`, and specialized remote rendering screens.
    - Re-exposed terminal and hacking functions in `web_main.py` (`execute_hack`, `console_command`) to restore remote interaction.
- **Modular Hardware Evolution**:
    - **Dismantled the "Bundle Trap"**: Refactored `GatewayState` to support independent CPU slots, Modem speed, and Memory (GQ) components.
    - **Resource Separation**: Formally separated **Active RAM** (tool capacity) from **VFS Storage** (file capacity).
    - **Incremental Upgrades**: Implemented `buy_cpu`, `buy_modem`, and `buy_memory` in `store_engine.py` using original Uplink hardware constants.
- **The Living Network (Internal AI)**:
    - Implemented a background `maintenance_tick` in `world_sim.py` that runs every 50 ticks.
    - **Security Self-Repair**: Bypassed or disabled security systems now have a chance to re-enable themselves over time.
    - **Log Expiration**: Implemented automated log purging; evidence older than 400 ticks is now automatically deleted by the host computer.
    - **Credential Rotation**: Admin passwords now rotate periodically if a breach is detected (player knows the password).
- **Security Protocol Depth**:
    - **Temporary Bypassing**: Implemented `is_bypassed` state on `SecuritySystem`. Bypasses are now fragile and reset immediately upon disconnection.
    - **Encrypter Integration**: Added the "Encrypter" (Cypher) security type (Type 4) and its corresponding breaker logic.
    - **Trace Sensitivity**: The `RemoteController` now respects bypassed monitors, preventing traces from starting on stealthy breaches.
- **Forensic Tool Expansion**:
    - Added **Log_UnDeleter** and higher versions of **Log_Modifier** and **Trace_Tracker** to the software catalog and task engine.
- **TDD Verification**: Added `tests/test_security_protocols.py`, `tests/test_hardware_modular.py`, and `tests/test_world_alive.py`. Total test count: **502 passed** (including resolved regressions).

- **Atmospheric Audio Restoration**:
    - **Native Tracker Playback**: Integrated `chiptune2.js` and `libopenmpt.js` to play original Uplink tracker files.
    - **Local Binary Hosting**: Localized all audio binaries (`libopenmpt.js`, `.mem`) to ensure worker thread stability.
    - **Extension-Agnostic Protocol**: Implemented a resilient `MusicManager` that automatically searches for the soundtrack using multiple extensions (.s3m, .xm, .mod, .it, .uni).
    - **Identity Manifestation**: Resolved a critical `ReferenceError: libopenmpt is not defined` by pre-defining global identities in `index.html`.
    - **Internal Context Wake-up**: Implemented an explicit resumption of the player's internal `AudioContext` during user gesture, pacifying browser autoplay security.
    - **State-Based Atmosphere**: Synced specific tracks (`serenity`, `mystique`, `symphonic`) to world states.

### Phase 21: UI Modernization & Personalization (The "Sharp Tactical" Milestone — April 2026)
- **Visual De-Aging**:
    - Removed the CRT curvature overlay and scanline effects to provide a high-precision, sharp tactical output.
    - Improved font rendering and color contrast for long-term operational comfort.
- **Elastic Workspace (Window Evolution)**:
    - **Tactical Resizing**: Implemented a global window resizing engine with bottom-right drag handles.
    - **Map Auto-Reflow**: Linked the World Map application to the resize events, ensuring the Leaflet canvas automatically invalidates and redraws its coordinates during scaling.
    - **Active Highlighting**: Developed an active window tracking system that visually elevates the focused window via a glowing cyan border and brightened title bar.
- **Desktop Personalization**:
    - **Wallpaper Engine**: Implemented `setBackground` logic to support custom tactical imagery or "Pure Void" (black) backgrounds.        
    - **Context Menu Integration**: Added a "WALLPAPER" section to the desktop right-click menu for real-time aesthetic rotation.
- **TDD Verification**: Total test count remains at **502 passed**. UI interaction logic verified through manual functional audit of window state transitions.

### Phase 22: High-Fidelity Economy & Structural Integrity (The "Audit" Milestone — April 21, 2026)
- **Environmental Mastery**:
    - Equipped the terminal with **Rust-powered tools** (`rg`, `ruff`, `tokei`, `uv`, `fzf`, `bat`, `jq`) via Winget.
    - Established the **GitHub Uplink**: Initialized the repository and synchronized the local "Forge" with the cloud.
- **The "Great Audit" (Structural Healing)**:
    - **Forensic Scan Repair**: Fixed a critical bug in `npc_engine` where investigators scanned internal logs instead of public suspicion levels, making forensics non-functional.
    - **Timer Leak Fix**: Repaired the bank robbery system to correctly purge timers once logs are wiped.
    - **Difficulty Sync**: Synchronized real-time tool progress (`Password_Breaker`) with actual server difficulty.
    - **Ruff Compliance**: Purged all ambiguous variables, redundant properties, and unused imports from the core engine.
- **Advanced Financial Forensics**:
    - **Hot Credits**: Implemented cryptographic "hot" signatures on stolen funds that increase global alert levels based on a weighted average `hot_ratio`.
    - **Money Laundering**: Created a laundering loop where connection bounces (5% per hop) and **Offshore Accounts** (50% per transfer) "clean" the credits.
    - **Ghost Logs**: Implemented permanent forensic signatures in bank internal backups that bypass standard log-deletion tools.
    - **Asset Repossession**: Banks now employ automated "Debt Collection" scripts to delete player software if loans default (overdue 5,000 ticks).
- **Frontend Resonance**:
    - Synchronized **8 missing Eel bridges** (Missions, News, Remote Security) previously shouting into a void.
    - Connected task progress/completion signals to real-time UI pushes.
- **Sentinel Protocol (Automated Testing)**:
    - Built an **AST-based Parity Test** (`tests/test_eel_bridges.py`) that automatically detects unexposed functions or broken bridges.
    - Verified all logic with `tests/test_finance_advanced.py` and `tests/test_laundering.py`.
    - **Total Test Count: 517 passed (100% Core Logic Pass Rate).**

---

## 5. Technical Stack- **Language**: Python 3.12+ (Backend), JavaScript (Frontend)
- **Communication**: Eel (Python <-> JS Bridge)
- **UI Framework**: HTML5 / CSS3 / Vanilla JS
- **Visuals**: CSS Gradients, Box-Shadow Glows, HTML5 Canvas (Vector Map)
