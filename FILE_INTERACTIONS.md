# Sovereign Breach: File Interaction & Architecture Map

This document describes how the core Python modules and Web frontend files interact following the decoupled, App Registry architecture.

## 1. Core Data Flow (The Game Loop)

```
[Ticker] -> core/engine.py -> [Internal Engines] -> core/game_state.py
   ^                                                   |
   |                                                   v
[Frontend] <--------- Eel Bridge (JSON) <--------- [State Push]
```

1.  **`core/engine.py`**: The heart of the simulation. It runs a background thread that "ticks" several times per second. It coordinates all specialized engines and has error-resilient loop handling. **`_tick()` releases `self._lock` after bumping tick count so `stop()` can always interrupt the thread. `stop()` skips join when called from within the tick thread (self-join deadlock guard). `new_game()` calls `reset_warnings()` and `reset_lan_states()` to clear module-level state between sessions. Processes jail time each tick via `process_jail_time()`; handles disavowed countdown and profile deletion.**
2.  **`core/game_state.py`**: The "Single Source of Truth." It contains dataclasses for every entity in the world (Computers, Companies, People, Manifests). No engine stores local state; they all read/write to the `GameState` object. **PlayerState includes `arrest_count`, `disavow_countdown_ticks`, `bail_amount` for arrest/consequence tracking. Computer has `log_modified(index)` and `recover_log(index)` methods for forensic tampering detection. AccessLog includes `tick_created` for expiration tracking. GatewayState supports modular `cpus` list, `memory_gq` (RAM), and `storage_gq` (VFS).**
3.  **`core/world_generator.py`**: Ran once at game start. It populates `GameState` with the procedural world, generates initial missions, and utilizes `core/name_generator.py` and `core/geodata.py`.

## 2. Specialized Simulation Engines

These engines are called by `engine.py` during each tick:

-   **`core/npc_engine.py`**: Simulates government agencies scanning internal logs for crimes. **0.5% per-tick crime discovery rate** (~1 investigation per 200 ticks per server). If a crime is found, starts a PassiveTrace backwards.
-   **`core/logistics_engine.py`**: Generates and moves Aircraft, Ships, and Trucks. It creates temporary `Computer` nodes in `GameState` for vehicles in transit.
-   **`core/pmc_engine.py`**: Handles tactical combat math and interceptions. It emits events (e.g., `hijack_success`) via the `EventEmitter`.
-   **`core/finance_engine.py`**: Adjusts stock prices based on ambient volatility and world events (like a successful PMC hijack). Handles bank account creation, loans, and transfers.
-   **`core/bank_forensics.py`**: Works alongside the Finance Engine to generate cryptographic hashes for every transaction and provides tracking tools to trace money through multiple accounts.
-   **`core/news_engine.py`**: Generates procedural text articles when specific world events are triggered.
-   **`core/world_sim.py`**: Handles background world events (blackouts, stocks) and **Internal AI Maintenance**. Every 50 ticks, it checks for log expiration (400 ticks), re-enables disabled/bypassed security systems, and rotates compromised admin passwords.
-   **`core/task_engine.py`**: Manages progress for all active hacking tasks. Supports **Software Versioning** with performance multipliers. Includes **Bypass** vs **Disable** logic for security layers. Supports Log_UnDeleter and Log_Modifier (framing).
-   **`core/store_engine.py`**: Handles hardware/software purchases. Supports **Modular Hardware Upgrades** (individual CPUs, Modems, Memory) and addon purchases (Self Destruct, Motion Sensor). Syncs Gateway storage with VFS capacity.
-   **`core/trace_engine.py`**: Handles connection tracing. Implements **Access-Level Modifiers** (0.1x to 1.6x) based on account status (None, User, Admin, Bank Admin).
-   **`core/connection_manager.py`**: Manages connections and logs. **Disconnect() resets all temporary security bypasses world-wide**, matching original protocol fragility.
-   **`core/hardware_engine.py`**: A strictly modular engine that manages physical hardware constraints. It calculates power draw, heat generation, component degradation, and manages the CPU scheduler (priority-based GHZ allocation) for all active tasks. It is now the primary driver for task progression (via `process_tasks`).
-   **`core/security_engine.py`**: Handles connection security checks and **System Self-Repair**. Periodically rotates admin passwords and re-enables bypassed security systems for servers tracked in `state.compromised_ips`.
-   **`core/lan_engine.py`**: Handles LAN topology scanning, node probing, and spoofing.
-   **`core/event_scheduler.py`**: Schedules future events (subscription fees, mission generation, warnings, fines, arrests) and processes them on tick. **Phase 15+: Full arrest flow with balance seizure, rating reset, credit rating penalty, neuromancer drift, news generation, jail time processing, disavowed threshold (3 arrests → profile deletion countdown). Phase 16: Bail/Buyout system — `pay_bail()` reduces jail time or disavow countdown by 50% for a fee.**
-   **`core/log_suspicion.py`**: Escalates access log suspicion levels over time (Not Suspicious → Suspicious → Suspicious and Noticed → Under Investigation). Auth logs escalate 2x faster, connection logs 0.5x slower. Deleted logs stop escalating.
-   **`core/gateway_nuke.py`**: Emergency self-destruct for the player's gateway. Destroys all VFS files, melts hardware, and triggers game over.
-   **`core/neuromancer.py`**: Tracks moral alignment rating (-100 to +100) based on mission types. 11 named levels from Revolutionary to Paragon.
-   **`core/warning_events.py`**: Checks for HIGH suspicion logs and emits warning events. Each log only warns once.
-   **`core/bank_robbery.py`**: Tracks illegal money transfers with 120-tick countdown timers. Emits warnings at halfway point and game-over on expiry. Can be cleared by deleting relevant logs.

