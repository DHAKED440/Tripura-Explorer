"""Interactive map page and the marker data endpoint."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, render_template, request
from sqlalchemy import or_

from app.models import Category, District, Place
from app.services.destination_service import base_query, category_place_counts, list_districts

bp = Blueprint("map", __name__)


@bp.get("/map")
def map_page():
    return render_template(
        "map.html",
        categories=Category.query.order_by(Category.name.asc()).all(),
        districts=list_districts(),
        category_counts=category_place_counts(),
    )


@bp.get("/api/places/map")
def api_map_places():
    """Published destinations that have valid coordinates.

    Records without coordinates are skipped rather than guessed, and the
    response tells the UI how many published places are missing coordinates so
    the limitation is visible instead of silent.
    """
    category = (request.args.get("category") or "").strip().lower()
    district = (request.args.get("district") or "").strip()
    only_verified = (request.args.get("verified") or "").strip().lower() in {"1", "true", "yes"}

    query = base_query().filter(Place.latitude.isnot(None), Place.longitude.isnot(None))

    if category:
        found = Category.query.filter(Category.slug == category).first()
        query = query.filter(Place.category_id == found.id) if found else query.filter(Place.id.is_(None))

    if district:
        lowered = district.lower()
        found_district = District.query.filter(
            or_(District.slug == lowered, District.name.ilike(district))
        ).first()
        query = (
            query.filter(Place.district_id == found_district.id)
            if found_district
            else query.filter(Place.id.is_(None))
        )

    if only_verified:
        query = query.filter(Place.coordinates_verified.is_(True))

    places = query.order_by(Place.popularity.desc()).all()
    markers = [place.to_map_dict() for place in places]
    missing = Place.query.filter(
        Place.is_published.is_(True),
        or_(Place.latitude.is_(None), Place.longitude.is_(None)),
    ).count()

    return jsonify(
        {
            "count": len(markers),
            "published_without_coordinates": missing,
            "coordinates_verified": sum(1 for m in markers if m["coordinates_verified"]),
            "filters": {"category": category, "district": district, "verified": only_verified},
            "source_note": "Destination coordinates are maintained in the published place records; check each record's verification status.",
            "places": markers,
        }
    )
