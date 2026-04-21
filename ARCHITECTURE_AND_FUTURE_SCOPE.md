# Sovereign Breach: Macro-to-Micro Architectural Blueprint & Future Scope

This document defines the advanced simulation parameters, module interactions, and future scope for Sovereign Breach (formerly Onlink-Clone). It serves as the primary contextual reference for AI agentic integration (Gemini CLI / MCP) regarding the system's architecture.

---

## 1. The Core Architecture: Message Broker Pattern
The system fundamentally rejects a monolithic structure in favor of a highly decoupled, modular design akin to an Entity Component System (ECS).

* **The Bridge (`Eel`):** The HTML5/CSS/JS frontend acts purely as a visual renderer and input catcher. It communicates exclusively via Eel.
* **The Hub (`core/engine.py`):** The central Python engine acts as a **Message Broker**. It does not run specific game logic (like hacking or routing). Instead, it receives Eel callbacks from the Web UI and routes them to the appropriate standalone Python modules.
* **The Modules:** Independent Python scripts (e.g., `gateway.py`, `map_router.py`, `remote_target.py`) that handle specific domain logic. They communicate with each other *only* through `core/engine.py`. 

---

## 2. The Virtual OS Layer (VDE)
The frontend is designed as a Virtual Desktop Environment (VDE) utilizing web-native DOM manipulation.

* **Window Management:** Modules render as draggable, minimizable HTML `<div>` elements with dynamic `z-index` sorting.
* **Nested Logic:** Due to decoupling, "games within the game" (e.g., retro arcades) or distinct applications (e.g., a Start Menu, a Login Screen) can run simultaneously in the VDE without polluting the core simulation loop.
* **Floating Tool UI (Planned):** Evolving from a sidebar-only setup to contextual, draggable popup action widgets for individual hacking tools, mirroring Onlink's advanced interaction paradigms.

---

## 3. Future Scope: The Cybernetic GIS Sandbox
The project will expand from a localized hacking simulator into a global, living simulation spanning macro-economics to individual entities.

### 3.1 Global Systems Integration (Macro Layer)
The simulation tracks high-level abstracted mathematics for global infrastructure:
* **WebGIS Map:** Transitioning from static coordinate images to a dynamic, tile-based mapping system (like Leaflet.js) to allow zooming from global InterNIC views down to specific street-level targets (e.g., a specific hospital or transport depot in Christchurch).
* **Utility Grids & Infrastructure:** Hacking a regional power grid drops its power state, which creates a ripple effect: transport hubs halt, stock prices for affected logistics companies crash, and local targets switch to backup generators.
* **Logistics & PMC:** Players can hack transport companies to modify cargo manifests, intercept shipping vessels or aircraft, and coordinate with their own Private Military Company (PMC) layer.

### 3.2 "Lazy Loading" Procedural Generation (Micro Layer)
To prevent hardware bottlenecking (CPU/RAM melting), the simulation uses "The Matrix Illusion" for individual-level data.
* **Abstract until observed:** The system does not simulate millions of individuals in the background. 
* **Procedural Instantiation:** When the player breaches a specific micro-target (e.g., gaining root access to a hospital database), the engine procedurally generates the required localized data (e.g., 500 patient records, blood types, billing histories) in that exact moment.
* **Persistence:** Only individuals or data points that the player explicitly interacts with or alters are saved permanently to the VFS (Virtual File System) database.

---

## 4. Deep Reference Porting (The Uplink & Onlink Legacy)
To ensure the simulation remains "Better Than Both" Onlink and Uplink, we formally incorporate high-value logic from the original Uplink source code (and its modern Python forks) alongside advanced mechanics conceptualized in Onlink into our decoupled architecture.

### 4.1 Procedural Plot Generator (`PlotGenerator.cpp`)
We port the core logic that chains independent missions into cohesive world-changing "arcs." This includes:
* **Consequence Logic:** Ensuring that a successful hack on a research server triggers a specific sequence of news stories and follow-up "clean-up" missions.
* **Ambient World Events:** Adapting the "Company Bust" and "Stock Market Crash" triggers that keep the world feeling alive without player input.

### 4.2 Advanced Onlink Security & Interaction
Incorporating Onlink's hardcore difficulty and deep mechanics:
* **Voice Recording & Authentication:** Required to bypass high-level LAN locks.
* **Advanced Cryptography:** Implementing Elliptic Curve encryption layers over standard decipher tasks.
* **Dynamic Software Company Raids:** Allowing players to physically (or digitally) infiltrate software developers to steal next-gen hacking tools rather than purchasing them.
* **VFS Parity:** Expanding the Memory Banks to natively display and store both executable tools and plain-text files (like intercepted passwords) seamlessly.

### 4.3 NPC Competition & Agency (`agent.cpp`)
We integrate the logic that allows NPC hackers to exist as entities in the world:
* **Mission Snatching:** NPCs can accept and complete missions from the BBS before the player, creating a sense of urgency.
* **Forensic Framing:** Implementing the logic for NPCs to plant logs or "frame" the player (or other NPCs) for their own crimes, triggering the Passive Trace system.

### 4.4 Financial & Forensic Systems (`bankcomputer.cpp` / `newsgenerator.cpp`)
We adapt the deep-level data structures for:
* **Bank Transaction Logs:** Porting the multi-stage transfer and "log-matching" logic that makes bank heists a high-stakes forensic puzzle.
* **Procedural News Templates:** Using the multi-part headline/body template system to generate immersive, reactive journalism based on simulated world events.

### 4.5 Reference Implementation Tracking
* [x] **News Template System** (Ported from `news_engine.py` reference)
* [x] **Mission Completion Logic** (Ported from `mission_engine.py` reference)
* [ ] **Bank Transaction & Log Forensic Engine** (Planned)
* [ ] **NPC Agent Lifecycle & Competition** (Planned)
* [ ] **Procedural Plot & Consequence Engine** (Planned)
* [ ] **Floating Tool Widgets UI** (Planned)
* [ ] **Advanced LAN Voice Auth & Crypto** (Planned)