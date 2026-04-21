# Uplink Source Code Porting Status

This document tracks what has been ported from the original Uplink C++ source code (D:\pyth\uplink-reference\uplink-source-code-master) into Sovereign Breach, and what remains to be done.

---

## 1. World Generators (`uplink/src/world/generator/`)

| Uplink Source File | Ported? | SB Equivalent | Status Notes |
|---|---|---|---|
| `worldgenerator.cpp` | ✅ | `core/world_generator.py` | Ported — generates computers, companies, people, initial missions, InterNIC, public servers |
| `missiongenerator.cpp` | ✅ | `core/mission_engine.py` | Ported — generates missions with completion_a through completion_e, negotiation, deadlines, verification. **Phase 12 (April 2026):** All 4 record mission types (CHANGEACADEMIC, CHANGECRIMINAL, CHANGESOCIAL, CHANGEMEDICAL) now generate with proper completion criteria and verify correctly against actual record field changes. |
| `newsgenerator.cpp` | ✅ | `core/news_engine.py` | Ported — multi-part templates (headline+body), event-driven articles, ambient news, stock crash detection |
| `plotgenerator.cpp` | ⚠️ | `core/plot_engine.py` | Partially ported — Revelation Act 1 trigger exists; Faith and ARC storylines are stubs; no act progression logic |
| `consequencegenerator.cpp` | ⚠️ | — | Partially ported — CaughtHacking stub exists; needs full criminal record and arrest scheduling logic |
| `langenerator.cpp` | ✅ | `core/lan_engine.py` | Ported — LAN topology generation, node probing, spoofing, force locks |
| `namegenerator.cpp` | ✅ | `core/name_generator.py` | Ported — generates person names and company names |
| `recordgenerator.cpp` | ❌ | — | Not ported — generates academic/criminal/medical/social records on servers (CRITICAL FOR MISSIONS) |
| `numbergenerator.cpp` | ❌ | — | Not ported — generates phone numbers, account numbers, SSNs |
| `demoplotgenerator.cpp` | ❌ | — | Not needed — demo-specific plot |

---

## 2. Event Scheduler (`uplink/src/world/scheduler/`)

| Uplink Source File | Ported? | SB Equivalent | Status Notes |
|---|---|---|---|
| `eventscheduler.cpp` | ✅ | `core/event_scheduler.py` | Ported — schedules future events, processes them on tick |
| `arrestevent.cpp` | ✅ | `core/event_scheduler.py` | Ported — full arrest flow with balance seizure (50%), rating reset, credit rating penalty, neuromancer drift, news generation, jail time, disavowed threshold (3 arrests → profile deletion countdown). **Bail/Buyout System**: Players can pay bail (1000-50000c) to reduce jail time or disavow countdown by 50%. |
| `warningevent.cpp` | ⚠️ | `core/event_scheduler.py` | Partially ported — warnings exist but no escalating warning system |
| `bankrobberyevent.cpp` | ❌ | — | Not ported — NPC bank heists that affect player |
| `attemptmissionevent.cpp` | ✅ | `core/npc_engine.py` | Ported — NPCs attempt and complete missions |
| `runplotsceneevent.cpp` | ❌ | — | Not ported — plot scene execution for story arcs |
| `seizegatewayevent.cpp` | ❌ | — | Not ported — authorities seize player gateway |
| `changegatewayevent.cpp` | ❌ | — | Not ported — NPC gateway changes |
| `installhardwareevent.cpp` | ❌ | — | Not ported — NPC hardware upgrades |
| `notificationevent.cpp` | ⚠️ | `core/game_state.py` | Partially ported — messages/notifications exist |
| `shotbyfedsevent.cpp` | ❌ | — | Not ported — Onlink-specific fed encounter |
| `uplinkevent.cpp` | ✅ | `core/engine.py` | Ported — base event class pattern |

---

## 3. Computer Systems (`uplink/src/world/computer/`)

