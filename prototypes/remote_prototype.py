"""
Onlink-Clone: Remote Interface Prototype (v3.0)
- Fixed TypeError in tool execution
- Implemented universal task progress for all tools
- High-density world map dataset integration
"""
import eel
import os
import uuid
import threading
import time

class RemotePrototype:
    def __init__(self):
        self.local_ram = [
            {"id": "p1", "name": "Password_Breaker", "type": "cracker", "active": False},
            {"id": "p2", "name": "Log_Deleter", "type": "utility", "active": False},
            {"id": "p3", "name": "File_Copier", "type": "utility", "active": False},
            {"id": "p4", "name": "Trace_Tracker", "type": "security", "active": False},
            {"id": "p5", "name": "Proxy_Bypass", "type": "bypasser", "active": False},
        ]
        
        self.server = {
            "name": "Global Research Mainframe",
            "ip": "210.45.92.11",
            "is_unlocked": False,
            "security": {
                "proxy": {"level": 3, "active": True, "bypassed": False},
                "firewall": {"level": 2, "active": True, "bypassed": False},
                "monitor": {"level": 1, "active": True, "bypassed": False},
            },
            "files": [
                {"id": "f1", "name": "research_notes.doc", "size": 4, "type": "data", "blocks": [12, 13, 14, 15]},
                {"id": "f2", "name": "admin_keys.enc", "size": 2, "type": "data", "blocks": [45, 46]},
                {"id": "f3", "name": "sys_kernel.bin", "size": 8, "type": "tool", "blocks": [80, 81, 82, 83, 84, 85, 86, 87]},
            ],
            "logs": [
                {"time": "14:02", "from": "127.0.0.1", "action": "Connection routing established", "type": "routing"},
                {"time": "14:05", "from": "unknown", "action": "Unauthorized access attempt", "type": "hack"},
            ]
        }
        
        self.manifests = [
            {"id": "TRK-8821", "carrier": "Global Freight", "cargo": "GPU Crates", "origin": "Christchurch", "dest": "Dunedin", "value": 45000, "status": "IN_TRANSIT"},
            {"id": "TRK-9012", "carrier": "Apex Logistics", "cargo": "Medical Supplies", "origin": "London", "dest": "Paris", "value": 12000, "status": "IN_TRANSIT"},
        ]
        
        self.news = []
        self.companies = {
            "Global Freight": {"stock": 120.0},
            "Apex Logistics": {"stock": 95.0},
            "Aegis PMC": {"stock": 88.0}
        }

        self.active_tasks = []
        self.trace_active = False
        self.trace_progress = 0
        self.bounce_count = 5  # Simulating a connection routed through 5 nodes
        self.game_over = False
        self.game_over_reason = ""
        self._lock = threading.Lock()

    def get_state(self):
        with self._lock:
            # Check if Trace Tracker is active in RAM
            tracker = next((t for t in self.local_ram if t["name"] == "Trace_Tracker"), None)
            show_trace = tracker["active"] if tracker else False
            
            return {
                "local_ram": self.local_ram,
                "server": self.server,
                "tasks": self.active_tasks,
                "trace_active": self.trace_active,
                "trace_progress": self.trace_progress if show_trace else 0,
                "show_trace_warning": show_trace and self.trace_active,
                "bounce_count": self.bounce_count,
                "game_over": self.game_over,
                "game_over_reason": self.game_over_reason,
                "manifests": self.manifests,
                "news": self.news,
                "companies": self.companies
            }

    def hijack_shipment(self, manifest_id):
        with self._lock:
            manifest = next((m for m in self.manifests if m["id"] == manifest_id), None)
            if not manifest or manifest["status"] == "HIJACKED":
                return {"success": False, "msg": "TARGET INVALID"}
            
            manifest["status"] = "HIJACKED"
            
            # Ripple Effect
            carrier = manifest["carrier"]
            if carrier in self.companies:
                self.companies[carrier]["stock"] *= 0.85
            
            self.companies["Aegis PMC"]["stock"] *= 1.05
            
            self.news.append({
                "headline": f"HIJACKING: {manifest['cargo']} stolen near {manifest['dest']}",
                "body": f"Armed interceptors have stolen a shipment from {carrier}. Market shock expected."
            })
            return {"success": True}

    def toggle_tool(self, tool_id):
        with self._lock:
            for t in self.local_ram:
                if t["id"] == tool_id:
                    t["active"] = not t["active"]
                    return {"success": True, "active": t["active"]}
            return {"success": False}

    def start_hack(self, tool_name, target_type, target_id):
        with self._lock:
            if self.game_over:
                return {"success": False, "msg": "CONNECTION TERMINATED"}
                
            tool = next((t for t in self.local_ram if t["name"] == tool_name), None)
            if not tool or not tool["active"]:
                return {"success": False, "msg": f"ERROR: {tool_name} MUST BE RUNNING IN RAM"}

            if tool_name in ["Log_Deleter", "File_Copier"] and not self.server["is_unlocked"]:
                return {"success": False, "msg": "ACCESS DENIED: REMOTE PRIVILEGES REQUIRED"}

            # Start active trace on first hack attempt
            if not self.trace_active:
                self.trace_active = True
                threading.Thread(target=self._run_trace, daemon=True).start()

            task_id = str(uuid.uuid4())[:4]
            # Speed depends on tool type
            speed = 15 if tool_name == "Log_Deleter" else 8
            
            task = {
                "id": task_id, 
                "name": tool_name, 
                "target_type": target_type,
                "target_id": target_id, 
                "progress": 0, 
                "speed": speed
            }
            self.active_tasks.append(task)
            threading.Thread(target=self._run_task, args=(task_id,), daemon=True).start()
            return {"success": True, "task_id": task_id}

    def _run_trace(self):
        # Base trace speed: 10% per second for a direct 1-node connection
        # Tracing through more bounce nodes slows down the trace.
        trace_speed_per_sec = 10.0 / max(1, self.bounce_count)

        while self.trace_active and not self.game_over:
            time.sleep(1)
            with self._lock:
                self.trace_progress += trace_speed_per_sec
                if self.trace_progress >= 100:
                    self.trace_progress = 100
                    self.game_over = True
                    self.game_over_reason = "CONNECTION TRACED - SYSTEM DISAVOWED"
                    break

    def _run_task(self, task_id):
        while True:
            time.sleep(1)
            with self._lock:
                task = next((t for t in self.active_tasks if t["id"] == task_id), None)
                if not task: break
                
                task["progress"] += task["speed"]
                if task["progress"] >= 100:
                    task["progress"] = 100
                    # Handle completion
                    if task["target_type"] == "password":
                        self.server["is_unlocked"] = True
                    elif task["name"] == "Log_Deleter":
                        idx = int(task["target_id"])
                        if 0 <= idx < len(self.server["logs"]):
                            self.server["logs"].pop(idx)
                    elif task["name"] == "File_Copier":
                        fid = task["target_id"]
                        self.server["files"] = [f for f in self.server["files"] if f["id"] != fid]
                    
                    # Remove task after short delay so UI shows 100%
                    threading.Timer(1.0, self._cleanup_task, args=(task_id,)).start()
                    break

    def _cleanup_task(self, tid):
        with self._lock:
            self.active_tasks = [t for t in self.active_tasks if t["id"] != tid]

# --- Eel Bridge ---
proto = RemotePrototype()

@eel.expose
def get_remote_state(): return proto.get_state()

@eel.expose
def toggle_tool(tool_id): return proto.toggle_tool(tool_id)

@eel.expose
def execute_hack(tool_name, target_type, target_id):
    # Flattened arguments to avoid any JS object issues
    return proto.start_hack(str(tool_name), str(target_type), str(target_id))

@eel.expose
def hijack_shipment(manifest_id): return proto.hijack_shipment(manifest_id)

@eel.expose
def save_ip(ip):
    # Dummy function for standalone lab
    return {"success": True, "msg": f"IP {ip} added to known IPs."}

def start():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    eel.init('web')
    print("Launching Remote Interface Prototype v3.0...")
    eel.start('remote_prototype.html', size=(1250, 850))

if __name__ == "__main__":
    start()
