"""
Sovereign Breach: Kinetic Bridge Prototype (v1.0)
Bridges the Kinetic Ballistics Engine with live GameState data.
"""
import eel
import os
import sys
import math
import random

# Ensure core is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.engine import GameEngine
from core.game_state import NodeType
from core.scenario_heist import init_heist_scenario

class KineticBridge:
    def __init__(self):
        self.engine = GameEngine()
        init_heist_scenario(self.engine.state)
        
        self.selected_target_ip = None
        self.GRAVITY = 9.81
        self.VELOCITY = 900 # m/s (.338 Lapua)

    def get_tactical_targets(self):
        """Returns a list of nodes that can be physically targeted."""
        targets = []
        for c in self.engine.state.computers.values():
            # For now, let's assume all non-localhost nodes are targetable
            if c.ip != "127.0.0.1":
                targets.append({
                    "ip": c.ip,
                    "name": c.name,
                    "x": c.x,
                    "y": c.y,
                    "type": c.computer_type.name
                })
        return targets

    def get_ballistic_data(self, target_ip):
        """Calculates range and generates wind for a specific target node."""
        target = self.engine.state.computers.get(target_ip)
        if not target: return None
        
        self.selected_target_ip = target_ip
        
        # Calculate distance in 'game units' and scale to meters
        # Assuming map units are roughly 1 unit = 100km for map, 
        # but for tactical we'll scale it to a realistic sniper range (400m - 1500m)
        local = self.engine.state.computers.get("127.0.0.1")
        dist = math.sqrt((target.x - local.x)**2 + (target.y - local.y)**2)
        
        # Map distance to a 400m-1600m range for the scope
        simulated_range = 400 + (dist % 1200) 
        
        # Generate wind based on 'region' (stochastic for now)
        # In a full impl, we'd check a weather_map in GameState
        random.seed(target_ip) # Deterministic wind per node for the prototype
        wind_speed = random.uniform(0.5, 8.5)
        wind_dir = random.randint(0, 359)
        
        return {
            "range": round(simulated_range),
            "wind_speed": round(wind_speed, 1),
            "wind_dir": wind_dir,
            "target_name": target.name
        }

    def calculate_shot(self, elevation_moa, windage_moa, data):
        """Processes the physics of the shot."""
        range_m = data['range']
        wind_ms = data['wind_speed']
        wind_dir_deg = data['wind_dir']
        
        # Time of flight
        tof = range_m / self.VELOCITY
        
        # Gravity Drop (cm)
        drop = 0.5 * self.GRAVITY * (tof ** 2) * 100
        
        # Wind Drift (cm)
        rad = math.radians(wind_dir_deg)
        cross_wind = wind_ms * math.sin(rad)
        drift = cross_wind * tof * 50 
        
        # Scope Compensation (MOA to cm at range)
        moa_to_cm = (range_m / 100.0) * 2.908
        comp_elev = elevation_moa * moa_to_cm
        comp_wind = windage_moa * moa_to_cm
        
        final_y = drop - comp_elev
        final_x = drift - comp_wind
        
        # Hit detection (Target is 20cm x 40cm)
        is_hit = abs(final_x) < 10 and abs(final_y) < 20
        
        # Ripple Effect: If we hit, we affect the GameState
        if is_hit and self.selected_target_ip:
            # Placeholder for actual world action:
            # self.engine.state.computers[self.selected_target_ip].security.monitor.active = False
            pass

        return {
            "hit": is_hit,
            "drop_cm": round(drop, 1),
            "drift_cm": round(drift, 1),
            "final_x": round(final_x, 1),
            "final_y": round(final_y, 1)
        }

bridge = KineticBridge()

@eel.expose
def get_targets(): return bridge.get_tactical_targets()

@eel.expose
def get_ballistics(ip): return bridge.get_ballistic_data(ip)

@eel.expose
def fire_shot(elev, windage, data): return bridge.calculate_shot(elev, windage, data)

def start():
    # Absolute path to the prototypes directory
    proto_dir = os.path.dirname(os.path.abspath(__file__))
    # Initialize Eel strictly within the prototypes folder
    eel.init(proto_dir)
    print(f"Launching Kinetic Bridge Prototype from: {proto_dir}")
    # The file is directly in the root of the init directory
    try:
        eel.start('kinetic_bridge_prototype.html', size=(1300, 900), port=8085)
    except (SystemExit, KeyboardInterrupt):
        print("Laboratory shutdown initiated.")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    start()