| Uplink Source File | Ported? | SB Equivalent | Status Notes |
|---|---|---|---|
| `computer.cpp` | ✅ | `core/game_state.py` (Computer) | Ported — computers with screens, files, logs, security, accounts |
| `securitysystem.cpp` | ✅ | `core/game_state.py` (SecuritySystem) | Ported — proxy, firewall, monitor types |
| `securitymonitor.cpp` | ✅ | `core/security_engine.py` | Ported — monitor triggers active traces |
| `bankcomputer.cpp` | ⚠️ | `core/finance_engine.py` + `core/bank_forensics.py` | Partially ported — accounts, transfers, loans, stocks work; forensic hash tracing exists but no multi-stage bank heist logic |
| `bankaccount.cpp` | ✅ | `core/game_state.py` (BankAccount) | Ported — transaction logs with SHA-256 hashes |
| `logbank.cpp` | ⚠️ | `core/game_state.py` (AccessLog) | Partially ported — basic logs exist but missing `internallogs` backup feature for deep forensics |
| `databank.cpp` | ❌ | — | Not ported — record storage (academic, criminal, medical, social security) |
| `recordbank.cpp` | ❌ | — | Not ported — record manipulation for missions |
| `lancomputer.cpp` | ✅ | `core/lan_engine.py` | Ported — LAN topology and operations |
| `lanmonitor.cpp` | ⚠️ | — | Not ported — LAN-specific monitoring |
| `gateway.cpp` | ✅ | `core/game_state.py` (GatewayState) | Ported — player gateway with CPU, RAM, storage |
| `gatewaydef.cpp` | ✅ | `core/store_engine.py` | Ported — gateway definitions for store |

---

## 4. Hacking Tools / Task Manager (`uplink/src/interface/taskmanager/`)

| Uplink Source File | Ported? | SB Equivalent | Status Notes |
|---|---|---|---|
| `passwordbreaker.cpp` | ✅ | `core/task_engine.py` | Ported — character-by-character reveal |
| `dictionaryhacker.cpp` | ✅ | `core/task_engine.py` | Ported — 70% success chance |
| `filecopier.cpp` | ✅ | `core/task_engine.py` | Ported — copies to VFS |
| `filedeleter.cpp` | ✅ | `core/task_engine.py` | Ported — removes from target |
| `logdeleter.cpp` | ✅ | `core/task_engine.py` | Ported — v1-v4 deletion levels |
| `logundeleter.cpp` | ✅ | `core/task_engine.py` | Ported — restores deleted logs |
| `logmodifier.cpp` | ✅ | `core/task_engine.py` + `core/remote_controller.py` | Ported — modifies log `from_ip` to frame agents. `internal_logs` backup preserved for forensic recovery. `log_modified()` detects tampering, `recover_log()` restores originals. UI has MODIFY button per log entry with `[MODIFIED]` indicator. |
| `firewalldisable.cpp` | ✅ | `core/task_engine.py` | Ported — disables firewall |
| `proxydisable.cpp` | ✅ | `core/task_engine.py` | Ported — disables proxy |
| `securitybypass.cpp` | ✅ | `core/task_engine.py` | Ported — bypass tools for firewall/proxy/monitor |
| `tracetracker.cpp` | ✅ | `core/task_engine.py` | Ported — shows active trace progress |
| `decrypter.cpp` | ✅ | `core/task_engine.py` | Ported |
| `decypher.cpp` | ❌ | — | Not ported — decypher tool (different from decrypter) |
| `defrag.cpp` | ✅ | `core/task_engine.py` | Ported — VFS defragmentation |
| `ipprobe.cpp` | ✅ | `core/task_engine.py` | Ported |
| `iplookup.cpp` | ✅ | `core/task_engine.py` | Ported |
| `voiceanalyser.cpp` | ❌ | — | Not ported — voice recording analysis for LAN auth |
| `lanscan.cpp` | ✅ | `core/lan_engine.py` | Ported |
| `lanprobe.cpp` | ✅ | `core/lan_engine.py` | Ported |
| `lanspoof.cpp` | ✅ | `core/lan_engine.py` | Ported |
| `lanforce.cpp` | ❌ | — | Not ported — force LAN lock |
| `motionsensor.cpp` | ✅ | `core/store_engine.py` | Ported — addon purchase |
| `gatewaynuke.cpp` | ❌ | — | Not ported — destroys target gateway |
| `revelation.cpp` | ❌ | — | Not ported — Revelation virus tool |
| `revelationtracker.cpp` | ❌ | — | Not ported — tracks virus spread |
| `faith.cpp` | ❌ | — | Not ported — Faith storyline tool |
| `tutorial.cpp` | ✅ | `core/apps/tutorial.py` | Ported — interactive step-by-step training system verified by backend logic. |
| `uplinktask.cpp` | ✅ | `core/task_engine.py` | Ported — base task class |
| `uplinkagentlist.cpp` | ✅ | `core/npc_engine.py` | Ported — rankings leaderboard |
| `taskmanager.cpp` | ✅ | `core/task_engine.py` | Ported — task orchestration |