## 3. App Registry System (Modular Architecture)

Each application is a self-contained module that can be added/removed independently:

### Backend (`core/apps/`)
-   **`__init__.py`**: `AppRegistry` class with `register()`, `unregister()`, `get()`, `list_apps()`. `BaseApp` abstract class defines the contract: `app_id`, `name`, `category`, `icon`, `window_size`, `init()`.
-   **`terminal.py`**: Command-line interface app.
-   **`remote.py`**: Remote terminal for connecting to servers.
-   **`missions.py`**: Mission BBS with available/active missions.
-   **`finance.py`**: Banking, stock market, and loan management.
-   **`messages.py`**: Email/inbox system.
-   **`hardware.py`**: Gateway status, CPU/RAM/storage/thermal monitoring.
-   **`store.py`**: Software, hardware, components, and addons shop.
-   **`news.py`**: News server with procedural articles.
-   **`rankings.py`**: Agent leaderboard.
-   **`map.py`**: World map with node markers. Returns nodes with valid coordinates for Leaflet rendering.
-   **`memory_banks.py`**: VFS file browser showing all files organized by software type (Crackers, File Utilities, Log Tools, etc.). Shows load/unload state and supports delete. Holds both hacking tools and mission data.
-   **`tutorial.py`**: Interactive step-by-step training system verified by backend logic.

### Frontend (`web/js/`)
-   **`os.js`**: Core OS module. Window manager, start menu, taskbar, HUD, draggable windows, and all app renderers. **Includes `MusicManager` with an extension-agnostic loading loop (.s3m/.xm/.mod/.it/.uni) and state-based tracker music switching.**
-   **`libopenmpt.js` / `chiptune2.js`**: Binary libraries for real-time synthesis of tracker modules. Requires global identity mapping in `index.html`.

## 4. Frontend & UI Interaction (The Virtual OS)

The UI is built as a consolidated Web OS using HTML/CSS/JS, centered around a virtual desktop paradigm matching Uplink's aesthetic.

