"""
Onlink-Clone: Standalone World Map Prototype Launcher
Focuses strictly on the high-fidelity map logic.
"""
import eel
import os
import sys

# Ensure core is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.engine import GameEngine
from core.scenario_heist import init_heist_scenario

from core.game_state import NodeType

# Init engine with heist nodes for testing
print("DEBUG: Initializing Game Engine and Heist Scenario...")
engine = GameEngine()
init_heist_scenario(engine.state)
print(f"DEBUG: Nodes loaded: {len(engine.state.computers)}")

@eel.expose
def get_nodes():
    nodes = []
    for c in engine.state.computers.values():
        if c.ip in engine.state.player.known_ips or c.computer_type == NodeType.VEHICLE:
            nodes.append({
                "ip": c.ip, "name": c.name, 
                "x": c.x, "y": c.y,
                "type": c.computer_type.value
            })
    print(f"DEBUG: Frontend requested nodes - sending {len(nodes)} objects")
    return nodes

@eel.expose
def save_ip(ip):
    if ip not in engine.state.player.known_ips and ip in engine.state.computers:
        engine.state.player.known_ips.append(ip)
        return {"success": True, "msg": f"IP {ip} added to map."}
    return {"success": False, "msg": "IP already known or invalid."}

@eel.expose
def get_bounce_chain():
    chain = engine.state.bounce.hops
    # Enforce logic: Must start with localhost
    if not chain or chain[0] != "127.0.0.1":
        if "127.0.0.1" in chain: chain.remove("127.0.0.1")
        chain.insert(0, "127.0.0.1")
    return chain

@eel.expose
def toggle_bounce(ip):
    chain = engine.state.bounce.hops
    if ip == "127.0.0.1": return chain # Cannot remove localhost
    
    if ip in chain:
        chain.remove(ip)
    else:
        chain.append(ip)
    return chain

def start():
    # Force absolute paths for web assets
    base_dir = os.path.dirname(os.path.abspath(__file__))
    web_dir = os.path.join(base_dir, 'web')
    os.chdir(base_dir)
    
    eel.init(web_dir)
    print(f"DEBUG: Launching Standalone Map Prototype from {web_dir}...")
    # Mode='edge' or 'chrome' or 'default'
    eel.start('map_prototype.html', size=(1000, 600), port=8081)

if __name__ == "__main__":
    start()