---

## 5. Remote Interface Screens (`uplink/src/interface/remoteinterface/`)

| Uplink Screen | Ported? | SB Equivalent | Status Notes |
|---|---|---|---|
| `bbsscreen` | ✅ | `core/apps/missions.py` | Ported — mission BBS |
| `fileserverscreen` | ✅ | `web/js/main.js` (remote view) | Ported — file listing and operations |
| `passwordscreen` | ✅ | `web/js/main.js` (remote view) | Ported — password cracking UI |
| `highsecurityscreen` | ✅ | `web/js/main.js` (remote view) | Ported — security stack visualization |
| `logscreen` | ✅ | `web/js/main.js` (remote view) | Ported — log viewing and deletion |
| `consolescreen` | ✅ | `web_main.py` (console_command) | Ported — cd, ls, delete, shutdown |
| `securityscreen` | ✅ | `web/js/main.js` (remote view) | Ported — security system management |
| `accountscreen` | ✅ | `core/apps/finance.py` | Ported — bank account management |
| `shareslistscreen` | ✅ | `core/apps/finance.py` | Ported — stock market listing |
| `sharesviewscreen` | ✅ | `core/apps/finance.py` | Ported — stock portfolio view |
| `loansscreen` | ✅ | `core/apps/finance.py` | Ported — loan management |
| `messagescreen` | ✅ | `core/apps/messages.py` | Ported — email/message system |
| `newsscreen` | ✅ | `core/apps/news.py` | Ported — news articles |
| `rankingscreen` | ✅ | `core/apps/rankings.py` | Ported — agent leaderboard |
| `linksscreen` | ✅ | `web/js/os.js` (map app) | Ported — server discovery via links |
| `hwsalesscreen` | ✅ | `core/apps/store.py` | Ported — hardware store |
| `swsalesscreen` | ✅ | `core/apps/store.py` | Ported — software store |
| `academicscreen` | ✅ | `core/remote_controller.py` + `web/js/os.js` | Ported — academic record viewing/editing with two-panel layout, ALTER buttons per field, `window._recordData` for JS access. |
| `criminalscreen` | ✅ | `core/remote_controller.py` + `web/js/os.js` | Ported — criminal record viewing/editing with ALTER buttons. |
| `socialsecurityscreen` | ✅ | `core/remote_controller.py` + `web/js/os.js` | Ported — social security record viewing/editing with ALTER buttons. |
| `recordscreen` | ✅ | `core/remote_controller.py` + `web/js/os.js` | Ported — generic record screen infrastructure via `build_record_screen_html()`. |
| `cypherscreen` | ❌ | — | Not ported — cipher/encryption screen |
| `voiceanalysisscreen` | ❌ | — | Not ported — voice analysis UI |
| `voicephonescreen` | ❌ | — | Not ported — voice phone interface |
| `companyinfoscreen` | ❌ | — | Not ported — company information |
| `contactscreen` | ❌ | — | Not ported — contact directory |
| `useridscreen` | ❌ | — | Not ported — user ID management |
| `changegatewayscreen` | ❌ | — | Not ported — change gateway hardware |
| `nearestgatewayscreen` | ❌ | — | Not ported — find nearest gateway |
| `codecardscreen` | ❌ | — | Not ported — code card system |
| `protovisionscreen` | ❌ | — | Not ported — protovision (ARC storyline) |
| `faithscreen` | ❌ | — | Not ported — Faith storyline screen |
| `nuclearwarscreen` | ❌ | — | Not ported — nuclear war (endgame) |
| `radiotransmitterscreen` | ❌ | — | Not ported — radio transmitter |
| `dialogscreen` | ⚠️ | — | Partially ported — basic dialogs exist |
| `disconnectedscreen` | ✅ | `web/index.html` | Ported — disconnected state |
| `menuscreen` | ✅ | `web/js/os.js` (start menu) | Ported — categorized start menu |