-   **`web_main.py`**: The primary entry point and Eel bridge orchestrator. It initializes the `GameEngine`, exposes unified API functions to the frontend, manages the lifecycle of the simulation thread, and provides the `open_app(app_id)` endpoint for the app registry.
-   **`web/index.html`**: The unified frontend. Hosts the start menu, taskbar, HUD top bar, windows container, and login screen. No desktop icons — apps launched via START menu.
-   **`web/js/os.js`**: The master OS controller. Handles app lifecycle, window management, start menu, taskbar, HUD updates, Leaflet map (as an app), and all app renderers.
-   **`web/js/main.js`**: The remote view module. Handles remote terminal rendering when connected to a server.

## 5. API & Controller Layer

To maintain decoupling, specialized controllers format simulation data for the UI:

-   **`core/remote_controller.py`**: Bridges the `GameState` (Computers, Logs, Files) to the Remote UI. It translates raw backend objects into the JSON structures required by the high-fidelity frontend and coordinates task initiation. Includes tool toggle tracking, comprehensive tool type detection, and `alter_record()` for modifying database server records.
-   **`core/apps/`**: Each app module provides its own `init()` method that returns the initial data snapshot for its frontend renderer.

## 6. Interaction Mechanisms

### Python -> JS (Push)
The Python engine periodically pushes the relevant slice of `GameState` to the frontend using `eel.update_state()` or specialized triggers:
-   `update_hud(data)`: Pushes a **pre-formatted View-Model packet** every tick. Contains `time_str`, `date_str`, `balance_str`, `neuromancer_str`, and `trace` progress. Frontend performs zero formatting.
-   `update_tasks(tasks)`: Triggers hardware and remote app refreshes when task progress changes.
-   `trigger_event(evt)`: Signals world events. **Event types: `arrest` (shows arrest overlay with bail option), `disavowed` (shows disavowed overlay with delete button), `profile_deleted` (reloads page), `released` (jail release notification), `disavow_countdown` (countdown warning), `game_over` (legacy alert).**

### JS -> Python (Unified Request)
The frontend calls Python functions exposed via `@eel.expose`:

**Network & Bounce Chain:**
-   `get_bounce_chain()`: Returns the active multi-hop IP list.
-   `toggle_bounce(ip)`: Adds/removes a node from the chain. Manual route overrides automatic paths.
-   `get_nodes(query)`: Returns nodes filtered by discovery and **optional search query**.
-   `save_ip(ip)`: Adds a discovered IP from the map or logs to the player's `known_ips` list.
-   `attempt_connect(ip)`: Initiates a multi-hop connection using the active bounce chain.

**App System & Hardware:**
-   `list_apps(category)`: Returns a list of available applications based on software installed in VFS (e.g. `map.exe`). Includes icons and window sizes.
-   `open_app(app_id)`: Opens an app and returns its initial data snapshot.
-   `call_app_func(app_id, func_name, *args)`: Invokes specialized backend methods for a specific application (e.g. tutorial step verification).
-   `redirect_transport(ip, manifest_id, new_dest)`: Redirects a transport to a new city.
-   `sabotage_transport(ip, manifest_id)`: Permanently reduces a shipment's security level.
-   `get_hardware_upgrades(category)`: Returns a list of individual CPU, Modem, or Memory upgrades.
-   `buy_cpu(slot, model)`, `buy_modem(model)`, `buy_memory(model)`: Performs modular hardware upgrades.

**Core Actions:**
-   `toggle_tool(id)`: Loads/unloads a tool from VFS (disk) into RAM. Directly modifies `VFSFile.is_active`.
-   `execute_hack(ip, tool, target_type, target_id)`: Initiates a task in the `TaskEngine` via the `RemoteController`.
-   `stop_task(task_id)`: Manually stops a running task.
-   `alter_record(ip, name, field, value)`: Modifies a specific forensic record on a database server.
-   `modify_log(ip, log_index, new_from_ip)`: Modifies a log entry's from_ip to frame another agent. Internal backup log preserved for forensic recovery.
-   `pay_bail()`: Pays bail to reduce jail time or disavow countdown by 50%. Returns success/failure with details.
-   `found_company(name, type_idx)`: Spends 10,000c to establish a player-owned PMC or Logistics firm.

