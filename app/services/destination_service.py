"""Queries and helpers for destination records.

Routes only ever talk to the database through this module so the "published
records only" rule and the coordinate rules live in one place.
"""
from __future__ import annotations

import math

from sqlalchemy import func, or_

from app.extensions import db
from app.models import Category, District, Place

# Interests offered by the trip planner. They mirror the categories used on the
# public site (plus Wildlife, which appears on the map filter).
INTEREST_OPTIONS = ["Nature", "Heritage", "Lakes", "Hills", "Temples", "Wildlife", "Culture"]

RELATED_RADIUS_KM = 40.0


def get_interest_options() -> list[str]:
    """Interests used by the trip planner form and the map filters."""
    return list(INTEREST_OPTIONS)


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Straight-line distance between two points, in kilometres.

    This is *not* a road distance. The UI always labels it as an approximate
    straight-line distance and links to an external navigation service instead.
    """
    radius = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = phi2 - phi1
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def coordinates_are_valid(latitude, longitude) -> bool:
    """Validate latitude/longitude ranges (unknown stays unknown)."""
    if latitude is None or longitude is None:
        return False
    try:
        lat = float(latitude)
        lng = float(longitude)
    except (TypeError, ValueError):
        return False
    return -90 <= lat <= 90 and -180 <= lng <= 180


def base_query():
    """Published destinations ordered by popularity."""
    return Place.query.filter(Place.is_published.is_(True))


def featured_places(limit: int = 6) -> list[Place]:
    """Destinations shown on the homepage, most popular first."""
    return (
        base_query()
        .order_by(Place.popularity.desc(), Place.name.asc())
        .limit(limit)
        .all()
    )


def get_place_by_slug(slug: str, include_unpublished: bool = False) -> Place | None:
    """Fetch a destination by slug, hiding unpublished records from the public."""
    if not slug:
        return None
    query = Place.query.filter(Place.slug == slug)
    if not include_unpublished:
        query = query.filter(Place.is_published.is_(True))
    return query.first()


def list_categories() -> list[Category]:
    return Category.query.order_by(Category.name.asc()).all()


def list_districts() -> list[District]:
    return District.query.order_by(District.name.asc()).all()


def category_place_counts() -> dict[str, int]:
    """Number of published destinations per category slug."""
    rows = (
        db.session.query(Category.slug, func.count(Place.id))
        .outerjoin(Place, (Place.category_id == Category.id) & (Place.is_published.is_(True)))
        .group_by(Category.slug)
        .all()
    )
    return {slug: count for slug, count in rows}


def district_place_counts() -> dict[str, int]:
    rows = (
        db.session.query(District.slug, func.count(Place.id))
        .outerjoin(Place, (Place.district_id == District.id) & (Place.is_published.is_(True)))
        .group_by(District.slug)
        .all()
    )
    return {slug: count for slug, count in rows}


def nearby_places(place: Place, limit: int = 4) -> list[tuple[Place, float | None]]:
    """Other published destinations close to ``place``.

    When coordinates exist the distance is a straight-line estimate; without
    coordinates the fallback is "same district, same category first".
    """
    if place is None:
        return []
    candidates = (
        base_query()
        .filter(Place.id != place.id)
        .order_by(Place.popularity.desc())
        .limit(60)
        .all()
    )
    scored: list[tuple[Place, float | None]] = []
    for candidate in candidates:
        distance = None
        if place.map_ready and candidate.map_ready:
            distance = haversine_km(place.latitude, place.longitude, candidate.latitude, candidate.longitude)
            if distance > RELATED_RADIUS_KM:
                continue
        else:
            same_district = place.district_id and candidate.district_id == place.district_id
            same_category = candidate.category_id == place.category_id
            if not (same_district or same_category):
                continue
        scored.append((candidate, distance))

    scored.sort(key=lambda item: (item[1] is None, item[1] if item[1] is not None else 0, -item[0].popularity))
    return scored[:limit]


def related_by_interest(place: Place, limit: int = 3) -> list[Place]:
    """Destinations sharing the primary category (a safe fallback for 'nearby')."""
    if place is None:
        return []
    return (
        base_query()
        .filter(Place.category_id == place.category_id, Place.id != place.id)
        .order_by(Place.popularity.desc())
        .limit(limit)
        .all()
    )


def search_places_lite(term: str, limit: int = 8) -> list[Place]:
    """Small helper used by the homepage search suggestions."""
    if not term:
        return []
    pattern = f"%{term.strip()}%"
    return (
        base_query()
        .filter(or_(Place.name.ilike(pattern), Place.locality.ilike(pattern)))
        .order_by(Place.popularity.desc())
        .limit(limit)
        .all()
    )


def dashboard_stats() -> dict:
    """Counters for the admin overview page."""
    from app.models import Business, CorrectionReport, Inquiry, Itinerary, User

    return {
        "places_total": Place.query.count(),
        "places_published": Place.query.filter(Place.is_published.is_(True)).count(),
        "places_unpublished": Place.query.filter(Place.is_published.is_(False)).count(),
        "places_unverified": Place.query.filter(Place.is_verified.is_(False)).count(),
        "places_without_coordinates": Place.query.filter(Place.latitude.is_(None)).count(),
        "coordinates_unverified": Place.query.filter(Place.coordinates_verified.is_(False)).count(),
        "categories": Category.query.count(),
        "districts": District.query.count(),
        "businesses_total": Business.query.count(),
        "businesses_pending": Business.query.filter(Business.approval_status == "pending").count(),
        "inquiries_new": Inquiry.query.filter(Inquiry.status == "new").count(),
        "inquiries_total": Inquiry.query.count(),
        "corrections_new": CorrectionReport.query.filter(CorrectionReport.status == "new").count(),
        "users": User.query.count(),
        "itineraries": Itinerary.query.count(),
    }