"""Travelling Salesperson Problem (TSP) & Multi-Stop Tour Service.

Implements exact Held-Karp dynamic programming with bitmask states for N <= 10,
and Nearest-Neighbor with 2-opt local search improvement for larger sets.
Uses all-pairs shortest path closure so routes work reliably across the
road network without requiring direct single edges between every destination pair.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from app.services.graph_service import GraphService
from app.services.shortest_path_service import ShortestPathService


class TSPService:
    EXACT_SOLVER_MAX_STOPS = 10

    def __init__(self, graph_service: Optional[GraphService] = None):
        self.graph = graph_service if graph_service is not None else GraphService()
        self.sp_service = ShortestPathService(self.graph)

    def solve_tour(
        self,
        stop_ids: List[int],
        start_id: int,
        end_id: Optional[int] = None,
        return_to_start: bool = True,
    ) -> Dict[str, Any]:
        """Solve multi-stop tour over the selected destination subset."""
        start_time = time.perf_counter()

        # Deduplicate while preserving start_id first
        unique_stops: List[int] = []
        if start_id in stop_ids:
            unique_stops.append(start_id)
        for sid in stop_ids:
            if sid not in unique_stops and sid in self.graph.places_by_id:
                unique_stops.append(sid)

        if start_id not in unique_stops and start_id in self.graph.places_by_id:
            unique_stops.insert(0, start_id)

        n = len(unique_stops)
        if n == 0:
            return {
                "success": False,
                "error": "No valid destination stops specified.",
                "stops": [],
                "legs": [],
                "total_weight": 0.0,
            }

        if n == 1:
            stop_node = self.graph.places_by_id[unique_stops[0]].to_dict()
            return {
                "success": True,
                "algorithm": "Trivial single stop",
                "guarantee": "exact_tsp",
                "stop_order": [unique_stops[0]],
                "stops": [stop_node],
                "legs": [],
                "total_weight": 0.0,
                "total_distance_km": 0.0,
                "total_time_minutes": 0.0,
                "total_estimated_cost": 0.0,
                "elapsed_ms": 0.1,
            }

        # 1. Compute all-pairs shortest path matrix between unique_stops
        # dist_matrix[i][j] = shortest path weight from unique_stops[i] to unique_stops[j]
        dist_matrix: List[List[float]] = [[0.0] * n for _ in range(n)]
        path_matrix: List[List[List[int]]] = [[[] for _ in range(n)] for _ in range(n)]
        legs_matrix: List[List[List[Dict[str, Any]]]] = [[[] for _ in range(n)] for _ in range(n)]

        for i in range(n):
            u = unique_stops[i]
            for j in range(n):
                if i == j:
                    dist_matrix[i][j] = 0.0
                    path_matrix[i][j] = [u]
                    legs_matrix[i][j] = []
                else:
                    v = unique_stops[j]
                    sp = self.sp_service.dijkstra(u, v, record_steps=False)
                    if not sp["success"] or not sp.get("reachable", True):
                        return {
                            "success": False,
                            "error": f"Cannot connect {self.graph.places_by_id[u].name} to {self.graph.places_by_id[v].name} through the road network.",
                            "unreachable_pair": (u, v),
                            "algorithm": "TSP Multi-Stop",
                            "guarantee": "no_feasible_route",
                        }
                    dist_matrix[i][j] = sp["total_weight"]
                    path_matrix[i][j] = sp["path_ids"]
                    legs_matrix[i][j] = sp["legs"]

        # Map start_id index
        start_idx = unique_stops.index(start_id)

        # Map end_id index if specified and not round-trip
        end_idx = None
        if not return_to_start and end_id is not None and end_id in unique_stops:
            end_idx = unique_stops.index(end_id)

        # 2. Run solver (Exact Held-Karp if n <= EXACT_SOLVER_MAX_STOPS, else Heuristic 2-opt)
        if n <= self.EXACT_SOLVER_MAX_STOPS:
            best_order_indices, best_weight = self._held_karp(
                dist_matrix, n, start_idx, end_idx, return_to_start
            )
            algorithm_name = "Held-Karp Dynamic Programming (Bitmask)"
            guarantee = "exact_tsp"
            complexity = f"O(N^2 * 2^N) with N={n} (total states: {n * (1 << n)})"
        else:
            best_order_indices, best_weight = self._nearest_neighbor_2opt(
                dist_matrix, n, start_idx, end_idx, return_to_start
            )
            algorithm_name = "Nearest-Neighbor + 2-Opt Heuristic"
            guarantee = "heuristic_tour"
            complexity = f"O(N^2) heuristic passes for N={n}"

        # 3. Unpack full road path through all intermediate nodes
        full_path_ids: List[int] = []
        full_legs: List[Dict[str, Any]] = []
        ordered_stops: List[Dict[str, Any]] = []

        total_distance = 0.0
        total_time = 0.0
        total_cost = 0.0

        for idx in best_order_indices:
            stop_id = unique_stops[idx]
            ordered_stops.append(self.graph.places_by_id[stop_id].to_dict())

        for k in range(len(best_order_indices) - 1):
            i = best_order_indices[k]
            j = best_order_indices[k + 1]

            road_path = path_matrix[i][j]
            if not full_path_ids:
                full_path_ids.extend(road_path)
            else:
                full_path_ids.extend(road_path[1:])

            for leg in legs_matrix[i][j]:
                full_legs.append(leg)
                total_distance += leg.get("distance_km", 0.0)
                total_time += leg.get("travel_time_minutes", 0.0)
                if leg.get("estimated_cost") is not None:
                    total_cost += leg["estimated_cost"]
                else:
                    total_cost += leg.get("distance_km", 0.0) * 12.0

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        steps = []
        for step_idx, ord_idx in enumerate(best_order_indices):
            s_id = unique_stops[ord_idx]
            steps.append({
                "step": step_idx,
                "action": "visit_stop",
                "current_node": s_id,
                "current_node_name": self.graph.places_by_id[s_id].name,
                "description": f"Leg {step_idx + 1}: Visiting {self.graph.places_by_id[s_id].name}.",
            })

        return {
            "success": True,
            "algorithm": algorithm_name,
            "guarantee": guarantee,
            "complexity": complexity,
            "is_round_trip": return_to_start,
            "ordered_stop_ids": [unique_stops[i] for i in best_order_indices],
            "tour_node_ids": [unique_stops[i] for i in best_order_indices],
            "path_node_ids": full_path_ids if full_path_ids else [unique_stops[i] for i in best_order_indices],
            "ordered_stops": ordered_stops,
            "full_road_path_ids": full_path_ids,
            "legs": full_legs,
            "total_weight": round(best_weight, 2),
            "weight_metric": self.graph.weight_metric,
            "total_distance_km": round(total_distance, 2),
            "total_time_minutes": round(total_time, 1),
            "total_estimated_cost": round(total_cost, 2),
            "elapsed_ms": round(elapsed_ms, 3),
            "stops_count": n,
            "steps": steps,
        }

    def solve_multi_stop_tour(
        self,
        origin_id: int,
        stop_ids: List[int],
        metric: str = "time",
        record_steps: bool = True,
    ) -> Dict[str, Any]:
        """Convenience method for multi-stop tour calculation."""
        if metric != self.graph.weight_metric:
            self.graph = GraphService(weight_metric=metric)
            self.sp_service = ShortestPathService(self.graph)
        return self.solve_tour(stop_ids=stop_ids, start_id=origin_id, return_to_start=True)

    def _held_karp(
        self,
        dist: List[List[float]],
        n: int,
        start_idx: int,
        end_idx: Optional[int],
        return_to_start: bool,
    ) -> Tuple[List[int], float]:
        """Exact Held-Karp dynamic programming bitmask solver."""
        # dp[mask][j] = (min_cost, parent_node)
        # mask is integer 0 to (1 << n) - 1 representing visited set
        memo: Dict[Tuple[int, int], Tuple[float, int]] = {}

        # Base case: visited only start_idx
        start_mask = 1 << start_idx
        memo[(start_mask, start_idx)] = (0.0, -1)

        # Iterate all bitmask sizes from 2 to n
        for size in range(2, n + 1):
            for mask in range(1 << n):
                if bin(mask).count("1") != size:
                    continue
                if not (mask & (1 << start_idx)):
                    continue

                for j in range(n):
                    if j == start_idx or not (mask & (1 << j)):
                        continue

                    prev_mask = mask ^ (1 << j)
                    min_cost = float("inf")
                    best_parent = -1

                    for k in range(n):
                        if k == j or not (prev_mask & (1 << k)):
                            continue
                        if (prev_mask, k) in memo:
                            cost = memo[(prev_mask, k)][0] + dist[k][j]
                            if cost < min_cost:
                                min_cost = cost
                                best_parent = k

                    if best_parent != -1:
                        memo[(mask, j)] = (min_cost, best_parent)

        full_mask = (1 << n) - 1
        best_cost = float("inf")
        last_node = -1

        if return_to_start:
            # Add cost from last node back to start_idx
            for j in range(n):
                if j == start_idx:
                    continue
                if (full_mask, j) in memo:
                    total = memo[(full_mask, j)][0] + dist[j][start_idx]
                    if total < best_cost:
                        best_cost = total
                        last_node = j
        elif end_idx is not None:
            # Fixed end node
            if (full_mask, end_idx) in memo:
                best_cost = memo[(full_mask, end_idx)][0]
                last_node = end_idx
        else:
            # Free end node
            for j in range(n):
                if (full_mask, j) in memo:
                    if memo[(full_mask, j)][0] < best_cost:
                        best_cost = memo[(full_mask, j)][0]
                        last_node = j

        # Reconstruct path from memo
        curr_mask = full_mask
        curr_node = last_node
        path = []

        while curr_node != -1:
            path.append(curr_node)
            next_node = memo[(curr_mask, curr_node)][1]
            curr_mask = curr_mask ^ (1 << curr_node)
            curr_node = next_node

        path.reverse()

        if return_to_start:
            path.append(start_idx)

        return path, best_cost

    def _nearest_neighbor_2opt(
        self,
        dist: List[List[float]],
        n: int,
        start_idx: int,
        end_idx: Optional[int],
        return_to_start: bool,
    ) -> Tuple[List[int], float]:
        """Nearest-neighbor construction followed by 2-opt local search."""
        # 1. Greedy Nearest Neighbor
        unvisited = set(range(n))
        unvisited.remove(start_idx)
        tour = [start_idx]

        curr = start_idx
        while unvisited:
            # If end_idx is fixed, keep it for last if possible
            candidates = [node for node in unvisited if node != end_idx] or list(unvisited)
            next_node = min(candidates, key=lambda node: dist[curr][node])
            tour.append(next_node)
            unvisited.remove(next_node)
            curr = next_node

        if return_to_start:
            tour.append(start_idx)

        # 2. 2-Opt local improvement
        improved = True
        max_iterations = 200
        iteration = 0

        def calc_length(t: List[int]) -> float:
            return sum(dist[t[i]][t[i + 1]] for i in range(len(t) - 1))

        best_tour = tour
        best_len = calc_length(best_tour)

        while improved and iteration < max_iterations:
            improved = False
            iteration += 1

            for i in range(1, len(best_tour) - 2):
                for j in range(i + 1, len(best_tour) - (0 if return_to_start else 1)):
                    # Reverse segment from i to j
                    new_tour = best_tour[:i] + best_tour[i : j + 1][::-1] + best_tour[j + 1 :]
                    new_len = calc_length(new_tour)
                    if new_len < best_len - 1e-6:
                        best_tour = new_tour
                        best_len = new_len
                        improved = True
                        break
                if improved:
                    break

        return best_tour, best_len
