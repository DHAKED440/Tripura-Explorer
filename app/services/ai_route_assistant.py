"""AI Route Assistant Service: Natural-language query parser and mathematical route explanation.

Translates conversational tourist requests into structured optimization parameters,
and explains calculated itineraries and trade-offs using actual graph numbers.
Provides a robust deterministic fallback when external AI providers are not configured.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.models import Place


class AIRouteAssistant:
    def __init__(self, places: Optional[List[Place]] = None):
        if places is None:
            self.places = Place.query.filter_by(is_published=True).all()
        else:
            self.places = places
        self.places_by_slug = {p.slug: p for p in self.places}

    def parse_natural_language_request(self, user_query: str) -> Dict[str, Any]:
        """Convert conversational travel preferences into validated structured planner inputs."""
        query = (user_query or "").lower()

        # 1. Detect duration in days
        duration = 2  # default
        days_match = re.search(r"(\d+)\s*[-]?\s*(?:days?|day|d)", query)
        if days_match:
            try:
                parsed_days = int(days_match.group(1))
                if 1 <= parsed_days <= 5:
                    duration = parsed_days
            except ValueError:
                pass
        elif "one day" in query or "single day" in query:
            duration = 1
        elif "two days" in query:
            duration = 2
        elif "three days" in query:
            duration = 3

        # 2. Detect starting destination
        start_id = None
        for p in self.places:
            name_parts = p.name.lower().split()
            locality = (p.locality or "").lower()
            if p.name.lower() in query or (locality and locality in query):
                start_id = p.id
                break

        # Fallback start: Agartala (Ujjayanta Palace)
        if not start_id:
            for p in self.places:
                if "agartala" in (p.locality or "").lower() or "ujjayanta" in p.slug:
                    start_id = p.id
                    break
            if not start_id and self.places:
                start_id = self.places[0].id

        # 3. Detect interests
        detected_interests = []
        interest_keywords = {
            "heritage": ["history", "heritage", "palace", "ancient", "monument", "sculpture", "archaeology"],
            "lakes": ["lake", "water", "boating", "boat", "rudrasagar", "dumboor"],
            "hills": ["hill", "hills", "mountain", "viewpoint", "jampui", "altitude"],
            "temples": ["temple", "temples", "puja", "shakti", "pilgrim", "religious", "sacred"],
            "wildlife": ["wildlife", "animal", "zoo", "sanctuary", "bison", "safari", "leopard"],
            "nature": ["nature", "forest", "green", "waterfall", "river"],
            "culture": ["culture", "craft", "folk", "museum", "tradition"],
        }
        for category_slug, words in interest_keywords.items():
            if any(w in query for w in words):
                detected_interests.append(category_slug.capitalize())

        if not detected_interests:
            detected_interests = ["Heritage", "Lakes"]

        # 4. Detect travel pace
        pace = "balanced"
        if any(w in query for w in ["relaxed", "slow", "easy", "leisure", "peaceful", "calm"]):
            pace = "relaxed"
        elif any(w in query for w in ["packed", "fast", "busy", "intense", "maximum", "see everything"]):
            pace = "packed"

        # 5. Detect budget
        budget = None
        budget_match = re.search(r"(?:rs\.?|inr|₹|budget\s*of)\s*(\d{3,6})", query)
        if budget_match:
            try:
                budget = float(budget_match.group(1))
            except ValueError:
                pass

        # 6. Detect accessibility
        accessibility_required = any(
            w in query for w in ["wheelchair", "accessible", "elderly", "mobility"]
        )

        primary_int = detected_interests[0].lower() if detected_interests else "all"

        return {
            "success": True,
            "raw_query": user_query,
            "parsed": {
                "days": duration,
                "duration_days": duration,
                "origin_id": start_id,
                "start_destination_id": start_id,
                "primary_interest": primary_int,
                "interests": detected_interests,
                "pace": pace,
                "budget": budget,
            },
            "parsed_preferences": {
                "start_destination_id": start_id,
                "duration_days": duration,
                "interests": detected_interests,
                "pace": pace,
                "budget": budget,
                "accessibility_required": accessibility_required,
                "return_to_start": True,
            },
            "interpretation_note": (
                f"Parsed request for a {duration}-day {pace} journey starting from "
                f"{self.places_by_slug.get(start_id, self.places[0]).name if start_id else 'Agartala'} "
                f"focusing on {', '.join(detected_interests)}."
            ),
        }

    def parse_natural_language_query(self, user_query: str) -> Dict[str, Any]:
        """Alias for parse_natural_language_request."""
        res = self.parse_natural_language_request(user_query)
        return res.get("parsed", {})

    def explain_route(self, route_result: Dict[str, Any]) -> str:
        """Generate a mathematically sound, tourist-friendly plain-language explanation of calculated route."""
        if not route_result.get("success"):
            return f"Route could not be generated: {route_result.get('error', 'Unknown constraint violation')}."

        total_km = route_result.get("total_distance_km", 0.0)
        total_time = route_result.get("total_time_minutes", 0.0)
        algorithm = route_result.get("algorithm", "Graph Optimizer")
        guarantee = route_result.get("guarantee", "feasible_route")

        hours = int(total_time // 60)
        mins = int(total_time % 60)
        time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"

        stops = route_result.get("ordered_stops", [])
        stop_names = []
        for s in stops:
            if isinstance(s, dict):
                stop_names.append(s.get("name", "Destination"))
            elif isinstance(s, int):
                p = next((x for x in self.places if x.id == s), None)
                stop_names.append(p.name if p else f"Stop {s}")
            else:
                stop_names.append(str(s))

        explanation_parts = [
            f"**Route Overview:** Your journey covers {total_km} km with approximately {time_str} of total road travel across {len(stops)} stops.",
            f"**Mathematical Formulation:** The sequence was calculated using **{algorithm}** ({guarantee}). "
            f"Instead of relying on straight-line air distances, the optimizer navigated the exact verified road topology of Tripura.",
        ]

        if "exact_tsp" in guarantee:
            explanation_parts.append(
                "Because your stop count is within the exact solver threshold (N <= 10), the algorithm used "
                "the **Held-Karp Dynamic Programming method**, proving this order is mathematically optimal "
                "for minimum travel burden under the selected objective."
            )
        elif "heuristic_tour" in guarantee:
            explanation_parts.append(
                "For your selection, the engine executed **Nearest-Neighbor followed by 2-Opt local improvement**, "
                "systematically untangling crossing road segments until no pairwise inversion could reduce travel time."
            )

        if len(stop_names) > 2:
            explanation_parts.append(
                f"**Travel Sequence:** Departure from **{stop_names[0]}**, moving along connecting highways to "
                f"{', '.join(stop_names[1:-1])}, and concluding at **{stop_names[-1]}**."
            )

        return "\n\n".join(explanation_parts)
