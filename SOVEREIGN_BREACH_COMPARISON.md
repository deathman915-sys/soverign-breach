# Sovereign Breach vs. Uplink/Onlink: Architectural Comparison & Evolution

This report compares the legacy **Uplink/Onlink** systems with the **Sovereign Breach** (SB) prototype. It identifies the technical deltas and outlines a strategy to surpass both by leveraging modern architectural patterns and simulation depth.

---

## 1. Architectural Overview

| Feature | Uplink / Onlink | Sovereign Breach (SB) | The "Better Than Both" Advantage |
| :--- | :--- | :--- | :--- |
| **Language** | Monolithic C++ | Decoupled Python + HTML5/JS | **Modularity:** SB's Python core allows for rapid prototyping and AI-agentic integration (MCP). |
| **UI Engine** | Fixed-resolution SDL/OpenGL | Eel / Chrome (HTML5/CSS/JS) | **Fidelity:** SB uses modern web-tech for a high-density, "living" OS interface with CSS effects. |
| **Logic Pattern** | Tight-coupled OO | **Message Broker (Hub & Spoke)** | **Scalability:** Independent modules (Hacking, Routing, WorldSim) communicate via a central broker. |
| **Simulation** | Static, Scripted | **Macro-to-Micro GIS Sandbox** | **Persistence:** Procedural "Lazy Loading" (The Matrix Illusion) allows for a massive living world without CPU melting. |

---

## 2. Core Mechanics Comparison

### 2.1 Connection & Bouncing
*   **Legacy:** Static IP bouncing. Logs are simple strings in a text file.
*   **Sovereign Breach:**
    *   **Improvement:** Routing is handled by a standalone `map_router.py`. 
    *   **Evolution:** Introduce **VFS-based logs** that aren't just strings but interactive database objects that can be manipulated, encrypted, or "salted" by advanced admins.
    *   **New Feature:** **Physical Infrastructure Routing**. Bouncing through a server in a city with a power outage (caused by the player) should fail or introduce lag.

### 2.2 Hacking Tools & Interaction
*   **Legacy:** Drag-and-drop tools that run on a timer.
*   **Sovereign Breach:**
    *   **Improvement:** Tools are independent Python processes (`remote_prototype.py`).
    *   **Evolution:** **Tool Synergies.** Running a "Packet Sniffer" while a "Password Breaker" is active provides a speed bonus by pre-filling dictionary buffers.
    *   **New Feature:** **Hardware-bound Performance.** Tools are limited by Gateway RAM slots and CPU heat, directly ported and enhanced from the Onlink hardware mechanics.

---

## 3. The "Better Than Both" Strategy: Feature Roadmap

To surpass the legacy titles, Sovereign Breach will implement the following high-fidelity systems:

### 3.1 Advanced Hardware Engineering (The Onlink Delta)
*   **RAM Management:** Tools are executables that must be loaded into "RAM Slots." Players must choose between running multiple low-tier tools or one heavy-duty cracker.
*   **Individual CPU Overclocking:** Each core in the player's Gateway can be pushed to its limit, increasing processing speed but risking **Component Health** degradation and triggering high-thermal alarms that make the Gateway easier to detect.
*   **VFS Bus Speeds:** Internal file operations (copy/move/delete) are tied to a dedicated bus speed, making "smash and grab" data heists a matter of hardware specs, not just timer bars.

### 3.2 Global Infrastructure & Utility Grids (Macro Layer)
*   **GIS Integration:** A dynamic world map (Leaflet.js) where players can zoom from global clusters down to street-level transformers.
*   **Cross-Domain Impact:** Hacking a city's power grid or water treatment plant creates real-world ripples—stocks crash, transport halts, and security levels on local targets drop (or spike) as they switch to backup protocols.

### 3.3 NPC Agent Agency & Rivalry
*   **Persistent Rivals:** NPC hackers aren't just scripted events; they are entities with their own Gateways, reputations, and goals. 
*   **Mission Competition:** NPCs can "outbid" or "out-hack" the player for BBS missions.
*   **Forensic Framing:** NPCs (and the player) can plant logs that point to each other, triggering the "Passive Trace" system on a rival, effectively using the law as a weapon.

---

## 4. Technical Implementation Priorities (Next Steps)

1.  **[Core] Bank Transaction & Log Forensic Engine:** Port the multi-stage transfer logic from Uplink's `bankcomputer.cpp` but enhance it with modern SQL-backed VFS for high-speed forensic searches.
2.  **[UI] Floating Tool Widgets:** Transition from the sidebar UI to a fully draggable, windowed system where hacking tools are "Mini-Apps" within the VDE.
3.  **[Sim] Utility Grid Interdependency:** Create a state machine in `world_sim_prototype.py` that links infrastructure health to target security levels.
4.  **[AI] Agentic Content Generation:** Use LLM integration to generate unique, context-aware news stories and mission briefings based on the current state of the global simulation.

---

## 5. Summary: Why Sovereign Breach Wins
Sovereign Breach wins by combining the **hardcore hardware depth of Onlink**, the **cohesive world-building of Uplink**, and a **modern, modular architecture** that allows for infinite expansion into global infrastructure and AI-driven gameplay. It is not just a game; it is a living cybernetic sandbox.