---

## 6. World Entities (`uplink/src/world/`)

| Uplink Source File | Ported? | SB Equivalent | Status Notes |
|---|---|---|---|
| `player.cpp` | ✅ | `core/game_state.py` (PlayerState) | Ported — handle, balance, rating, known_ips, passwords |
| `agent.cpp` | ✅ | `core/npc_engine.py` | Ported — NPC agents with ratings, mission completion, arrests |
| `person.cpp` | ✅ | `core/game_state.py` (Person) | Ported — name, employer, digital footprint |
| `company` | ✅ | `core/game_state.py` (Company) | Ported — companies with stock prices |
| `connection.cpp` | ✅ | `core/connection_manager.py` | Ported — bounce chains, connection state |
| `rating.cpp` | ✅ | `core/game_state.py` | Ported — uplink rating system |
| `date.cpp` | ✅ | `core/game_state.py` (Clock) | Ported — game clock |
| `vlocation.cpp` | ✅ | `core/geodata.py` | Ported — geographic coordinates |
| `world.cpp` | ✅ | `core/game_state.py` (WorldState) | Ported — container for all world entities |
| `message.cpp` | ✅ | `core/game_state.py` (Message) | Ported — email/message system |

---

## 7. Core Systems

| Uplink System | Ported? | SB Equivalent | Status Notes |
|---|---|---|---|
| Game Loop | ✅ | `core/engine.py` | Ported — threaded tick loop with error resilience |
| Serialization | ❌ | — | Not ported — binary save/load (not needed for web version) |
| Eclipse UI Framework | ✅ | `web/js/os.js` | Replaced — high-fidelity HTML5/CSS3 VDE with minimize, snap-to-grid, retro CRT effects, hotkeys, and audio engine. |
| OpenGL View | ❌ | HTML5/CSS3 | Replaced — web rendering |
| Network (multi-monitor) | ❌ | — | Not ported — not applicable |
| Script Library | ❌ | — | Not ported — in-game scripting |
| Obituary System | ❌ | — | Not ported — player death/failure screen |
| Options | ⚠️ | — | Partially ported — speed controls, basic settings |

---

## 8. High-Value Features NOT Yet Ported

### 8.1 Plot & Story System
- **`plotgenerator.cpp`** — Three-act story arcs (Revelation, Faith, ARC) with scene progression
- **`consequencegenerator.cpp`** — Mission chaining, cause-and-effect story logic
- **`runplotsceneevent.cpp`** — Plot scene execution
- **Current SB state:** `core/plot_engine.py` has Revelation Act 1 trigger only; no progression, no Faith/ARC arcs

### 8.2 Record Systems
- **`databank.cpp`** / **`recordbank.cpp`** — Academic, criminal, medical, social security record storage and manipulation
- **Current SB state:** Mission types exist for record changes but no actual record data structures or editing logic

### 8.3 Log Modifier / Framing
- **`logmodifier.cpp`** — Modify log contents to frame other agents
- **Current SB state:** Not implemented

### 8.4 Advanced Tools
- **`voiceanalyser.cpp`** — Voice recording analysis for LAN authentication bypass
- **`decypher.cpp`** — Cipher decryption tool
- **`lanforce.cpp`** — Force LAN locks
- **`gatewaynuke.cpp`** — Destroy target gateway
- **`revelation.cpp`** / **`revelationtracker.cpp`** — Revelation virus and spread tracking

