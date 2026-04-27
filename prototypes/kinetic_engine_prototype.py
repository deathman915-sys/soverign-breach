"""
Sovereign Breach: Kinetic Engine Prototype
Handles ballistics, physical travel, and tactical inventory.
"""
from __future__ import annotations
import math
import random
from dataclasses import dataclass, field

@dataclass
class BallisticResult:
    hit: bool
    drop_cm: float
    drift_cm: float
    message: str

class KineticEngine:
    def __init__(self):
        # Constants for .338 Lapua Magnum (approximate)
        self.GRAVITY = 9.81
        self.VELOCITY = 900 # m/s

    def calculate_shot(self, range_m: float, wind_ms: float, wind_dir_deg: float, elev_moa: float, windage_moa: float) -> BallisticResult:
        """
        Simplied ballistic calculation for the prototype.
        """
        # Time of flight
        tof = range_m / self.VELOCITY
        
        # Gravity Drop (cm)
        drop = 0.5 * self.GRAVITY * (tof ** 2) * 100
        
        # Wind Drift (cm)
        # Assuming wind is perpendicular for simplicity in prototype
        rad = math.radians(wind_dir_deg)
        cross_wind = wind_ms * math.sin(rad)
        drift = cross_wind * tof * 50 # Arbitrary factor for visible drift
        
        # Scope Compensation (MOA to cm at range)
        # 1 MOA is ~2.9cm at 100m
        moa_to_cm = (range_m / 100.0) * 2.908
        comp_elev = elev_moa * moa_to_cm
        comp_wind = windage_moa * moa_to_cm
        
        final_y = drop - comp_elev
        final_x = drift - comp_wind
        
        # Hit detection (Target is 20cm x 40cm)
        is_hit = abs(final_x) < 10 and abs(final_y) < 20
        
        msg = "TARGET NEUTRALIZED" if is_hit else "MISS: ADJUST AND RE-ENGAGE"
        if not is_hit:
            if final_y > 20: msg += " (SHOT LOW)"
            elif final_y < -20: msg += " (SHOT HIGH)"
            if final_x > 10: msg += " (DRIFT RIGHT)"
            elif final_x < -10: msg += " (DRIFT LEFT)"

        return BallisticResult(is_hit, drop, drift, msg)

# Prototype Test
if __name__ == "__main__":
    eng = KineticEngine()
    # 800m shot, 5m/s full value wind
    res = eng.calculate_shot(800, 5, 90, 0, 0)
    print(f"Untrained Shot: {res.message} (Drop: {res.drop_cm:.1f}cm, Drift: {res.drift_cm:.1f}cm)")
    
    # Adjusted shot (Simulating player clicking dials)
    # At 800m, drop is ~388cm. 388 / (8 * 2.9) = ~16.7 MOA
    res_adj = eng.calculate_shot(800, 5, 90, 16.7, 1.8)
    print(f"Adjusted Shot: {res_adj.message}")
