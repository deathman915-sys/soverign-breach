"""
Onlink-Clone: Store & Upgrade Prototype

Demonstrates the purchasing loop for:
1. Software (added to VFS)
2. Gateways (full spec upgrade)
3. Cooling & PSU (modular hardware upgrades)
"""
import eel
import os
import sys

# Ensure core is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.game_state import GameState
from core import store_engine

class StorePrototype:
    def __init__(self):
        self.state = GameState()
        self.state.player.balance = 50000  # Give player some starting cash for testing

    def get_state(self):
        return {
            "player": {
                "balance": self.state.player.balance
            },
            "gateway": {
                "name": self.state.gateway.name,
                "cpu": self.state.gateway.cpu_speed,
                "modem": self.state.gateway.modem_speed,
                "memory": self.state.gateway.memory_size,
                "cooling": self.state.gateway.cooling_power,
                "psu": self.state.gateway.psu_capacity
            },
            "vfs": [f.filename for f in self.state.vfs.files],
            "catalogs": {
                "software": store_engine.get_software_catalog(),
                "gateways": store_engine.get_hardware_catalog(),
                "cooling": store_engine.get_cooling_catalog(),
                "psu": store_engine.get_psu_catalog()
            }
        }

    def buy_software(self, name, version):
        res = store_engine.buy_software(self.state, name, version)
        return res

    def buy_gateway(self, name):
        res = store_engine.buy_gateway(self.state, name)
        return res

    def buy_cooling(self, name):
        res = store_engine.buy_cooling(self.state, name)
        return res

    def buy_psu(self, name):
        res = store_engine.buy_psu(self.state, name)
        return res

proto = StorePrototype()

@eel.expose
def get_store_state(): return proto.get_state()

@eel.expose
def buy_software(name, version): return proto.buy_software(name, version)

@eel.expose
def buy_gateway(name): return proto.buy_gateway(name)

@eel.expose
def buy_cooling(name): return proto.buy_cooling(name)

@eel.expose
def buy_psu(name): return proto.buy_psu(name)

def start():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    web_dir = os.path.join(base_dir, 'web')
    eel.init(web_dir)
    print("Launching Store Prototype...")
    eel.start('store_prototype.html', size=(1100, 850))

if __name__ == "__main__":
    start()