**Missions:**
-   `get_missions()`: Returns available (unaccepted) missions the player can take.
-   `get_active_missions()`: Returns accepted-but-incomplete missions with time remaining.
-   `accept_mission(mission_id)`: Accepts a mission and sends confirmation email.
-   `complete_mission(mission_id)`: Verifies mission objectives and pays out on success.
-   `negotiate_mission(mission_id, increase_percentage)`: Attempts to increase mission payment via employer negotiation.

**Finance:**
-   `get_finance_state()`: Returns accounts, loans, holdings, stocks, and credit rating.
-   `open_bank_account(bank_ip)`: Opens a new bank account.
-   `transfer_money(from_id, to_id, amount)`: Transfers funds between accounts.
-   `take_loan(acct_id, amount)`: Takes out a loan.
-   `repay_loan(loan_id)`: Repays a loan in full.
-   `buy_stock(company_name, shares)`: Buys shares in a company.
-   `sell_stock(company_name, shares)`: Sells shares in a company.
-   `delete_transaction_log(tx_hash)`: Scrubs a forensic transaction log from the bank records.

**Messages:**
-   `get_messages()`: Returns all messages with read/unread status.
-   `mark_message_read(message_id)`: Marks a message as read.

**Store:**
-   `get_catalogs()`: Returns all store catalogs (software, gateways, cooling, PSU).
-   `buy_software(name, version)`: Purchases software.
-   `buy_gateway(name)`: Purchases a gateway.
-   `buy_cooling(name)`: Purchases a cooling system.
-   `buy_psu(name)`: Purchases a PSU.
-   `buy_addon(name)`: Purchases a hardware addon.
-   `get_addon_catalog()`: Returns available addons.

**Hardware:**
-   `get_hardware_status()`: Streams a detailed snapshot of the Gateway's physical state.
-   `set_cpu_overclock(cpu_id, multiplier)`: Tunes individual processor clock speeds.
-   `set_ram_overclock(multiplier)`: Tunes RAM clock speed.
-   `set_storage_overclock(multiplier)`: Tunes VFS Bus (storage) clock speed. Affects I/O task performance.
-   `defrag_vfs()`: Defragments VFS storage.
-   `delete_vfs_file(filename)`: Deletes a file from VFS.

**Rankings & News:**
-   `get_rankings()`: Returns agent rankings leaderboard.
-   `get_news()`: Returns recent news articles.

**Logistics & LAN:**
-   `get_manifests()`: Returns in-transit logistics manifests.
-   `hijack_shipment(manifest_id)`: Attempts to hijack a shipment.
-   `start_lan_scan(target_ip)`: Begins LAN topology scan.
-   `get_lan_state(target_ip)`: Returns LAN scan state.
-   `probe_lan_node(target_ip, node_id)`: Probes a LAN node.
-   `spoof_lan_node(target_ip, node_id)`: Compromises a LAN node.

**Network:**
-   `get_shortest_path(src_ip, dst_ip)`: Returns optimal bounce route via Dijkstra.

