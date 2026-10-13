"""Personalization Service: Destination relevance scoring, constraint satisfaction, and multi-day itinerary construction."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Set

from app.models import Place
from app.services.destination_service import haversine_km
from app.services.graph_service import GraphService
from app.services.tsp_service import TSPService


class PersonalizationService:
    def __init__(self, graph_service: Optional[GraphService] = None):
        self.graph = graph_service if graph_service is not None else GraphService()
        self.tsp_service = TSPService(self.graph)

    def score_destination(
        self,
        place: Place,
        start_place: Place,
        interests: List[str],
        w_i: float = 0.40,
        w_p: float = 0.25,
        w_f: float = 0.15,
        w_t: float = 0.20,
    ) -> float:
        """Calculate destination relevance score: S(v) = w_i*I(v) + w_p*P(v) + w_f*F(v) - w_t*T(v)."""
        # Interest match score I(v)
        i_score = 0.0
        if interests:
            user_ints = {i.lower().strip() for i in interests if i.strip()}
            cat_slug = (place.category.slug if place.category else "").lower()
            extra_tags = {t.lower().strip() for t in (place.extra_tags or "").split(",") if t.strip()}
            matched = 0
            if cat_slug in user_ints:
                matched += 1
            matched += len(user_ints.intersection(extra_tags))
            i_score = min(1.0, matched / max(1, len(user_ints)))
        else:
            i_score = 0.5

        # Popularity score P(v) normalized [0, 1]
        p_score = min(1.0, max(0.0, (place.popularity or 50) / 100.0))

        # Feasibility / verification bonus F(v)
        f_score = 0.5
        if place.coordinates_verified:
            f_score += 0.3
        if place.typical_visit_hours:
            f_score += 0.2
        f_score = min(1.0, f_score)

        # Travel burden T(v) normalized by max diameter (~160km in Tripura)
        dist_km = 0.0
        if start_place.has_coordinates and place.has_coordinates:
            dist_km = haversine_km(
                start_place.latitude, start_place.longitude,
                place.latitude, place.longitude
            )
        t_score = min(1.0, dist_km / 160.0)

        total_score = (w_i * i_score) + (w_p * p_score) + (w_f * f_score) - (w_t * t_score)
        return round(total_score, 4)

    def build_personalized_itinerary(
        self,
        start_id: int,
        duration_days: int = 2,
        interests: Optional[List[str]] = None,
        pace: str = "balanced",  # relaxed, balanced, packed
        budget: Optional[float] = None,
        must_visit_ids: Optional[List[int]] = None,
        accessibility_required: bool = False,
        return_to_start: bool = True,
    ) -> Dict[str, Any]:
        """Generate a personalized, constraint-validated multi-day journey with daily schedules."""
        interests = interests or []
        must_visit_ids = must_visit_ids or []

        if start_id not in self.graph.places_by_id:
            return {
                "success": False,
                "feasible": False,
                "error": "Starting destination is not available in the graph network.",
            }

        start_place = self.graph.places_by_id[start_id]

        # Pace parameters
        pace_limits = {
            "relaxed": {"max_stops_day": 2, "max_travel_hours": 4.5, "label": "Relaxed (2 stops/day)"},
            "balanced": {"max_stops_day": 3, "max_travel_hours": 6.0, "label": "Balanced (3 stops/day)"},
            "packed": {"max_stops_day": 4, "max_travel_hours": 8.0, "label": "Packed (4 stops/day)"},
        }
        active_pace = pace_limits.get(pace, pace_limits["balanced"])
        max_total_stops = duration_days * active_pace["max_stops_day"]

        # 1. Validate must-visit feasibility
        if len(must_visit_ids) > max_total_stops:
            return {
                "success": False,
                "feasible": False,
                "error": f"You selected {len(must_visit_ids)} must-visit destinations, but a {duration_days}-day {pace} trip allows at most {max_total_stops} stops.",
                "suggestions": [
                    f"Increase trip duration to {math.ceil(len(must_visit_ids) / active_pace['max_stops_day'])} days.",
                    f"Switch pace from '{pace}' to 'packed' to fit more stops per day.",
                    f"Keep at most {max_total_stops} must-visit destinations and mark others as optional.",
                ],
            }

        # 2. Candidate filtering
        candidates: List[Place] = []
        for p in self.graph.places:
            if p.id == start_id:
                continue

            if accessibility_required:
                acc_text = (p.accessibility_info or "").lower()
                if "not suitable for wheelchairs" in acc_text or "limited access for wheelchairs" in acc_text:
                    if p.id in must_visit_ids:
                        return {
                            "success": False,
                            "feasible": False,
                            "error": f"Must-visit destination '{p.name}' has recorded accessibility barriers, conflicting with your accessibility preference.",
                            "suggestions": ["Remove the wheelchair accessibility requirement or replace this destination."],
                        }
                    continue

            candidates.append(p)

        # 3. Score and rank candidates
        scored_candidates = []
        for p in candidates:
            score = self.score_destination(p, start_place, interests)
            is_must = p.id in must_visit_ids
            scored_candidates.append({
                "place": p,
                "score": score,
                "is_must_visit": is_must,
                "rank_score": 999.0 if is_must else score,  # must-visit ranked highest
            })

        scored_candidates.sort(key=lambda item: item["rank_score"], reverse=True)

        # Select top candidates to fit total trip capacity
        selected_items = scored_candidates[:max_total_stops]
        selected_places = [item["place"] for item in selected_items]
        selected_ids = [p.id for p in selected_places]

        # 4. Partition selected stops across days
        # Sort places by geographic longitude / latitude angle relative to start to form daily geographic sectors
        def angle_from_start(p: Place) -> float:
            if not p.has_coordinates or not start_place.has_coordinates:
                return 0.0
            return math.atan2(p.latitude - start_place.latitude, p.longitude - start_place.longitude)

        selected_places.sort(key=angle_from_start)

        days_stops: List[List[int]] = [[] for _ in range(duration_days)]
        for i, p in enumerate(selected_places):
            day_idx = i % duration_days
            days_stops[day_idx].append(p.id)

        # 5. Build detailed daily schedule with TSP ordering
        daily_itinerary: List[Dict[str, Any]] = []
        grand_total_km = 0.0
        grand_total_mins = 0.0
        grand_total_cost = 0.0
        infeasibility_warnings: List[str] = []

        for d_num in range(1, duration_days + 1):
            day_stop_ids = days_stops[d_num - 1]
            if not day_stop_ids:
                continue

            # Solve optimal tour for this day starting from start_id
            day_tour = self.tsp_service.solve_tour(
                stop_ids=day_stop_ids,
                start_id=start_id,
                return_to_start=return_to_start,
            )

            if not day_tour["success"]:
                infeasibility_warnings.append(
                    f"Day {d_num}: Could not connect all assigned stops ({day_tour.get('error')})."
                )
                continue

            day_dist = day_tour["total_distance_km"]
            day_travel_mins = day_tour["total_time_minutes"]
            day_cost = day_tour["total_estimated_cost"]

            grand_total_km += day_dist
            grand_total_mins += day_travel_mins
            grand_total_cost += day_cost

            # Check daily travel limit
            travel_hours = day_travel_mins / 60.0
            if travel_hours > active_pace["max_travel_hours"]:
                infeasibility_warnings.append(
                    f"Day {d_num}: Estimated travel time ({round(travel_hours, 1)} hrs) exceeds your {pace} daily threshold ({active_pace['max_travel_hours']} hrs)."
                )

            # Build timeline stops
            timeline = []
            curr_time_min = 9 * 60  # Start at 09:00 AM

            stops_in_order = day_tour["ordered_stops"]
            for s_idx, stop in enumerate(stops_in_order):
                is_start_or_end = (stop["id"] == start_id and (s_idx == 0 or s_idx == len(stops_in_order) - 1))
                h = int(curr_time_min // 60)
                m = int(curr_time_min % 60)
                time_str = f"{h:02d}:{m:02d}"

                visit_hrs = stop.get("typical_visit_hours") or 1.5
                visit_mins = int(visit_hrs * 60)

                timeline.append({
                    "time": time_str,
                    "place_id": stop["id"],
                    "name": stop["name"],
                    "locality": stop.get("locality"),
                    "activity": "Departure" if (is_start_or_end and s_idx == 0) else ("Return" if is_start_or_end else "Sightseeing & Exploration"),
                    "duration_minutes": 0 if is_start_or_end else visit_mins,
                    "image_url": stop.get("image_url"),
                    "category": stop.get("category"),
                })

                if not is_start_or_end:
                    curr_time_min += visit_mins

                # Add leg drive time to next stop
                if s_idx < len(day_tour["legs"]):
                    leg = day_tour["legs"][s_idx]
                    curr_time_min += int(leg.get("travel_time_minutes", 30))

            daily_itinerary.append({
                "day_number": d_num,
                "title": f"Day {d_num}: Exploring {', '.join(self.graph.places_by_id[sid].name for sid in day_stop_ids[:2])}",
                "stops": day_tour["ordered_stops"],
                "legs": day_tour["legs"],
                "distance_km": day_dist,
                "travel_time_minutes": day_travel_mins,
                "estimated_cost": day_cost,
                "timeline": timeline,
            })

        # Check budget constraint
        if budget is not None and grand_total_cost > budget:
            infeasibility_warnings.append(
                f"Estimated travel cost (₹{round(grand_total_cost, 0)}) exceeds your budget constraint (₹{round(budget, 0)}). Suggest reducing distant destinations or using public transit."
            )

        daily_plans = [
            {
                "day_number": d["day_number"],
                "title": d["title"],
                "travel_hours": round(d["travel_time_minutes"] / 60.0, 1),
                "schedule_items": [
                    {
                        "time": t.get("time", ""),
                        "title": t.get("name", ""),
                        "details": f"{t.get('activity', 'Visit')} ({t.get('duration_minutes', 0)} min)",
                    }
                    for t in d.get("timeline", [])
                ],
            }
            for d in daily_itinerary
        ]

        flat_itinerary = []
        for d in daily_itinerary:
            for s in d.get("stops", []):
                flat_itinerary.append(s)

        anim_steps = []
        for s_idx, place_item in enumerate(flat_itinerary):
            pid = place_item.get("id") or place_item.get("place_id")
            anim_steps.append({
                "step": s_idx,
                "action": "schedule_visit",
                "current_node": pid,
                "current_node_name": place_item.get("name", "Destination"),
                "description": f"Scheduled visit to {place_item.get('name', 'Destination')}.",
            })

        return {
            "success": True,
            "feasible": len(infeasibility_warnings) == 0,
            "start_destination": start_place.to_dict(),
            "duration_days": duration_days,
            "pace": pace,
            "pace_info": active_pace,
            "interests": interests,
            "total_destinations_selected": len(selected_places),
            "selected_destinations": [p.to_dict() for p in selected_places],
            "days": daily_itinerary,
            "daily_plans": daily_plans,
            "itinerary": flat_itinerary,
            "steps": anim_steps,
            "total_distance_km": round(grand_total_km, 2),
            "total_travel_time_minutes": round(grand_total_mins, 1),
            "total_time_minutes": round(grand_total_mins, 1),
            "total_estimated_cost": round(grand_total_cost, 2),
            "total_cost_inr": round(grand_total_cost, 2),
            "warnings": infeasibility_warnings,
            "scoring_model": {
                "formula": "S(v) = 0.40*I(v) + 0.25*P(v) + 0.15*F(v) - 0.20*T(v)",
                "terms": "Interest Match (40%) + Popularity (25%) + Data Quality (15%) - Travel Burden (20%)",
            },
        }

    def generate_personalized_journey(
        self,
        start_node_id: int,
        days: int = 2,
        max_daily_travel_hours: float = 6.0,
        primary_interest: str = "heritage",
        pace: str = "moderate",
        objective: str = "balanced",
    ) -> Dict[str, Any]:
        """Convenience method matching journey planner arguments."""
        interests = [primary_interest] if primary_interest and primary_interest != "all" else []
        pace_map = {"relaxed": "relaxed", "moderate": "balanced", "fast": "packed"}
        mapped_pace = pace_map.get(pace.lower(), "balanced")
        return self.build_personalized_itinerary(
            start_id=start_node_id,
            duration_days=days,
            interests=interests,
            pace=mapped_pace,
        )
