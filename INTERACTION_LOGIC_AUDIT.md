# Interaction Logic Audit: Sovereign Breach vs. Uplink

This document audits how the player interacts with servers and buys upgrades in Sovereign Breach compared to the original Uplink C++ source code. 

---

## ✅ RESOLVED PROTOCOL GAPS

The following issues identified in previous audits have been successfully addressed and verified in the current codebase.

### 1.1 Manual Bouncing & World Map
- **STATUS: FIXED.** The player can now manually build bounce routes on the World Map by clicking servers in sequence. 
- **Verification:** `os.js` handles `toggle_bounce` on click; `WorldMap` renders the chain with orange dashed lines.

### 1.2 Access-Level Trace Modifiers
- **STATUS: FIXED.** Trace speed is no longer uniform. 
- **Verification:** `core/trace_engine.py:calculate_trace_speed` implements Uplink-spec multipliers:
  - No Account: `0.1x`
  - Known Password: `0.7x`
  - Admin Access: `1.0x`
  - Bank Admin: `1.6x`

### 1.3 Trace Consequences & Forensics
- **STATUS: FIXED.** Trace completion now has terminal consequences, and investigations continue after disconnect.
- **Verification:** `engine.py` triggers `game_over` on 100% trace. `_tick_passive_traces()` and `npc_engine.process_npc_investigations()` handle the forensic "Passive Trace" layer.

---

## ❌ REMAINING PROTOCOL DIVERGENCES

### 1. HARDWARE UPGRADES (The Bundle Trap)
**Severity: HIGH**
- **Issue:** Hardware is still sold as pre-packaged Gateway bundles (ALPHA, BETA, etc.) in `store_engine.py`.
- **Uplink Spec:** Hardware should be modular. Players should be able to buy individual CPUs (20GHz - 200GHz), Modems, and Memory (GQ) components.
- **Impact:** Progression is chunky and forced rather than incremental and strategic.

### 2. SECURITY SYSTEMS (Bypass vs. Disable)
**Severity: HIGH**
- **Issue:** SB's `SecuritySystem` only has an `is_active` state. Disabling a proxy or firewall is permanent for that session.
- **Uplink Spec:** Security should have a `bypassed` state. A bypass is temporary and ends on disconnect. 
- **Missing Type:** The "Encrypter" (Cypher) security type is currently missing from `game_state.py`.

### 3. COMPUTER SELF-MAINTENANCE (The Dead World)
**Severity: HIGH**
- **Issue:** Servers are static. Once hacked, they stay hacked. Logs never expire.
- **Uplink Spec:** Computers should have an "Internal AI" that periodically:
  - Re-enables security systems and changes admin passwords after a breach.
  - Deletes logs older than a specific tick threshold.
  - Generates ambient traffic and new data files.
- **Impact:** The world feels like a static collection of nodes rather than a living network.

---

## 🛠️ RECOMMENDED ROADMAP

1. **Modular Hardware:** Refactor `store_engine.py` and `game_state.py` to support individual component slots and purchases.
2. **Temporary Bypassing:** Add `is_bypassed` to `SecuritySystem` and clear it in `connection_manager.py:disconnect()`.
3. **Computer AI Tick:** Add a `maintenance_tick` to `Computer` logic in `world_sim.py` to handle log cleanup and security restoration.