### UI Component Interactions
-   **Start Menu**: START button in taskbar opens categorized menu (Network/System/Finance). Click any app to open as floating window. Closes when clicking outside.
-   **Taskbar**: Shows open windows as buttons. Click to focus, minimize, or restore. Active window highlighted. RESET button for connection reset.
-   **Window Manager**: Draggable windows with z-index management, minimize/restore, and edge-snapping (Snap-to-Grid). Close button removes window and taskbar button.
-   **App Purchasing**: Apps require `.exe` files in VFS. Free `.exe` files (`map.exe`, `finance.exe`, etc.) are sold in the Store under "Software" tab. Buying adds `.exe` to VFS, which unlocks the app in the Start Menu.
-   **HUD Top Bar**: Shows clock, player handle, balance, connection status, and speed controls. Click balance for Finance app, clock for News app.
-   **Desktop**: Right-click for context menu with quick app shortcuts and cleanup tools. Retro CRT curvature and scanline overlay enhance visual fidelity.
-   **Map App**: Leaflet.js with dark tiles, noWrap, maxBounds to prevent world looping. **Single-click selects node + toggles bounce chain** (orange dotted line, markers highlight). **Double-click connects to node** and opens Remote app. Sidebar shows selected node info with **CONNECT** and **CLEAR CHAIN** buttons. Integrated search sidebar and node focus list.
-   **Remote Terminal**: Shows server info, security stack, files, logs, console, and local RAM tools. **New: Real-time security/trace progress bars, `interactWithIP(ip)` routes clicked log/link IPs to Remote app for connection.**
-   **Mission BBS**: Tabbed interface (Available/Active). Available tab shows missions with Accept/Negotiate buttons. Active tab shows accepted missions with time remaining and Complete button.
-   **Finance**: Tabbed interface (Banking/History/Stocks/Loans). Banking shows accounts and transfers. History shows forensic transaction logs with "DEL" (scrub) option. Stocks shows portfolio and market. Loans shows outstanding debts and credit limit.
-   **Company Manager**: Dashboard for player-owned corporations. Allows founding a firm, tracking fleet vehicles (Ships/Aircraft), and monitoring active logistical contracts.
-   **Arrest Screen**: Full-screen modal triggered on `game_over`. High-fidelity terminal-style "OFFICIAL NOTICE OF ARREST" showing reason, jail sentence, balance seized, arrest count, and bail amount with PAY BAIL button. **Disavowed variant**: "DISAVOWED" overlay with "DELETE & RESTART" button after 3+ arrests. Bail payment reduces jail time or disavow countdown by 50%.
-   **Messages**: Inbox with read/unread status. Click to read full message.
-   **Hardware**: High-fidelity dashboard. Real-time gauges for power/thermal, a visual **VFS Physical Sector Map**, a **RAM Slot Grid**, and interactive Bus/CPU OC controls.
-   **Memory Banks**: Table view of all VFS files organized by type (Crackers, File Utilities, Log Tools, Data Files, etc.). Each row shows name, version, size, loaded state. Click ON/OFF to load/unload into RAM. Click X to delete. Holds both hacking tools and mission data (e.g., stolen files).
-   **Store**: Tabbed interface (Software/Gateways/Components). Components tab includes cooling, PSU, and addons. Software tab includes free `.exe` files that unlock apps.
-   **News**: Procedurally generated articles with headlines, dates, and body text.
-   **Rankings**: Agent leaderboard sorted by rating with player highlighted.
-   **Terminal**: Command-line interface with help, status, connect, disconnect, ls, and app launch commands. **Uses `data.prompt` from backend for dynamic prompt display (e.g., `handle@localhost:~$`).**
-   **Public Access Servers**: Servers with `NodeType.PUBLIC_SERVER` auto-unlock on connection — no password required. Controlled by `is_public` flag in `world_generator.py`.
-   **Procedural Server Placement**: Corporate servers placed in 6 realistic tech hub regions (North America, Europe, East Asia, South America, Australia, South Africa) instead of random global coordinates.

### Event Ripple Effect
When a `pmc_engine` action succeeds, it emits an internal Python event. `engine.py` catches this event and:
1.  Calls `finance_engine` to drop a stock price.
2.  Calls `news_engine` to write an article.
3.  The next `GameState` push to the UI includes the new news and stock data.

## 7. Testing & Verification Infrastructure

To ensure modularity and prevent regressions as the simulation scales, the project uses a multi-layered testing suite in the `tests/` directory (**480 tests**):

