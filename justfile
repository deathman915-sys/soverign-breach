# justfile for Sovereign Breach (High-Fidelity Hacking Simulation)

# Detect OS: windows = PowerShell, linux/mac = bash
os := if os() == "windows" { "windows" } else { "linux" }

# Platform-specific settings
shell := if os == "windows" { ["powershell.exe", "-Command"] } else { ["bash", "-c"] }
python := if os == "windows" { "D:/pyth/.venv/Scripts/python.exe" } else { ".venv/bin/python" }

# Default action: Execute a full structural and logical audit
default: audit

# Run all core simulation tests (518+ cases)
test:
    {{python}} -m pytest tests/ -q --tb=short

# Run the structural linter (Ruff) to catch code smells
lint:
    ruff check core/

# Execute a full audit: Linting followed by Runtime Tests
audit: lint test

# Launch the unified Web UI simulation engine
run:
    {{python}} web_main.py

# View codebase metrics and architectural expansion
stats:
    tokei .

# Monitor system thermals and CPU load in real-time
monitor:
    btm

# Teleport to the core application logic
nav-apps:
    z apps

# Synchronize the local Forge with the GitHub cloud
uplink msg="Forge Update: Manual Synchronization":
    git add .
    git commit -m "{{msg}}"
    git push origin main

# Perform a structural search for specific patterns
search pattern:
    sg -p "{{pattern}}"
