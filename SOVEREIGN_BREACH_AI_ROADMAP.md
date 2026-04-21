# Sovereign Breach: Architectural & Feature Comparison vs. Uplink & Onlink

**Objective**: Provide a structured, machine-readable (AI-ingestible) comparison between the legacy Uplink/Onlink codebases and the Sovereign Breach (SB) clone, outlining architectural deltas, mechanics, and proposed feature specifications to exceed both systems.

## 1. System Architecture Data
```yaml
ArchitectureComparison:
  Uplink:
    Language: "C++ (Monolithic)"
    UI_Engine: "SDL/OpenGL (Fixed-resolution)"
    Paradigm: "Tight-coupled Object-Oriented"
    World_Simulation: "Static, Scripted Events"
  Onlink:
    Language: "C++ (Monolithic, modified Uplink core)"
    UI_Engine: "SDL/OpenGL (Complex UI overlay)"
    Paradigm: "Tight-coupled Object-Oriented"
    World_Simulation: "Static, expanded with hardcoded NPC agents and complex hardware limits"
  Sovereign_Breach:
    Language: "Python (Backend) + HTML5/CSS/JS (Frontend)"
    UI_Engine: "Eel / Chrome VDE (Virtual Desktop Environment)"
    Paradigm: "Message Broker / Hub & Spoke (Decoupled ECS-like)"
    World_Simulation: "Macro-to-Micro GIS Sandbox (Procedural Lazy Loading)"
```

## 2. Core Mechanics Delta
```json
{
  "Mechanics": {
    "Routing_And_Bouncing": {
      "Uplink": "Static IP bouncing; logs are simple strings in text files.",
      "Onlink": "Same as Uplink, but requires more rigorous log wiping to avoid advanced passive traces.",
      "Sovereign_Breach": "Dynamic routing via core/network_graph.py. Logs are VFS objects.",
      "Proposed_Enhancement": "Physical Infrastructure Routing. Introduce node latency based on simulated real-world GIS utility grids (e.g., regional power outages cause node lag or failures)."
    },
    "Security_And_Tools": {
      "Uplink": "Proxy, Firewall, Monitor. Voice authorization.",
      "Onlink": "Adds Bandwidth monitors, Sentry systems, Elliptic Curve encryption. Biometrics (Retinal/Fingerprint).",
      "Sovereign_Breach": "Modular TaskEngine integrated with HardwareEngine for priority-based GHz allocation.",
      "Proposed_Enhancement": "Zero-Day Vulnerability Research. Instead of just buying tools, players can analyze procedural code snippets in VFS to compile custom bypassers. Combine Onlink's biometrics with SB's macro-sim (e.g., tracking a CEO's GPS via their phone to bypass 2FA)."
    },
    "Hardware_Simulation": {
      "Uplink": "Simple CPU and Modem upgrades increase global speed.",
      "Onlink": "RAM slots dictate active tools. Individual CPU overclocking creates heat. VFS bus speeds bottleneck data transfers.",
      "Sovereign_Breach": "Standalone core/hardware_engine.py manages multi-core scheduling, thermals, and power limits.",
      "Proposed_Enhancement": "Thermal Dynamics & Hardware Lifecycles. Overclocking degrades physical components. Players must buy physical server racks and manage cooling systems, directly impacting operational stealth (high heat = high power draw = physical location trace)."
    }
  }
}
```

## 3. "Better Than Both": Proposed Feature Roadmap (AI Ingestible)
```yaml
ProposedFeatures:
  - Feature_ID: "F-001"
    Name: "Dynamic Infrastructure Interdependency"
    Category: "Simulation"
    Description: >
      Instead of isolated servers, all nodes are tied to a macro GIS grid. 
      Hacking a SCADA system at a regional power plant drops the power for that region, 
      causing dependent financial servers to switch to backup UPS, lowering their 
      security tier temporarily but alerting physical PMC (Private Military) forces.
    Dependencies: ["core/world_sim.py", "Leaflet.js UI"]

  - Feature_ID: "F-002"
    Name: "Advanced NPC Hacking Ecosystem"
    Category: "AI/Entities"
    Description: >
      Expanding Onlink's AI agents into fully autonomous entities with their own Gateways 
      and VFS. NPCs will bid on BBS missions, attempt to frame the player by planting 
      VFS log objects, and can be physically tracked down.
    Dependencies: ["core/npc_engine.py", "core/mission_engine.py"]

  - Feature_ID: "F-003"
    Name: "Physical/Digital Crossover (OSINT)"
    Category: "Gameplay Mechanics"
    Description: >
      Implement Open-Source Intelligence (OSINT) gathering. Players must search a simulated 
      'in-game internet' or social media nodes to find passwords, employee IDs, or daily 
      schedules to bypass biometrics (e.g., knowing an admin is on a flight to bypass 
      a geographic IP-lock).
    Dependencies: ["web_main.py", "core/world_generator.py"]

  - Feature_ID: "F-004"
    Name: "Software Company Heists & Zero-Days"
    Category: "Economy & Progression"
    Description: >
      Adapting Onlink's software theft: Players can infiltrate security firm LANs 
      to steal alpha versions of hacking tools or discover 'Zero-Day' exploits 
      for specific server versions, allowing instant bypasses until patched.
    Dependencies: ["core/store_engine.py", "LAN generation logic"]
```

## 4. Technical Integration Tasks for Sovereign Breach
To fully realize this blueprint, the following AI-assisted integration steps are required:
1. **Port Uplink's Bank Logic**: Translate `bankcomputer.cpp` into a Python module (`bank_forensics.py`). Upgrade the string-based log matching to SQL/JSON-based transaction hashes.
2. **Implement Onlink's Hardware Rules (Complete)**: Integrated the logic of "RAM Slots" and "CPU Overclocking Heat" directly into `core/hardware_engine.py`. This engine handles component degradation, power draw, and CPU scheduling, exposing its state to `web_main.py` via the unified Eel bridge.
3. **Build the VFS Object Model (Complete)**: Transitioned files from basic dictionaries to full classes (`VFSFile` in `core/game_state.py`) capable of storing encrypted payloads, block mappings, and digital signatures.