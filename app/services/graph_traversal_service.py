"""Graph Traversal Service: BFS and DFS algorithms with step snapshot recording."""
from __future__ import annotations

import time
from collections import deque
from typing import Any, Dict, List, Set

from app.services.graph_service import GraphService


class GraphTraversalService:
    def __init__(self, graph_service: Optional[GraphService] = None):
        self.graph = graph_service if graph_service is not None else GraphService()

    def bfs(self, start_id: int, target_id: Optional[int] = None) -> Dict[str, Any]:
        """Breadth-First Search traversal with unweighted hop metrics and step snapshots."""
        start_time = time.perf_counter()

        if start_id not in self.graph.places_by_id:
            return {"success": False, "error": "Start destination not found in graph."}

        queue: deque = deque([start_id])
        visited: Set[int] = {start_id}
        hop_distance: Dict[int, int] = {start_id: 0}
        parent: Dict[int, Optional[int]] = {start_id: None}
        traversal_order: List[int] = []

        steps: List[Dict[str, Any]] = []
        step_counter = 0

        steps.append({
            "step": step_counter,
            "action": "initialize",
            "current_node": start_id,
            "current_node_name": self.graph.places_by_id[start_id].name,
            "visited": list(visited),
            "queue": [self.graph.places_by_id[nid].name for nid in queue],
            "description": f"Initialized BFS queue at {self.graph.places_by_id[start_id].name} (hop level 0).",
        })

        while queue:
            u = queue.popleft()
            traversal_order.append(u)
            step_counter += 1

            steps.append({
                "step": step_counter,
                "action": "dequeue",
                "current_node": u,
                "current_node_name": self.graph.places_by_id[u].name,
                "hop_level": hop_distance[u],
                "visited": list(visited),
                "queue": [self.graph.places_by_id[nid].name for nid in queue],
                "description": f"Dequeued {self.graph.places_by_id[u].name} at hop level {hop_distance[u]}.",
            })

            if target_id is not None and u == target_id:
                break

            for v, _, _ in self.graph.get_neighbors(u):
                if v not in visited:
                    visited.add(v)
                    parent[v] = u
                    hop_distance[v] = hop_distance[u] + 1
                    queue.append(v)

                    step_counter += 1
                    steps.append({
                        "step": step_counter,
                        "action": "discover_neighbor",
                        "source": u,
                        "target": v,
                        "source_name": self.graph.places_by_id[u].name,
                        "target_name": self.graph.places_by_id[v].name,
                        "hop_level": hop_distance[v],
                        "visited": list(visited),
                        "queue": [self.graph.places_by_id[nid].name for nid in queue],
                        "description": f"Discovered neighbor {self.graph.places_by_id[v].name} via ({self.graph.places_by_id[u].name} -> {self.graph.places_by_id[v].name}), hop level {hop_distance[v]}.",
                    })

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Path reconstruction if target was specified
        target_path: List[int] = []
        if target_id is not None and target_id in visited:
            curr = target_id
            while curr is not None:
                target_path.append(curr)
                curr = parent[curr]
            target_path.reverse()

        return {
            "success": True,
            "algorithm": "Breadth-First Search (BFS)",
            "start_id": start_id,
            "target_id": target_id,
            "traversal_order": traversal_order,
            "visited_order": traversal_order,
            "traversal_nodes": [self.graph.places_by_id[nid].to_dict() for nid in traversal_order],
            "hop_distances": {nid: hop_distance.get(nid, -1) for nid in traversal_order},
            "unweighted_path": target_path,
            "unweighted_hop_count": len(target_path) - 1 if target_path else None,
            "steps": steps,
            "elapsed_ms": round(elapsed_ms, 3),
            "complexity_time": "O(|V| + |E|)",
            "complexity_space": "O(|V|)",
            "explanation": "BFS explores vertices in concentric circles by unweighted hop count. Notice that BFS does NOT minimize road distance or travel time on weighted graphs.",
        }

    def dfs(self, start_id: int) -> Dict[str, Any]:
        """Depth-First Search traversal with discovery times and step snapshots."""
        start_time = time.perf_counter()

        if start_id not in self.graph.places_by_id:
            return {"success": False, "error": "Start destination not found in graph."}

        visited: Set[int] = set()
        traversal_order: List[int] = []
        steps: List[Dict[str, Any]] = []
        step_counter = 0

        def _dfs_visit(u: int):
            nonlocal step_counter
            visited.add(u)
            traversal_order.append(u)
            step_counter += 1

            steps.append({
                "step": step_counter,
                "action": "visit_node",
                "current_node": u,
                "current_node_name": self.graph.places_by_id[u].name,
                "visited": list(visited),
                "description": f"DFS deeply exploring {self.graph.places_by_id[u].name}.",
            })

            for v, _, _ in self.graph.get_neighbors(u):
                if v not in visited:
                    step_counter += 1
                    steps.append({
                        "step": step_counter,
                        "action": "traverse_edge",
                        "source": u,
                        "target": v,
                        "source_name": self.graph.places_by_id[u].name,
                        "target_name": self.graph.places_by_id[v].name,
                        "visited": list(visited),
                        "description": f"Advancing along tree edge ({self.graph.places_by_id[u].name} -> {self.graph.places_by_id[v].name}).",
                    })
                    _dfs_visit(v)

        _dfs_visit(start_id)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "success": True,
            "algorithm": "Depth-First Search (DFS)",
            "start_id": start_id,
            "traversal_order": traversal_order,
            "visited_order": traversal_order,
            "traversal_nodes": [self.graph.places_by_id[nid].to_dict() for nid in traversal_order],
            "visited_count": len(visited),
            "unreachable_count": len(self.graph.places_by_id) - len(visited),
            "steps": steps,
            "elapsed_ms": round(elapsed_ms, 3),
            "complexity_time": "O(|V| + |E|)",
            "complexity_space": "O(|V|)",
            "explanation": "DFS explores along each branch as deeply as possible before backtracking. It is used to discover connected components, cycle detection, and topological reachability.",
        }

    def breadth_first_search(self, start_id: int, target_id: Optional[int] = None) -> Dict[str, Any]:
        """Alias for bfs."""
        return self.bfs(start_id, target_id=target_id)

    def depth_first_search(self, start_id: int) -> Dict[str, Any]:
        """Alias for dfs."""
        return self.dfs(start_id)
