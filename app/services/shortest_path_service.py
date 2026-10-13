"""Shortest Path Service: Dijkstra's Algorithm and A* Search.

Implements optimal shortest-path graph search with step-by-step state snapshot
recording for visual laboratory animation and complexity analysis.
"""
from __future__ import annotations

import heapq
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from app.services.destination_service import haversine_km
from app.services.graph_service import GraphService


class ShortestPathService:
    def __init__(self, graph_service: Optional[GraphService] = None):
        self.graph = graph_service if graph_service is not None else GraphService()

    def dijkstra(
        self,
        start_id: int,
        target_id: int,
        record_steps: bool = True,
    ) -> Dict[str, Any]:
        """Find optimal shortest path between start_id and target_id using Dijkstra's algorithm.

        Time Complexity: O((|V| + |E|) log |V|) with binary heap.
        Space Complexity: O(|V| + |E|).
        Guarantee: exact_shortest_path (for non-negative edge weights).
        """
        start_time = time.perf_counter()

        if start_id not in self.graph.places_by_id or target_id not in self.graph.places_by_id:
            return {
                "success": False,
                "error": "Start or target destination does not exist in the graph.",
                "path": [],
                "total_weight": float("inf"),
            }

        # distances[node] = shortest known distance from start_id
        distances: Dict[int, float] = {node_id: float("inf") for node_id in self.graph.places_by_id}
        distances[start_id] = 0.0

        # predecessor map for path reconstruction
        predecessors: Dict[int, Optional[int]] = {node_id: None for node_id in self.graph.places_by_id}

        # Priority queue stores tuples: (current_distance, node_id)
        pq: List[Tuple[float, int]] = [(0.0, start_id)]
        visited: Set[int] = set()

        steps: List[Dict[str, Any]] = []
        step_counter = 0

        if record_steps:
            steps.append({
                "step": step_counter,
                "action": "initialize",
                "current_node": start_id,
                "current_node_name": self.graph.places_by_id[start_id].name,
                "visited": list(visited),
                "tentative_distances": {nid: round(d, 2) for nid, d in distances.items() if d < float("inf")},
                "queue": [(round(d, 2), nid, self.graph.places_by_id[nid].name) for d, nid in sorted(pq)],
                "description": f"Initialized Dijkstra search at {self.graph.places_by_id[start_id].name} with distance 0.",
            })

        explored_count = 0

        while pq:
            curr_dist, u = heapq.heappop(pq)

            if u in visited:
                continue

            visited.add(u)
            explored_count += 1

            if record_steps:
                step_counter += 1
                steps.append({
                    "step": step_counter,
                    "action": "visit_node",
                    "current_node": u,
                    "current_node_name": self.graph.places_by_id[u].name,
                    "visited": list(visited),
                    "tentative_distances": {nid: round(d, 2) for nid, d in distances.items() if d < float("inf")},
                    "queue": [(round(d, 2), nid, self.graph.places_by_id[nid].name) for d, nid in sorted(pq)],
                    "description": f"Extracted vertex {self.graph.places_by_id[u].name} with minimum tentative weight {round(curr_dist, 2)}.",
                })

            # Early exit if we reached target
            if u == target_id:
                break

            # Relax edges to all neighbors
            for v, weight, edge_info in self.graph.get_neighbors(u):
                if v not in visited:
                    new_dist = curr_dist + weight
                    if new_dist < distances[v]:
                        distances[v] = new_dist
                        predecessors[v] = u
                        heapq.heappush(pq, (new_dist, v))

                        if record_steps:
                            step_counter += 1
                            steps.append({
                                "step": step_counter,
                                "action": "relax_edge",
                                "source": u,
                                "target": v,
                                "source_name": self.graph.places_by_id[u].name,
                                "target_name": self.graph.places_by_id[v].name,
                                "edge_weight": round(weight, 2),
                                "new_distance": round(new_dist, 2),
                                "visited": list(visited),
                                "tentative_distances": {nid: round(d, 2) for nid, d in distances.items() if d < float("inf")},
                                "queue": [(round(d, 2), nid, self.graph.places_by_id[nid].name) for d, nid in sorted(pq)],
                                "description": f"Relaxed edge ({self.graph.places_by_id[u].name} -> {self.graph.places_by_id[v].name}): updated tentative weight to {round(new_dist, 2)}.",
                            })

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Check reachability
        if distances[target_id] == float("inf"):
            return {
                "success": False,
                "reachable": False,
                "error": f"No supported path exists in the current network from {self.graph.places_by_id[start_id].name} to {self.graph.places_by_id[target_id].name}.",
                "path": [],
                "total_weight": float("inf"),
                "explored_nodes_count": explored_count,
                "steps": steps,
                "elapsed_ms": round(elapsed_ms, 3),
                "algorithm": "Dijkstra",
                "guarantee": "no_feasible_route",
            }

        # Reconstruct path
        path: List[int] = []
        curr = target_id
        while curr is not None:
            path.append(curr)
            curr = predecessors[curr]
        path.reverse()

        # Build path details
        path_nodes = [self.graph.places_by_id[nid].to_dict() for nid in path]
        legs = []
        total_dist_km = 0.0
        total_time_mins = 0.0
        total_cost_inr = 0.0

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge_data = self.graph.edges_by_pair.get((u, v))
            if edge_data:
                legs.append(edge_data)
                total_dist_km += edge_data.get("distance_km", 0.0)
                total_time_mins += edge_data.get("travel_time_minutes", 0.0)
                if edge_data.get("estimated_cost") is not None:
                    total_cost_inr += edge_data["estimated_cost"]
                else:
                    total_cost_inr += edge_data.get("distance_km", 0.0) * 12.0

        return {
            "success": True,
            "reachable": True,
            "start_id": start_id,
            "target_id": target_id,
            "path_ids": path,
            "path_node_ids": path,
            "path_nodes": path_nodes,
            "legs": legs,
            "total_weight": round(distances[target_id], 2),
            "weight_metric": self.graph.weight_metric,
            "total_distance_km": round(total_dist_km, 2),
            "total_time_minutes": round(total_time_mins, 1),
            "total_estimated_cost": round(total_cost_inr, 2),
            "explored_nodes_count": explored_count,
            "total_nodes_in_graph": len(self.graph.places_by_id),
            "elapsed_ms": round(elapsed_ms, 3),
            "steps": steps,
            "algorithm": "Dijkstra",
            "guarantee": "exact_shortest_path",
            "complexity_time": "O((|V| + |E|) log |V|)",
            "complexity_space": "O(|V| + |E|)",
        }

    def astar(
        self,
        start_id: int,
        target_id: int,
        record_steps: bool = True,
    ) -> Dict[str, Any]:
        """Find optimal shortest path between start_id and target_id using A* search.

        Evaluation function: f(n) = g(n) + h(n).
        Heuristic h(n):
          - For distance: straight-line Great Circle Haversine distance (admissible).
          - For travel time: Haversine distance / 80 km/h * 60 minutes (admissible lower bound).
          - For cost: Haversine distance * Rs 8.0/km (admissible lower bound).
        Guarantee: exact_shortest_path (when heuristic is admissible and consistent).
        """
        start_time = time.perf_counter()

        if start_id not in self.graph.places_by_id or target_id not in self.graph.places_by_id:
            return {
                "success": False,
                "error": "Start or target destination does not exist in the graph.",
                "path": [],
                "total_weight": float("inf"),
            }

        target_place = self.graph.places_by_id[target_id]

        def heuristic(node_id: int) -> float:
            node_place = self.graph.places_by_id[node_id]
            if not node_place.has_coordinates or not target_place.has_coordinates:
                return 0.0

            straight_km = haversine_km(
                node_place.latitude, node_place.longitude,
                target_place.latitude, target_place.longitude
            )

            if self.graph.weight_metric == "distance":
                return straight_km
            elif self.graph.weight_metric == "time":
                # Max reasonable highway speed in Tripura: 80 km/h -> time in minutes
                return (straight_km / 80.0) * 60.0
            elif self.graph.weight_metric == "cost":
                # Minimum possible cost rate per km
                return straight_km * 8.0
            elif self.graph.weight_metric == "balanced":
                d_norm = straight_km / self.graph.max_distance
                t_norm = ((straight_km / 80.0) * 60.0) / self.graph.max_time
                c_norm = (straight_km * 8.0) / self.graph.max_cost
                return self.graph.alpha * d_norm + self.graph.beta * t_norm + self.graph.gamma * c_norm
            return 0.0

        g_score: Dict[int, float] = {nid: float("inf") for nid in self.graph.places_by_id}
        g_score[start_id] = 0.0

        f_score: Dict[int, float] = {nid: float("inf") for nid in self.graph.places_by_id}
        f_score[start_id] = heuristic(start_id)

        predecessors: Dict[int, Optional[int]] = {nid: None for nid in self.graph.places_by_id}

        # Priority queue stores: (f_score, g_score, node_id)
        open_set: List[Tuple[float, float, int]] = [(f_score[start_id], 0.0, start_id)]
        open_set_hash: Set[int] = {start_id}
        closed_set: Set[int] = set()

        steps: List[Dict[str, Any]] = []
        step_counter = 0

        if record_steps:
            steps.append({
                "step": step_counter,
                "action": "initialize",
                "current_node": start_id,
                "current_node_name": self.graph.places_by_id[start_id].name,
                "visited": list(closed_set),
                "g_score": {start_id: 0.0},
                "h_score": {start_id: round(f_score[start_id], 2)},
                "f_score": {start_id: round(f_score[start_id], 2)},
                "description": f"Initialized A* search with h({self.graph.places_by_id[start_id].name}) = {round(f_score[start_id], 2)}.",
            })

        explored_count = 0

        while open_set:
            current_f, current_g, u = heapq.heappop(open_set)
            open_set_hash.discard(u)

            if u in closed_set:
                continue

            closed_set.add(u)
            explored_count += 1

            if record_steps:
                step_counter += 1
                steps.append({
                    "step": step_counter,
                    "action": "visit_node",
                    "current_node": u,
                    "current_node_name": self.graph.places_by_id[u].name,
                    "g": round(current_g, 2),
                    "h": round(heuristic(u), 2),
                    "f": round(current_f, 2),
                    "visited": list(closed_set),
                    "description": f"Visiting {self.graph.places_by_id[u].name} with f = g({round(current_g, 2)}) + h({round(heuristic(u), 2)}) = {round(current_f, 2)}.",
                })

            if u == target_id:
                break

            for v, weight, edge_info in self.graph.get_neighbors(u):
                if v in closed_set:
                    continue

                tentative_g = g_score[u] + weight

                if tentative_g < g_score[v]:
                    predecessors[v] = u
                    g_score[v] = tentative_g
                    h_val = heuristic(v)
                    f_score[v] = tentative_g + h_val

                    if v not in open_set_hash:
                        heapq.heappush(open_set, (f_score[v], tentative_g, v))
                        open_set_hash.add(v)

                    if record_steps:
                        step_counter += 1
                        steps.append({
                            "step": step_counter,
                            "action": "evaluate_neighbor",
                            "source": u,
                            "target": v,
                            "source_name": self.graph.places_by_id[u].name,
                            "target_name": self.graph.places_by_id[v].name,
                            "edge_weight": round(weight, 2),
                            "g": round(tentative_g, 2),
                            "h": round(h_val, 2),
                            "f": round(f_score[v], 2),
                            "description": f"Discovered path to {self.graph.places_by_id[v].name}: g={round(tentative_g, 2)}, h={round(h_val, 2)}, f={round(f_score[v], 2)}.",
                        })

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        if g_score[target_id] == float("inf"):
            return {
                "success": False,
                "reachable": False,
                "error": f"No supported path exists in the current network from {self.graph.places_by_id[start_id].name} to {self.graph.places_by_id[target_id].name}.",
                "path": [],
                "total_weight": float("inf"),
                "explored_nodes_count": explored_count,
                "steps": steps,
                "elapsed_ms": round(elapsed_ms, 3),
                "algorithm": "A* Search",
                "guarantee": "no_feasible_route",
            }

        # Path reconstruction
        path = []
        curr = target_id
        while curr is not None:
            path.append(curr)
            curr = predecessors[curr]
        path.reverse()

        path_nodes = [self.graph.places_by_id[nid].to_dict() for nid in path]
        legs = []
        total_dist_km = 0.0
        total_time_mins = 0.0
        total_cost_inr = 0.0

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge_data = self.graph.edges_by_pair.get((u, v))
            if edge_data:
                legs.append(edge_data)
                total_dist_km += edge_data.get("distance_km", 0.0)
                total_time_mins += edge_data.get("travel_time_minutes", 0.0)
                if edge_data.get("estimated_cost") is not None:
                    total_cost_inr += edge_data["estimated_cost"]
                else:
                    total_cost_inr += edge_data.get("distance_km", 0.0) * 12.0

        # Run Dijkstra baseline to compare explored count
        dijkstra_res = self.dijkstra(start_id, target_id, record_steps=False)

        return {
            "success": True,
            "reachable": True,
            "start_id": start_id,
            "target_id": target_id,
            "path_ids": path,
            "path_node_ids": path,
            "path_nodes": path_nodes,
            "legs": legs,
            "total_weight": round(g_score[target_id], 2),
            "weight_metric": self.graph.weight_metric,
            "total_distance_km": round(total_dist_km, 2),
            "total_time_minutes": round(total_time_mins, 1),
            "total_estimated_cost": round(total_cost_inr, 2),
            "explored_nodes_count": explored_count,
            "total_nodes_in_graph": len(self.graph.places_by_id),
            "heuristic_type": f"Admissible Haversine ({self.graph.weight_metric})",
            "elapsed_ms": round(elapsed_ms, 3),
            "steps": steps,
            "algorithm": "A* Search",
            "guarantee": "exact_shortest_path",
            "comparison": {
                "dijkstra_explored_count": dijkstra_res.get("explored_nodes_count", 0),
                "astar_explored_count": explored_count,
                "node_reduction_pct": round(
                    max(0, (dijkstra_res.get("explored_nodes_count", 0) - explored_count)
                    / max(1, dijkstra_res.get("explored_nodes_count", 1))) * 100, 1
                ),
                "weights_match": abs(dijkstra_res.get("total_weight", 0) - round(g_score[target_id], 2)) < 1e-4,
            },
            "complexity_time": "O((|V| + |E|) log |V|) worst case, directed by h(n)",
            "complexity_space": "O(|V| + |E|)",
        }

    def find_shortest_path(self, start_id: int, target_id: int, metric: str = "time", record_steps: bool = True) -> Dict[str, Any]:
        """Convenience method for Dijkstra shortest path with custom weight metric."""
        if metric != self.graph.weight_metric:
            self.graph = GraphService(weight_metric=metric)
        return self.dijkstra(start_id, target_id, record_steps=record_steps)

    def find_astar_path(self, start_id: int, target_id: int, metric: str = "distance", record_steps: bool = True) -> Dict[str, Any]:
        """Convenience method for A* search with custom weight metric."""
        if metric != self.graph.weight_metric:
            self.graph = GraphService(weight_metric=metric)
        return self.astar(start_id, target_id, record_steps=record_steps)

    def bellman_ford(
        self,
        start_id: int,
        target_id: int,
        record_steps: bool = True,
    ) -> Dict[str, Any]:
        """Find shortest path between start_id and target_id using Bellman-Ford algorithm.

        Time Complexity: O(|V| * |E|).
        Space Complexity: O(|V|).
        Guarantee: exact_shortest_path, capable of detecting negative cycles.
        """
        start_time = time.perf_counter()

        if start_id not in self.graph.places_by_id or target_id not in self.graph.places_by_id:
            return {
                "success": False,
                "error": "Start or target destination does not exist in the graph.",
                "path": [],
                "total_weight": float("inf"),
            }

        distances: Dict[int, float] = {nid: float("inf") for nid in self.graph.places_by_id}
        distances[start_id] = 0.0
        predecessors: Dict[int, Optional[int]] = {nid: None for nid in self.graph.places_by_id}

        all_edges: List[Tuple[int, int, float, Dict[str, Any]]] = []
        for u in self.graph.places_by_id:
            for v, w, edge_info in self.graph.adj.get(u, []):
                all_edges.append((u, v, w, edge_info))

        steps: List[Dict[str, Any]] = []
        step_counter = 0

        if record_steps:
            steps.append({
                "step": step_counter,
                "action": "initialize",
                "current_node": start_id,
                "current_node_name": self.graph.places_by_id[start_id].name,
                "tentative_distance": 0.0,
                "distances": {nid: (round(d, 2) if d != float("inf") else None) for nid, d in distances.items()},
                "open_set": [{"node_id": start_id, "cost": 0.0, "node_name": self.graph.places_by_id[start_id].name}],
                "closed_set": [start_id],
                "explanation": f"Initialized Bellman-Ford: d({self.graph.places_by_id[start_id].name}) = 0.0.",
            })

        v_count = len(self.graph.places_by_id)
        for pass_num in range(1, v_count):
            relaxed_any = False
            for u, v, w, edge_info in all_edges:
                if distances[u] != float("inf") and distances[u] + w < distances[v]:
                    distances[v] = distances[u] + w
                    predecessors[v] = u
                    relaxed_any = True
                    step_counter += 1

                    if record_steps:
                        steps.append({
                            "step": step_counter,
                            "action": f"pass_{pass_num}_relax",
                            "current_node": v,
                            "current_node_name": self.graph.places_by_id[v].name,
                            "relaxed_edge": {"source": u, "target": v, "weight": round(w, 2)},
                            "tentative_distance": round(distances[v], 2),
                            "distances": {nid: (round(d, 2) if d != float("inf") else None) for nid, d in distances.items()},
                            "explanation": f"Pass {pass_num}: Relaxed edge ({self.graph.places_by_id[u].name} -> {self.graph.places_by_id[v].name}) to distance {distances[v]:.1f}.",
                        })

            if not relaxed_any:
                break

        # Check negative cycle
        has_negative_cycle = False
        for u, v, w, edge_info in all_edges:
            if distances[u] != float("inf") and distances[u] + w < distances[v]:
                has_negative_cycle = True
                break

        if has_negative_cycle:
            return {
                "success": False,
                "error": "Negative weight cycle detected in the network graph.",
                "has_negative_cycle": True,
                "steps": steps,
            }

        # Reconstruct path
        path: List[int] = []
        curr: Optional[int] = target_id
        while curr is not None:
            path.append(curr)
            if curr == start_id:
                break
            curr = predecessors[curr]

        if not path or path[-1] != start_id:
            return {
                "success": False,
                "reachable": False,
                "error": f"No path exists between {self.graph.places_by_id[start_id].name} and {self.graph.places_by_id[target_id].name}.",
                "path": [],
                "path_node_ids": [],
                "steps": steps,
            }

        path.reverse()
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        total_dist_km = 0.0
        total_time_mins = 0.0
        total_cost_inr = 0.0
        legs = []

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge_data = self.graph.edges_by_pair.get((u, v))
            if edge_data:
                legs.append(edge_data)
                total_dist_km += edge_data.get("distance_km", 0.0)
                total_time_mins += edge_data.get("travel_time_minutes", 0.0)
                if edge_data.get("estimated_cost") is not None:
                    total_cost_inr += edge_data["estimated_cost"]
                else:
                    total_cost_inr += edge_data.get("distance_km", 0.0) * 12.0

        return {
            "success": True,
            "reachable": True,
            "start_id": start_id,
            "target_id": target_id,
            "path_ids": path,
            "path_node_ids": path,
            "legs": legs,
            "total_weight": round(distances[target_id], 2),
            "weight_metric": self.graph.weight_metric,
            "total_distance_km": round(total_dist_km, 2),
            "total_time_minutes": round(total_time_mins, 1),
            "total_cost_inr": round(total_cost_inr, 2),
            "elapsed_ms": round(elapsed_ms, 3),
            "steps": steps,
            "algorithm": "Bellman-Ford",
            "guarantee": "exact_shortest_path",
        }

    def find_bellman_ford_path(self, start_id: int, target_id: int, metric: str = "time", record_steps: bool = True) -> Dict[str, Any]:
        """Convenience method for Bellman-Ford with custom weight metric."""
        if metric != self.graph.weight_metric:
            self.graph = GraphService(weight_metric=metric)
        return self.bellman_ford(start_id, target_id, record_steps=record_steps)

