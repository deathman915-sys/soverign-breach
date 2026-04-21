# Onlink-Clone: Detailed Mechanics & Gameplay Guide

This document serves as the foundational "Brain" for the simulation logic, derived from the core Uplink/Onlink mechanics and enhanced for our high-fidelity clone.

---

## 1. Connection & Bouncing (The "Paper Trail")
The core of survival is managing how you connect to a target.
- **Bouncing**: Every connection MUST be routed through multiple nodes (Servers, Personal Computers, Mainframes).
- **InterNIC**: The industry-standard first bounce point. As a public database, its logs are easily accessible and deletable by the player.
- **Log Chain**: 
    - When you connect: [Gateway] -> [InterNIC] -> [Node A] -> [Node B] -> [Target].
    - Each node records a "Connection from [Previous IP] routed to [Next IP]".
    - To disappear, you must delete the log on InterNIC that points back to your Gateway.

---

## 2. Tracing Systems
### Active Trace (Real-time)
- **Trigger**: Starts the moment you perform an unauthorized action (cracking, bypassing, accessing files) or immediately upon connection to high-sec servers.
- **Visual**: A red line crawling backwards from the Target through your bounce chain.
- **Mechanism**: The Target admin is actively tracking the route.
- **Game Over**: If the red line reaches your Gateway, you are caught immediately. You must disconnect before this happens.

### Passive Trace (Forensics)
- **Trigger**: Happens *after* you disconnect.
- **Mechanism**: Authorities examine the logs you left behind. They follow the "Connection from..." breadcrumbs from the Target, to Node B, to Node A, to InterNIC.
- **Survival**: If you delete the log at InterNIC, the trail goes "cold". If you don't, you will be caught several hours/days later.

---

## 3. Log Management (Forensics)
Logs are physical "files" stored on servers.
- **Log Types**:
    - **Connection**: Logins/Routing.
    - **Auth**: Password attempts (success/fail).
    - **Data**: File copies, deletions, transfers.
- **Log Deleter (Tool)**:
    - **Level 1-3**: Only clears the text, leaving an empty log entry. Advanced NPCs can still see a connection occurred.
    - **Level 4.0+**: Completely erases the log entry, leaving no trace. **This is required for high-tier play.**

---

## 4. Hardware & Software Ecosystem
### Software Categories
1.  **Crackers**: Password Breakers, Dictionary Hackers.
2.  **Bypassers**: Proxy/Firewall/Monitor Bypassers. These allow you to hack *silently* (without starting an active trace).
3.  **Utility**: Log Deleters, File Copiers, Decrypters.
4.  **Security**: Trace Trackers (shows the red line on your HUD).

### Hardware (The Gateway)
- **CPUs**: Determine how fast your software runs. More CPUs = faster password cracking.
- **Memory (RAM)**: In Onlink, tools consume RAM to run. You can only run as many tools as your RAM supports.
- **Storage (VFS)**: Persistent storage for files and downloaded tools.
- **Modems**: Determine connection speed (critical for large file transfers).

---

## 5. Mission Progression
1.  **Novice**: Copying/Deleting files from simple servers.
2.  **Intermediate**: Modifying academic/criminal records, bank transfers.
3.  **Elite**: Mainframe destruction, LAN infiltration, Storyline/Plot missions.
4.  **The End-Game**: Managing a Private Military Company (PMC) layer, orchestrating global infrastructure blackouts, and competing with advanced Rival AIs.

---

## 7. Standalone Onlink Core Mechanics (The "Hardcore" Layer)
While original Uplink is the base, the Standalone Onlink engine introduces several high-complexity simulation layers:

### 7.1 Advanced Hardware Engineering
- **RAM Slots vs. VFS Storage**: 
    - **VFS (Drive)**: Passive storage for software and data files.
    - **RAM (Memory)**: Active execution space. Tools MUST be loaded into RAM to run. Each tool has a "RAM footprint" (e.g., Password Breaker v1.0 takes 2 slots).
- **Individual CPU Overclocking**: Each CPU in the Gateway can be pushed independently. Higher clock speeds = faster execution but increased **Power Draw** and **Heat**.
- **Bus Speeds (VFS Overclocking)**: Specifically affects internal file transfer (Copy/Move/Delete) and download/upload speeds.
- **Component Health**: Hardware degrades under heat or due to security "Neural Spikes." Health < 100% can cause random crashes or total component failure.

### 7.2 The Neural Interface
- **Mechanism**: A direct brain-to-gateway link (~50,000 credits).
- **Gameplay Change**: Removes traditional "UI lag" and allows for the most advanced LAN hacking maneuvers.
- **High Risk**: Connecting to a system that is "Neural Spiked" or physically destroyed while linked can result in character death or permanent rating loss.

### 7.3 Advanced Interactivity
- **Multi-Tasking**: The UI is designed for high density—multiple bypassers, traces, and crackers running simultaneously in an overlapping window system.
- **Console Scripting**: The terminal is a full script execution environment for automated log cleaning and multi-node routing.

---

## 8. Development Roadmap Strategy
To build "Better than Both," we focus on these technical deltas:
1.  **Pure Logic Separation**: All hardware calculations (Heat delta, Power curves, RAM allocation) live in the `core/` engine, independent of visual framework.
2.  **Web UI Fidelity**: Using HTML5 Canvas for the world map and CSS filters for the "Neural Interface" visual effects (e.g., chromatic aberration, screen shake).
3.  **Mouse-Driven Flow**: Implementing the "drag-and-drop tool targeting" system seen in high-level Onlink play.
