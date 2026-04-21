"""
Onlink-Clone: Ultimate Hardware & VFS Prototype (v6.0)
- Process Priority Management (CPU Scheduling)
- High-Fidelity Tool Persistence
- Corrected Right-Click Logic
"""
import eel
import os
import uuid
import threading
import time

class UltimateHardwarePrototype:
    def __init__(self):
        self.gateway = {
            "name": "Ice Queen Prototype",
            "cpu_slots": 4,
            "cpus": [
                {"id": 1, "model": "Standard 10GHz", "base_speed": 10, "speed": 10, "health": 100, "overclock": 1.0},
                {"id": 2, "model": "Standard 10GHz", "base_speed": 10, "speed": 10, "health": 100, "overclock": 1.0},
            ],
            "ram_slots": 16,
            "ram_used": 0,
            "ram_health": 100,
            "ram_overclock": 1.0,
            "storage_capacity": 64,
            "storage_used": 0,
            "storage_health": 100,
            "storage_overclock": 1.0,
            "fragmentation": 0.15,
            "power_draw": 50.0,
            "power_capacity": 500.0,
            "heat": 25.0,
            "max_heat": 90.0,
            "coolant_efficiency": 1.0,
            "credits": 5000,
            "events": []
        }
        
        self.vfs = [
            {"id": "t1", "name": "Password_Breaker", "size_gq": 4, "ram_cost": 4, "type": "tool", "blocks": [0,1,2,3], "compressed": False},
            {"id": "t2", "name": "Log_Deleter", "size_gq": 2, "ram_cost": 2, "type": "tool", "blocks": [5,6], "compressed": False},
            {"id": "t4", "name": "File_Copier", "size_gq": 1, "ram_cost": 1, "type": "tool", "blocks": [10], "compressed": False},
            {"id": "d1", "name": "top_secret.dat", "size_gq": 10, "type": "data", "blocks": list(range(15, 25)), "compressed": False},
        ]
        
        self.running_tasks = []
        self._lock = threading.Lock()
        self._running = True
        self.log_event("SYSTEM BOOT SEQUENCE COMPLETE.")
        
        threading.Thread(target=self._sim_loop, daemon=True).start()

    def log_event(self, msg):
        ts = time.strftime('%H:%M:%S')
        self.gateway["events"].append(f"[{ts}] {msg}")
        if len(self.gateway["events"]) > 12: self.gateway["events"].pop(0)

    def get_state(self):
        with self._lock:
            self.gateway["storage_used"] = sum(f["size_gq"] for f in self.vfs)
            bmap = ["free"] * self.gateway["storage_capacity"]
            for f in self.vfs:
                for b in f["blocks"]:
                    if b < len(bmap): bmap[b] = f["type"]
            
            # Total GHZ available
            total_ghz = sum(c["speed"] for c in self.gateway["cpus"])
            total_priority = sum(t["priority"] for t in self.running_tasks) or 1.0
            
            # Attach shares to tasks for UI
            for t in self.running_tasks:
                t["ghz_share"] = (t["priority"] / total_priority) * total_ghz

            return {
                "gateway": self.gateway,
                "vfs": self.vfs,
                "tasks": self.running_tasks,
                "block_map": bmap,
                "store": [
                    {"id": "st_defrag", "name": "VFS_Defragmenter", "cost": 800, "ram_cost": 4, "size_gq": 4, "type": "tool"},
                    {"id": "st_comp", "name": "Data_Compressor", "cost": 1200, "ram_cost": 2, "size_gq": 2, "type": "tool"},
                    {"id": "up_coolant", "name": "Liquid_Cooling_v1", "cost": 1500, "type": "upgrade"},
                    {"id": "up_psu", "name": "Titan_800W_PSU", "cost": 2000, "type": "upgrade"},
                ]
            }

    def _sim_loop(self):
        while self._running:
            with self._lock:
                # 1. CPU Scheduling & Progress
                total_ghz = sum(c["speed"] for c in self.gateway["cpus"])
                total_priority = sum(t["priority"] for t in self.running_tasks)
                
                if total_priority > 0:
                    for t in self.running_tasks:
                        # Share of CPU power
                        share = (t["priority"] / total_priority) * total_ghz
                        # Progress speed depends on GHz share and RAM overclock
                        progress_inc = (share / 10.0) * self.gateway["ram_overclock"]
                        t["progress"] = min(100, t["progress"] + progress_inc)
                
                # 2. Power & Heat
                base = 40.0
                task_load = sum(t.get("ram", 0) for t in self.running_tasks) * 5.0
                oc_load = sum((c["overclock"] - 1.0) * 150 for c in self.gateway["cpus"])
                self.gateway["power_draw"] = base + task_load + oc_load
                
                gen = self.gateway["power_draw"] * 0.1
                cool = self.gateway["coolant_efficiency"] * 8.0
                self.gateway["heat"] = max(25.0, self.gateway["heat"] + (gen - cool) * 0.1)
                
                if self.gateway["heat"] > self.gateway["max_heat"]:
                    dmg = (self.gateway["heat"] - self.gateway["max_heat"]) * 0.05
                    for c in self.gateway["cpus"]: c["health"] = max(0, c["health"] - dmg)

            time.sleep(1)

    def purchase(self, sid):
        with self._lock:
            if sid == "up_coolant" and self.gateway["credits"] >= 1500:
                self.gateway["credits"] -= 1500; self.gateway["coolant_efficiency"] = 2.5; return True
            if sid == "up_psu" and self.gateway["credits"] >= 2000:
                self.gateway["credits"] -= 2000; self.gateway["power_capacity"] = 800; return True
            
            # Tools
            cat = [
                {"id": "st_defrag", "name": "VFS_Defragmenter", "cost": 800, "ram_cost": 4, "size_gq": 4, "type": "tool"},
                {"id": "st_comp", "name": "Data_Compressor", "cost": 1200, "ram_cost": 2, "size_gq": 2, "type": "tool"},
            ]
            item = next((i for i in cat if i["id"] == sid), None)
            if not item or self.gateway["credits"] < item["cost"]: return False
            
            used = set()
            for f in self.vfs: used.update(f["blocks"])
            free = [i for i in range(self.gateway["storage_capacity"]) if i not in used]
            if len(free) < item["size_gq"]: return False
            
            new_f = item.copy(); new_f["id"] = str(uuid.uuid4())[:8]; new_f["blocks"] = free[:item["size_gq"]]; new_f["compressed"] = False
            self.vfs.append(new_f); self.gateway["credits"] -= item["cost"]
            return True

    def run_tool(self, fid):
        with self._lock:
            f = next((x for x in self.vfs if x["id"] == fid), None)
            if not f or f["type"] != "tool": return False
            if self.gateway["ram_used"] + f["ram_cost"] > self.gateway["ram_slots"]: return False
            
            task = {
                "id": str(uuid.uuid4())[:4], 
                "name": f["name"], 
                "ram": f["ram_cost"], 
                "priority": 1.0, 
                "progress": 0.0
            }
            self.running_tasks.append(task)
            self.gateway["ram_used"] += f["ram_cost"]
            return True

    def kill_task(self, tid):
        with self._lock:
            t = next((x for x in self.running_tasks if x["id"] == tid), None)
            if t:
                self.gateway["ram_used"] -= t["ram"]
                self.running_tasks.remove(t)
                return True
        return False

    def set_priority(self, tid, val):
        with self._lock:
            t = next((x for x in self.running_tasks if x["id"] == tid), None)
            if t:
                t["priority"] = float(val)
                return True
        return False

    def tool_action(self, tname, fid):
        with self._lock:
            f = next((x for x in self.vfs if x["id"] == fid), None)
            if not f: return {"msg": "File not found"}
            if tname == "Log_Deleter":
                self.vfs.remove(f)
                return {"msg": "File purged."}
            return {"msg": "Tool action applied."}

    def set_oc(self, mode, cid, val):
        with self._lock:
            if mode == "cpu":
                for c in self.gateway["cpus"]:
                    if c["id"] == cid:
                        c["overclock"] = val; c["speed"] = c["base_speed"] * val
            elif mode == "ram": self.gateway["ram_overclock"] = val
            elif mode == "storage": self.gateway["storage_overclock"] = val
            return True

# --- Eel Logic ---
p = UltimateHardwarePrototype()
@eel.expose
def get_state(): return p.get_state()
@eel.expose
def buy(sid): return p.purchase(sid)
@eel.expose
def launch(fid): return p.run_tool(fid)
@eel.expose
def kill(tid): return p.kill_task(tid)
@eel.expose
def set_priority(tid, val): return p.set_priority(tid, val)
@eel.expose
def action(tname, fid): return p.tool_action(tname, fid)
@eel.expose
def set_oc(mode, cid, val): return p.set_oc(mode, cid, float(val))

def start():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    eel.init('web')
    eel.start('detailed_vfs_prototype.html', size=(1300, 900))

if __name__ == "__main__":
    start()
