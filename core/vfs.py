"""
Onlink-Clone: Virtual File System

Manages the player's gateway memory as a flat block list.
All reads/writes go through GameState.vfs — no lateral core imports.
"""
from __future__ import annotations

from typing import Optional

from core.game_state import GameState, SoftwareType, VFSFile


class VirtualFileSystem:
    """
    Stateless VFS operations.  Every method takes a GameState reference
    so there are no circular imports.
    """

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    @staticmethod
    def list_files(state: GameState) -> list[VFSFile]:
        """Return all files on the gateway."""
        return list(state.vfs.files)

    @staticmethod
    def find_file(state: GameState, filename: str) -> Optional[VFSFile]:
        """Find a file by exact name."""
        for f in state.vfs.files:
            if f.filename == filename:
                return f
        return None

    @staticmethod
    def find_software(state: GameState, tool_name: str) -> Optional[VFSFile]:
        """Find the highest-version software matching a tool name."""
        matches = [
            f for f in state.vfs.files
            if f.software_type != SoftwareType.NONE
            and tool_name.lower() in f.filename.lower()
        ]
        if not matches:
            return None
        return max(matches, key=lambda f: f.version)

    @staticmethod
    def has_space(state: GameState, size_gq: int) -> bool:
        """Check if there's enough free memory."""
        return state.vfs.free_gq >= size_gq

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------
    @staticmethod
    def store_file(state: GameState, vfs_file: VFSFile) -> bool:
        """
        Store a file in memory.  Returns False if not enough space.
        """
        if not VirtualFileSystem.has_space(state, vfs_file.size_gq):
            return False
        state.vfs.files.append(vfs_file)
        return True

    @staticmethod
    def delete_file(state: GameState, filename: str) -> bool:
        """Delete a file by name.  Returns False if not found."""
        for i, f in enumerate(state.vfs.files):
            if f.filename == filename:
                state.vfs.files.pop(i)
                return True
        return False

    @staticmethod
    def defrag(state: GameState) -> int:
        """
        Defragment memory.

        In our model, fragmentation means duplicate filename entries
        (from partial overwrites) or zero-size ghosts.  Defrag merges
        them and returns the GigaQuads reclaimed.

        In the real Uplink, defrag compacts scattered memory blocks.
        We simulate this by removing zero-size files and deduplicating.
        """
        before = state.vfs.used_gq

        # Remove zero-size files
        state.vfs.files = [f for f in state.vfs.files if f.size_gq > 0]

        # Deduplicate: keep the highest version of each filename
        seen: dict[str, VFSFile] = {}
        for f in state.vfs.files:
            if f.filename not in seen or f.version > seen[f.filename].version:
                seen[f.filename] = f
        state.vfs.files = list(seen.values())

        after = state.vfs.used_gq
        return max(0, before - after)

    # ------------------------------------------------------------------
    # Capacity management
    # ------------------------------------------------------------------
    @staticmethod
    def upgrade_memory(state: GameState, new_total_gq: int) -> None:
        """Set the total memory capacity (hardware upgrade)."""
        state.vfs.total_memory_gq = new_total_gq
        state.gateway.storage_capacity = new_total_gq
