"""Rule-based trip planning.

The planner is deliberately simple and explainable:

1. validate the visitor's preferences,
2. pick published destinations that match the chosen interests,
3. rank them with transparent rules (interest matches, popularity, data quality),
4. group them into areas - by straight-line proximity when coordinates are
   verified, otherwise by district,
5. spread the groups over the requested number of days.

It never claims to produce an optimised route and it never invents distances,
fees or opening hours.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from app.services.destination_service import (
    INTEREST_OPTIONS,
    haversine_km,
)

CLUSTER_RADIUS_KM = 45.0
MAX_STOPS_PER_DAY = 3


@dataclass
class ItineraryPreferences:
    """Validated trip planner input."""

    duration_days: int
    starting_location: str
    interests: list[str] = field(default_factory=list)
    budget: int | None = None
    travel_date: date | None = None

    @classmethod
    def from_payload(
        cls,
        payload: dict,
        min_days: int = 1,
        max_days: int = 3,
        allowed_interests: list[str] | None = None,
    ) -> tuple["ItineraryPreferences", list[str]]:
        """Build preferences from a dict, returning ``(preferences, errors)``."""
        allowed = {value.lower(): value for value in (allowed_interests or INTEREST_OPTIONS)}
        errors: list[str] = []

        raw_days = payload.get("duration_days", payload.get("days"))
        try:
            days = int(raw_days)
        except (TypeError, ValueError):
            days = 0
        if days < min_days or days > max_days:
            errors.append(f"Trip duration must be between {min_days} and {max_days} days.")

        starting_location = str(payload.get("starting_location") or "").strip()
        if len(starting_location) < 2:
            errors.append("Please enter where your trip starts (for example Agartala).")
        elif len(starting_location) > 120:
            errors.append("The starting location is too long (maximum 120 characters).")

        raw_interests = payload.get("interests") or []
        if isinstance(raw_interests, str):
            raw_interests = [part.strip() for part in raw_interests.split(",")]
        interests: list[str] = []
        unknown: list[str] = []
        for item in raw_interests:
            key = str(item).strip().lower()
            if not key:
                continue
            if key in allowed:
                value = allowed[key]
                if value not in interests:
                    interests.append(value)
            else:
                unknown.append(str(item).strip())
        if unknown:
            errors.append("Unknown interests: " + ", ".join(sorted(set(unknown))) + ".")
        if not interests:
            errors.append("Choose at least one interest.")

        budget = payload.get("budget")
        if budget in ("", None):
            budget = None
        else:
            try:
                budget = int(float(budget))
            except (TypeError, ValueError):
                errors.append("Budget must be a number in Indian Rupees.")
                budget = None
            else:
                if budget < 0:
                    errors.append("Budget cannot be negative.")
                    budget = None

        travel_date = payload.get("travel_date")
        if isinstance(travel_date, str):
            travel_date = travel_date.strip() or None
        if travel_date:
            try:
                travel_date = datetime.strptime(str(travel_date), "%Y-%m-%d").date()
            except ValueError:
                errors.append("Travel date must use the YYYY-MM-DD format.")
                travel_date = None
        else:
            travel_date = None

        preferences = cls(
            duration_days=days if 1 <= days <= 3 else max(min_days, min(days or min_days, max_days)),
            starting_location=starting_location,
            interests=interests,
            budget=budget,
            travel_date=travel_date,
        )
        return preferences, errors


def rank_places(places: list, interests: list[str]) -> list[tuple]:
    """Return ``[(place, score, matched_interests)]`` ordered best first."""
    wanted = {interest.lower() for interest in interests}
    ranked = []
    for place in places:
        tags = {tag.lower() for tag in place.tag_list}
        matched = sorted(tag for tag in place.tag_list if tag.lower() in wanted)
        score = 3.0 * len(matched) + min(place.popularity or 0, 100) / 25.0
        if place.map_ready:
            score += 1.0
        if not place.is_verified:
            score += 0.25
        ranked.append((place, round(score, 3), matched))
    ranked.sort(key=lambda item: (-item[1], item[0].name))
    return ranked


def _cluster_places(ordered_places: list) -> list[dict]:
    """Group places into areas (proximity when possible, district otherwise)."""
    clusters: list[dict] = []
    for place in ordered_places:
        target = None
        if place.map_ready:
            for cluster in clusters:
                if cluster["centroid"] is None:
                    continue
                distance = haversine_km(
                    place.latitude, place.longitude, cluster["centroid"][0], cluster["centroid"][1]
                )
                if distance <= CLUSTER_RADIUS_KM:
                    target = cluster
                    break
            if target is None:
                clusters.append({"centroid": (place.latitude, place.longitude), "places": [place]})
                continue
            target["places"].append(place)
            points = target["places"]
            target["centroid"] = (
                sum(p.latitude for p in points) / len(points),
                sum(p.longitude for p in points) / len(points),
            )
        else:
            label = place.district_name or "Unspecified area"
            for cluster in clusters:
                if cluster.get("label") == label:
                    target = cluster
                    break
            if target is None:
                clusters.append({"centroid": None, "label": label, "places": [place]})
            else:
                target["places"].append(place)
    return clusters


def generate_plan(preferences: ItineraryPreferences, places: list) -> dict:
    """Build the day-by-day plan for the given preferences and candidate places."""
    notes: list[str] = []
    warnings: list[str] = [
        "Travel time, opening hours and entry fees are not verified yet for this prototype, "
        "so the plan shows a suggested order of stops rather than a timed schedule."
    ]

    ranked = rank_places(list(places), preferences.interests)
    capacity = preferences.duration_days * MAX_STOPS_PER_DAY
    chosen = [item for item in ranked[:capacity]]

    if not chosen:
        return {
            "days": [],
            "notes": notes,
            "warnings": warnings
            + [
                "No published destination matches these interests yet. "
                "Try selecting more interests or fewer days."
            ],
            "matched_count": 0,
            "ranked": ranked,
            "uses_coordinates": False,
        }

    ordered_places = [item[0] for item in chosen]
    clusters = _cluster_places(ordered_places)
    cluster_of = {}
    for index, cluster in enumerate(clusters):
        for place in cluster["places"]:
            cluster_of[place.id] = index

    day_buckets: dict[int, list] = {day: [] for day in range(1, preferences.duration_days + 1)}
    cluster_day: dict[int, int] = {}

    for place in ordered_places:
        cluster_index = cluster_of.get(place.id)
        target_day = None
        if cluster_index in cluster_day:
            candidate_day = cluster_day[cluster_index]
            if len(day_buckets[candidate_day]) < MAX_STOPS_PER_DAY:
                target_day = candidate_day
        if target_day is None:
            target_day = min(day_buckets, key=lambda day: (len(day_buckets[day]), day))
        if len(day_buckets[target_day]) >= MAX_STOPS_PER_DAY:
            break
        day_buckets[target_day].append(place)
        if cluster_index is not None:
            cluster_day.setdefault(cluster_index, target_day)

    days_payload = []
    uses_coordinates = False
    for day, bucket in day_buckets.items():
        stops = []
        previous = None
        for order, place in enumerate(bucket, start=1):
            leg_km = None
            if previous is not None and previous.map_ready and place.map_ready:
                leg_km = round(
                    haversine_km(previous.latitude, previous.longitude, place.latitude, place.longitude), 1
                )
                uses_coordinates = True
            stops.append(
                {
                    "place": place,
                    "day_number": day,
                    "stop_order": order,
                    "leg_km": leg_km,
                    "area": place.district_name or "Area not recorded",
                }
            )
            previous = place
        days_payload.append({"day": day, "stops": stops})

    if uses_coordinates:
        notes.append(
            "Stops in the same day are grouped using straight-line distance between the stored coordinates. "
            "Straight-line distance is not a road distance, so use the directions links to check real drive times."
        )
    else:
        notes.append(
            "Stops are grouped by district because verified coordinates are missing for some destinations. "
            "No distance or travel-time estimates are shown."
        )

    if len(chosen) < preferences.duration_days:
        notes.append("There are not enough matching destinations to fill every day of this trip.")

    if len(chosen) < capacity:
        notes.append(
            f"{len(chosen)} matching published destination(s) selected — fewer than the "
            f"{capacity} slots available for {preferences.duration_days} day(s)."
        )

    ranked_interest_labels = sorted({interest for item in chosen for interest in item[2]})
    if ranked_interest_labels:
        notes.append("Matched interests: " + ", ".join(ranked_interest_labels) + ".")

    if preferences.budget is not None:
        warnings.append(
            "Budget planning is limited: the prototype has no verified price data, "
            "so your budget was recorded but no cost estimate was produced."
        )
    if preferences.travel_date is not None:
        if preferences.travel_date < date.today():
            warnings.append("The travel date is in the past — pick a future date for a realistic plan.")
        else:
            notes.append(f"Planned travel date: {preferences.travel_date.strftime('%d %B %Y')}.")

    return {
        "days": days_payload,
        "notes": notes,
        "warnings": warnings,
        "matched_count": len(ordered_places),
        "ranked": ranked,
        "uses_coordinates": uses_coordinates,
    }


def summarise_plan(plan: dict) -> str:
    """Short human readable summary stored with a saved itinerary."""
    days = plan.get("days") or []
    parts = [f"{len(days)} day plan"]
    total = sum(len(day["stops"]) for day in days)
    parts.append(f"{total} stops")
    if plan.get("uses_coordinates"):
        parts.append("grouped with straight-line proximity")
    else:
        parts.append("grouped by district")
    return " · ".join(parts)