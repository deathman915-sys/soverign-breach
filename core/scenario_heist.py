"""
Onlink-Clone: Heist Scenario Initializer

Hardcodes exactly 4 nodes: Localhost, InterNIC, Proxy, and Target.
Sets up the initial files and passwords for the MVP loop.
"""
from core.game_state import GameState, Computer, NodeType, DataFile

def init_heist_scenario(state: GameState):
    state.computers = {}
    
    # 1. Localhost (Player Gateway) - Christchurch, NZ
    localhost = Computer(
        ip="127.0.0.1",
        name="Localhost",
        computer_type=NodeType.GATEWAY,
        listed=True,
        x=172.6306, y=-43.5320
    )
    state.computers[localhost.ip] = localhost
    state.player.localhost_ip = localhost.ip
    state.gateway.storage_capacity = 10
    state.vfs.total_memory_gq = 10 # Set memory on the gateway state instead
    
    # 2. InterNIC - New York, US
    internic = Computer(
        ip="100.100.100.1",
        name="InterNIC",
        computer_type=NodeType.INTERNIC,
        listed=True,
        x=-74.0060, y=40.7128
    )
    state.computers[internic.ip] = internic
    
    # 3. Public Proxy - London, UK
    proxy = Computer(
        ip="200.200.200.2",
        name="Public Proxy",
        computer_type=NodeType.PUBLIC_SERVER,
        listed=True,
        x=-0.1278, y=51.5074
    )
    state.computers[proxy.ip] = proxy
    
    # 4. Target Server - Tokyo, JP
    target = Computer(
        ip="4.4.4.4",
        name="Top Secret Server",
        computer_type=NodeType.INTERNAL_SRV,
        listed=True,
        x=139.6503, y=35.6762
    )
    # Add secret file using the correct DataFile class
    secret_file = DataFile(filename="secret.dat", size=2, file_type=1)
    target.files = [secret_file]
    state.computers[target.ip] = target
    
    # Init known IPs
    state.player.known_ips = [localhost.ip, internic.ip, proxy.ip, target.ip]