### 8.5 Passive Trace / Forensics (Deep)
- **`bankrobberyevent.cpp`** — NPC bank heists with forensic investigation
- **`seizegatewayevent.cpp`** — Gateway seizure by authorities
- **Current SB state:** `bank_forensics.py` has SHA-256 transaction hashes but no investigation flow, no passive trace from logs

### 8.6 Special Screens
- Academic, Criminal, Medical, Social Security record screens
- Voice analysis interface
- Cipher/encryption screens
- Company info, contact directories
- Code card system
- Protovision/Faith/Nuclear War storyline screens

---

## 9. Features Unique to Sovereign Breach (Not in Uplink)

| Feature | Notes |
|---|---|
| Hardware Thermals & Degradation | CPU overheating, component health, PSU trips |
| CPU Core Scheduling | Multi-core GHz allocation with priority-based scheduling |
| Physical VFS Block Map | Block-based storage with fragmentation and defragmentation |
| Leaflet.js World Map | Real GIS tiles, noWrap, maxBounds, procedural server placement in 6 tech hub regions |
| App Registry System | Modular app architecture (10 apps) |
| Virtual OS with Start Menu | Uplink-style categorized start menu, draggable windows, taskbar |
| PMC Engine | Tactical combat math and interceptions (Squad-based ratings) |
| Logistics Engine | Aircraft, ships, trucks with real-time interpolation, route redirection, and security sabotage |
| Event Ripple System | Hijack → stock crash → news report chain |
| Bank Forensics with SHA-256 | Cryptographic transaction tracing |
| LAN Engine | Topology scanning, probing, spoofing |
| 267 Automated Tests | Comprehensive test suite |

---

## 10. Summary Statistics

| Category | Total Uplink Modules | Fully Ported | Partially Ported | Not Ported |
|---|---|---|---|---|
| World Generators | 10 | 6 | 1 | 3 |
| Event Scheduler | 12 | 4 | 3 | 5 |
| Computer Systems | 14 | 9 | 2 | 3 |
| Hacking Tools | 28 | 21 | 0 | 7 |
| Remote Screens | 34 | 24 | 1 | 9 |
| World Entities | 10 | 10 | 0 | 0 |
| Core Systems | 8 | 4 | 1 | 3 |
| **TOTAL** | **116** | **78 (67%)** | **8 (7%)** | **30 (26%)** |

**Test count: 481 passed, 4 skipped** (up from 478 passed after TDD audit fixes)

### Codebase Audit (April 2026)
Comprehensive audit of Phases 11-16 code found and fixed:
- **CRITICAL**: `pay_bail()` returned `bail_paid: 0` instead of actual amount — fixed by capturing value before zeroing
- **CRITICAL**: `on_game_over()` called `eel.trigger_event()` without existence check — added `hasattr` guard
- **CRITICAL**: `_complete_log_undeleter` was undefined in `core/task_engine.py` — added proper logic to restore `is_deleted` flag on logs
- **CRITICAL**: Bare `except: pass` swallowed all errors in `on_game_over()` and other UI modules — replaced with proper exception logging
- **MEDIUM**: Unnecessary `hasattr(comp, 'log_modified')` check removed
- **MEDIUM**: Misleading bail error message clarified
- **MEDIUM**: Fixed unused local variables and bad boolean comparisons (`== True` vs `is True`) across multiple test files.
- **MEDIUM**: Cleaned up the entire project removing all unused imports via `autoflake` to improve maintainability.

---

## 11. Priority Recommendations for Next Porting Effort

1. **HIGH — FrameUser Missions**: Generate frame missions that check news articles for arrest completion. LogModifier, Full Arrest Flow, and Bail System are all complete — this is the natural next step.
2. **HIGH — TraceUser Missions**: Generate trace missions targeting specific persons. Currently defined but never generated (probability table is all zeros).
3. **LOW — Remaining Tools**: `decypher.cpp`, `lanforce.cpp`, `gatewaynuke.cpp`, `revelation.cpp`
4. **LOW — Storyline Screens**: Protovision, Faith, Nuclear War screens
5. **LOW — Plot Engine Completion**: Port full `plotgenerator.cpp` with all three arcs (Revelation, Faith, ARC) and `consequencegenerator.cpp` for mission chaining
