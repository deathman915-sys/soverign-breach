
from core.game_state import GameState, VFSFile
from core.hardware_engine import HardwareEngine
from core.apps.hardware import HardwareApp

def test_hardware_app_returns_vfs_block_mapping():
    state = GameState()
    state.gateway.storage_capacity = 64
    # Add a file
    f = VFSFile(filename="secret.dat", size_gq=4)
    state.vfs.files.append(f)
    
    # Rebuild map
    HardwareEngine.rebuild_vfs_map(state)
    
    assert len(f.blocks) == 4
    
    app = HardwareApp(state)
    data = app.init()
    
    assert "vfs_map" in data
    # vfs_map should be a list of blocks, each indicating which file owns it
    assert len(data["vfs_map"]) == 64
    # Blocks 0-3 should belong to secret.dat
    for i in range(4):
        assert data["vfs_map"][i] == "secret.dat"
    # Block 4 should be empty
    assert data["vfs_map"][4] is None