-   **`tests/test_core.py`**: Validates the `GameState` mediator, `NetworkGraph` pathfinding, and `VirtualFileSystem` block operations.
-   **`tests/test_engines.py`**: Smoke tests for the main simulation loop, including the Task, Trace, Security engines, and mission negotiation.
-   **`tests/test_advanced.py`**: Deep verification of the `HardwareEngine` (thermals/overclocking), `PMCEngine` (intercepts), and `LogisticsEngine` (manifests).
-   **`tests/test_gameplay.py`**: End-to-end integration tests simulating full game sessions.
-   **`tests/test_missions.py`**: Comprehensive mission tests (generation, acceptance, completion, negotiation, deadlines, verification).
-   **`tests/test_record_missions.py`**: Record mission generation and completion verification for all 4 types (academic, criminal, social, medical).
-   **`tests/test_record_ui.py`**: Record screen rendering, HTML structure, field alteration, end-to-end mission completion flow.
-   **`tests/test_log_modifier.py`**: Log modification (framing), internal backup preservation, tampering detection, recovery.
-   **`tests/test_arrest.py`**: Basic arrest trigger and jail time progression.
-   **`tests/test_arrest_flow.py`**: Full arrest consequences: balance seizure, rating reset, credit rating penalty, VFS wipe, gateway reset, news generation, disavowed flow, profile deletion.
-   **`tests/test_bail.py`**: Bail calculation, payment, jail time reduction, disavowed countdown reduction, insufficient funds.
-   **`tests/test_connection.py`**: Connection, disconnection, password auth, public servers, log creation.
-   **`tests/test_console.py`**: All console commands (cd, ls, delete, shutdown), error handling.
-   **`tests/test_events.py`**: Event scheduling, subscriptions, fines, mission generation events.
-   **`tests/test_hardware.py`**: Thermal limits, component degradation, CPU scheduling, PSU capacity, health bounds.
-   **`tests/test_store.py`**: Software and hardware purchasing, balance deduction, VFS updates.
-   **`tests/test_world_gen.py`**: World generation, public server flags, mission generation on boot, server structure.
-   **`tests/test_unwired.py`**: TDD tests for previously unwired features (PSU routing, tool toggle, VFS management, messages, finance, rankings, logistics, LAN, task stop, game state completeness, store addons).
-   **`tests/test_apps.py`**: App registry tests (register, unregister, list, built-in apps, autoload, backend init, .exe gating).
-   **`tests/test_login.py`**: Login screen, player profile, player defaults.
-   **`tests/test_bank_forensics.py`**: Transaction hash generation and tracing.
-   **`tests/test_audit_fixes.py`**: Regression tests for TDD audit findings (IP constants validity, neuromancer import, alter_record crash, mission difficulty, warning state reset, profile double-read, passive trace hop interval).
-   **`tests/test_records.py`**: Computer record bank storage and persistence hydration.
-   **`tests/test_high_impact.py`**: Gateway nuke, neuromancer HUD, bounce chain UI, task management app, overclocking UI.
-   **`tests/test_self_repair.py`**: Admin password rotation and security system re-enabling.
-   **`tests/test_screen_interaction.py`**: Server screen navigation, BBS, links, buy actions requiring connection.
-   **`tests/test_screen_html_generation.py`**: Python-generated HTML for all server screens (BBS, logs, file server, software/hardware sales, news, rankings).
-   **`tests/test_internal_logs.py`**: Internal forensic log creation and log deleter interaction.
-   **`tests/test_time_acceleration.py`**: Speed multiplier effects on time progression and traces.
-   **`tests/test_trace_speed.py`**: Trace speed modifiers based on access level.
-   **`tests/test_ui_fixes.py`**: Map app rendering, noWrap/maxBounds, no desktop icons.
-   **`tests/test_vfs_bus.py`**: Storage overclock effects on I/O vs CPU tasks.
-   **`tests/test_vfs_mapping.py`**: VFS physical block mapping in hardware app.
-   **`tests/test_warning_bank_robbery.py`**: Suspicion warnings and illegal transfer timers.
-   **`tests/test_player_company.py`**: Company founding costs and ownership.
-   **`tests/test_gateway_nuke_neuromancer.py`**: Gateway self-destruct and neuromancer rating integration.
-   **`tests/test_dynamic_forensics.py`**: Passive trace forensic investigation flow with dynamic player IPs.
-   **`tests/test_security_protocols.py`**: Security bypassing, Encrypter logic, and disconnection resets.
-   **`tests/test_hardware_modular.py`**: Modular CPU slots, Modem upgrades, and RAM/Storage separation.
-   **`tests/test_world_alive.py`**: Computer AI maintenance (log expiry, security repair, password rotation).

*(Current Test Count: 502 Passed)*
