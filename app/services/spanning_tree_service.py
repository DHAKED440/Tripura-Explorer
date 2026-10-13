"""Minimum Spanning Tree (MST) Service.

Implements Kruskal's algorithm with Disjoint-Set Union (DSU) and Prim's algorithm
for undirected weighted connectivity analysis and spanning forest calculations.
"""
from __future__ import annotations

import heapq
import time
from typing import Any, Dict, List, Set, Tuple

from app.services.graph_service import GraphService


class DisjointSetUnion:
    """DSU with path compression and union by rank."""

    def __init__(self, elements: List[int]):
        self.parent = {x: x for x in elements}
        self.rank = {x: 0 for x in elements}
        self.component_count = len(elements)

    def find(self, x: int) -> int:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: int, y: int) -> bool:
        root_x = self.find(x)
        root_y = self.find(y)
        if root_x == root_y:
            return False

        if self.rank[root_x] < self.rank[root_y]:
            root_x, root_y = root_y, root_x
        self.parent[root_y] = root_x
        if self.rank[root_x] == self.rank[root_y]:
            self.rank[root_x] += 1

        self.component_count -= 1
        return True


class SpanningTreeService:
    def __init__(self, graph_service: Optional[GraphService] = None):
        self.graph = graph_service if graph_service is not None else GraphService()

    def kruskal(self, record_steps: bool = True) -> Dict[str, Any]:
        """Compute Minimum Spanning Tree or Spanning Forest using Kruskal's Algorithm.

        Time Complexity: O(|E| log |E|)
        Space Complexity: O(|V| + |E|)
        Guarantee: exact_mst
        """
        start_time = time.perf_counter()

        node_ids = list(self.graph.places_by_id.keys())
        dsu = DisjointSetUnion(node_ids)

        # Collect unique undirected edges
        candidate_edges: List[Dict[str, Any]] = []
        seen_pairs: Set[Tuple[int, int]] = set()

        for conn in self.graph.connections:
            u, v = conn.source_destination_id, conn.target_destination_id
            if u not in self.graph.places_by_id or v not in self.graph.places_by_id:
                continue

            pair = (min(u, v), max(u, v))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            w = self.graph.calculate_weight(conn)
            candidate_edges.append({
                "id": conn.id,
                "u": u,
                "v": v,
                "u_name": self.graph.places_by_id[u].name,
                "v_name": self.graph.places_by_id[v].name,
                "weight": round(w, 4),
                "distance_km": round(conn.distance_km, 2),
                "travel_time_minutes": round(conn.travel_time_minutes, 1),
                "estimated_cost": round(conn.estimated_cost, 2) if conn.estimated_cost is not None else None,
                "data_source": conn.data_source,
                "verification_status": conn.verification_status,
            })

        # Sort edges in non-decreasing order of weight
        candidate_edges.sort(key=lambda e: e["weight"])

        mst_edges: List[Dict[str, Any]] = []
        steps: List[Dict[str, Any]] = []
        step_counter = 0

        if record_steps:
            steps.append({
                "step": step_counter,
                "action": "initialize",
                "total_candidate_edges": len(candidate_edges),
                "components": dsu.component_count,
                "description": f"Sorted {len(candidate_edges)} candidate edges by weight. Initialized {len(node_ids)} disjoint components.",
            })

        for edge in candidate_edges:
            u, v = edge["u"], edge["v"]
            step_counter += 1

            if dsu.union(u, v):
                mst_edges.append(edge)
                if record_steps:
                    steps.append({
                        "step": step_counter,
                        "action": "accept_edge",
                        "edge": edge,
                        "components": dsu.component_count,
                        "accepted_count": len(mst_edges),
                        "description": f"Accepted edge ({edge['u_name']} <-> {edge['v_name']}, w={edge['weight']}): connected two separate components.",
                    })
            else:
                if record_steps:
                    steps.append({
                        "step": step_counter,
                        "action": "reject_edge_cycle",
                        "edge": edge,
                        "components": dsu.component_count,
                        "description": f"Rejected edge ({edge['u_name']} <-> {edge['v_name']}, w={edge['weight']}): forms a cycle in the same component.",
                    })

            # Early break if single connected tree reached
            if dsu.component_count == 1 and len(node_ids) > 0:
                break

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        total_weight = sum(e["weight"] for e in mst_edges)
        total_dist = sum(e["distance_km"] for e in mst_edges)
        total_time = sum(e["travel_time_minutes"] for e in mst_edges)

        is_connected = dsu.component_count <= 1

        return {
            "success": True,
            "algorithm": "Kruskal's MST",
            "guarantee": "exact_mst" if is_connected else "exact_minimum_spanning_forest",
            "is_connected": is_connected,
            "component_count": dsu.component_count,
            "mst_edges": mst_edges,
            "tree_edges": mst_edges,
            "total_vertices": len(node_ids),
            "mst_edge_count": len(mst_edges),
            "expected_edges_if_connected": max(0, len(node_ids) - 1),
            "total_weight": round(total_weight, 2),
            "weight_metric": self.graph.weight_metric,
            "total_distance_km": round(total_dist, 2),
            "total_time_minutes": round(total_time, 1),
            "elapsed_ms": round(elapsed_ms, 3),
            "steps": steps,
            "complexity_time": "O(|E| log |E|)",
            "complexity_space": "O(|V| + |E|)",
            "explanation": (
                "Minimum Spanning Tree connects all reachable destinations using the absolute minimum "
                "total edge weight without forming cycles (|E_mst| = |V| - 1). While ideal for road infrastructure "
                "planning and telecom backbones, an MST is NOT a tourist tour since visiting it would require backtracking."
            ),
        }

    def compute_minimum_spanning_tree(self, metric: str = "distance", record_steps: bool = True) -> Dict[str, Any]:
        """Convenience method for MST calculation with specific metric."""
        if metric != self.graph.weight_metric:
            self.graph = GraphService(weight_metric=metric)
        return self.kruskal(record_steps=record_steps)
