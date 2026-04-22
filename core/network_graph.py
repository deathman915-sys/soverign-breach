"""
Onlink-Clone: Network Graph

Weighted directed graph for the global network.
Provides Dijkstra pathfinding on inverse-trace-speed for optimal bounce chains.
"""
from __future__ import annotations

import heapq
from typing import Optional

from core.game_state import BounceChain, GameState, NetNode


class NetworkGraph:
    """
    Operations on the network stored in GameState.nodes.

    This class is stateless — it reads/writes exclusively through
    the GameState reference passed to each method.
    """

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------
    @staticmethod
    def add_node(state: GameState, node: NetNode) -> None:
        """Register a node in the network."""
        state.nodes[node.ip] = node

    @staticmethod
    def remove_node(state: GameState, ip: str) -> None:
        """Remove a node and all links pointing to it."""
        if ip in state.nodes:
            # Remove inbound links
            for other in state.nodes.values():
                if ip in other.links:
                    other.links.remove(ip)
            del state.nodes[ip]

    @staticmethod
    def add_link(state: GameState, ip_a: str, ip_b: str) -> None:
        """Create a bidirectional link between two nodes."""
        if ip_a in state.nodes and ip_b in state.nodes:
            if ip_b not in state.nodes[ip_a].links:
                state.nodes[ip_a].links.append(ip_b)
            if ip_a not in state.nodes[ip_b].links:
                state.nodes[ip_b].links.append(ip_a)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    @staticmethod
    def get_node(state: GameState, ip: str) -> Optional[NetNode]:
        return state.nodes.get(ip)

    @staticmethod
    def nodes_in_region(state: GameState, region: str) -> list[NetNode]:
        return [n for n in state.nodes.values() if n.region == region]

    @staticmethod
    def online_nodes(state: GameState) -> list[NetNode]:
        return [n for n in state.nodes.values() if n.is_online]

    # ------------------------------------------------------------------
    # Pathfinding
    # ------------------------------------------------------------------
    @staticmethod
    def shortest_path(state: GameState, src_ip: str, dst_ip: str) -> list[str]:
        """
        Dijkstra on inverse trace_speed.

        We WANT to route through nodes that are slow to trace (high trace_speed),
        so weight = 1 / trace_speed.  Lower total weight = better cover.
        Nodes with trace_speed <= 0 (no trace) get weight 0 (free hops).
        Offline nodes are excluded.
        """
        nodes = state.nodes
        if src_ip not in nodes or dst_ip not in nodes:
            return []

        INF = float("inf")
        dist: dict[str, float] = {ip: INF for ip in nodes}
        prev: dict[str, Optional[str]] = {ip: None for ip in nodes}
        dist[src_ip] = 0.0

        # (distance, ip)
        heap: list[tuple[float, str]] = [(0.0, src_ip)]

        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue
            if u == dst_ip:
                break

            node_u = nodes[u]
            for v_ip in node_u.links:
                v_node = nodes.get(v_ip)
                if v_node is None or not v_node.is_online:
                    continue

                # Weight: prefer high trace_speed → low weight
                if v_node.trace_speed > 0:
                    w = 1.0 / v_node.trace_speed
                else:
                    w = 0.0  # untraceable node = free hop

                alt = dist[u] + w
                if alt < dist[v_ip]:
                    dist[v_ip] = alt
                    prev[v_ip] = u
                    heapq.heappush(heap, (alt, v_ip))

        # Reconstruct path
        if dist[dst_ip] == INF:
            return []

        path: list[str] = []
        cur: Optional[str] = dst_ip
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        return path

    # ------------------------------------------------------------------
    # Bounce helpers
    # ------------------------------------------------------------------
    @staticmethod
    def build_bounce_chain(state: GameState, hop_ips: list[str]) -> BounceChain:
        """Validate and build a BounceChain from a list of IPs."""
        valid = [ip for ip in hop_ips if ip in state.nodes and state.nodes[ip].is_online]
        return BounceChain(hops=valid)

    @staticmethod
    def trace_time(state: GameState, chain: BounceChain) -> float:
        """Total seconds for a trace to traverse the chain."""
        total = 0.0
        for ip in chain.hops:
            node = state.nodes.get(ip)
            if node and node.trace_speed > 0:
                total += node.trace_speed
        return total

    # ------------------------------------------------------------------
    # Blackouts
    # ------------------------------------------------------------------
    @staticmethod
    def blackout_region(state: GameState, region: str) -> list[str]:
        """
        Set is_online=False for all nodes in a region.
        Returns list of affected IPs.
        """
        affected = []
        for node in state.nodes.values():
            if node.region == region and node.is_online:
                node.is_online = False
                affected.append(node.ip)
        return affected

    @staticmethod
    def restore_region(state: GameState, region: str) -> None:
        """Bring a region back online."""
        for node in state.nodes.values():
            if node.region == region:
                node.is_online = True
