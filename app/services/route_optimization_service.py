"""Route Optimization Service: Multi-objective optimization and Pareto dominance trade-offs.

Compares alternative routes computed under different objectives (Distance, Time, Cost, Balanced)
and calculates empirical Pareto dominance to identify non-dominated trade-offs.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.graph_service import GraphService
from app.services.tsp_service import TSPService


class RouteOptimizationService:
    def __init__(self, places=None, connections=None):
        self.places = places
        self.connections = connections

    def compare_objectives(
        self,
        stop_ids: List[int],
        start_id: int,
        end_id: Optional[int] = None,
        return_to_start: bool = True,
    ) -> Dict[str, Any]:
        """Compute and compare routes across all four optimization objectives."""
        objectives = ["time", "distance", "cost", "balanced"]
        candidates: List[Dict[str, Any]] = []

        for obj in objectives:
            graph_svc = GraphService(
                places=self.places,
                connections=self.connections,
                weight_metric=obj,
            )
            tsp_svc = TSPService(graph_svc)
            res = tsp_svc.solve_tour(
                stop_ids=stop_ids,
                start_id=start_id,
                end_id=end_id,
                return_to_start=return_to_start,
            )

            if res["success"]:
                candidates.append({
                    "objective": obj,
                    "title": f"Optimized for {obj.capitalize()}",
                    "ordered_stop_ids": res["ordered_stop_ids"],
                    "ordered_stops": res["ordered_stops"],
                    "legs": res["legs"],
                    "distance_km": res["total_distance_km"],
                    "time_minutes": res["total_time_minutes"],
                    "cost_inr": res["total_estimated_cost"],
                    "algorithm": res["algorithm"],
                    "guarantee": res["guarantee"],
                })

        # Calculate Pareto Dominance
        # Route A dominates Route B if:
        # distance(A) <= distance(B) and time(A) <= time(B) and cost(A) <= cost(B)
        # with at least one strictly smaller (<).
        for i, r_a in enumerate(candidates):
            is_dominated = False
            dominated_by = []

            for j, r_b in enumerate(candidates):
                if i == j:
                    continue

                d_le = r_b["distance_km"] <= r_a["distance_km"]
                t_le = r_b["time_minutes"] <= r_a["time_minutes"]
                c_le = r_b["cost_inr"] <= r_a["cost_inr"]

                strictly_better = (
                    r_b["distance_km"] < r_a["distance_km"] or
                    r_b["time_minutes"] < r_a["time_minutes"] or
                    r_b["cost_inr"] < r_a["cost_inr"]
                )

                if d_le and t_le and c_le and strictly_better:
                    is_dominated = True
                    dominated_by.append(r_b["objective"])

            r_a["is_pareto_optimal"] = not is_dominated
            r_a["dominated_by"] = dominated_by

        # Generate trade-off explanations
        explanations = []
        if len(candidates) > 1:
            fastest = min(candidates, key=lambda c: c["time_minutes"])
            shortest = min(candidates, key=lambda c: c["distance_km"])
            cheapest = min(candidates, key=lambda c: c["cost_inr"])

            if fastest["objective"] != shortest["objective"]:
                time_diff = shortest["time_minutes"] - fastest["time_minutes"]
                dist_diff = fastest["distance_km"] - shortest["distance_km"]
                explanations.append(
                    f"The fastest route ({fastest['title']}) saves {round(time_diff, 1)} minutes "
                    f"compared to the shortest route, but adds {round(dist_diff, 1)} km of highway driving."
                )

            if cheapest["objective"] != fastest["objective"]:
                cost_diff = fastest["cost_inr"] - cheapest["cost_inr"]
                explanations.append(
                    f"The budget-optimized route ({cheapest['title']}) saves ~₹{round(cost_diff, 0)} "
                    f"over the fastest option by favoring fuel-efficient direct corridors."
                )

        return {
            "success": True,
            "candidates": candidates,
            "routes": candidates,
            "trade_off_notes": explanations,
            "pareto_summary": (
                "A route is Pareto non-dominated (optimal) if no other candidate is strictly better on all "
                "three metrics (distance, time, cost). Tourists can pick based on personal priorities."
            ),
        }

    def compare_route_alternatives(self, start_id: int, target_id: int) -> Dict[str, Any]:
        """Convenience method comparing route alternatives between two destinations."""
        return self.compare_objectives(stop_ids=[target_id], start_id=start_id, return_to_start=False)
