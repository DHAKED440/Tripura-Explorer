"""Local Experiences directory and inquiry handling.

Only administrators can create or approve providers. Public visitors see
approved listings only, and inquiries are stored for review instead of being
treated as a confirmed booking.
"""
from __future__ import annotations

import math
from types import SimpleNamespace

from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from email_validator import EmailNotValidError, validate_email
from flask_login import current_user
from app.extensions import db
from app.forms import InquiryForm
from app.models import Business, Inquiry, Place
from app.services.local_experience_search import (
    CATEGORY_LABELS, OSMServiceError, find_cached_place, find_persisted_restaurant,
    geocode_destination, persist_discovered_restaurants, search_nearby,
)

bp = Blueprint("experiences", __name__)
LOCAL_EXPERIENCE_PAGE_SIZE = 24


@bp.get("/api/health")
def api_health():
    """Report the provider used for nearby place discovery."""
    return jsonify({"provider": "OpenStreetMap", "geocoder": "configured"})


def validate_inquiry_payload(payload: dict) -> tuple[dict, list[str]]:
    """Shared validation for the JSON API and the HTML form."""
    errors: list[str] = []
    name = str(payload.get("name") or "").strip()
    email = str(payload.get("email") or "").strip()
    phone = str(payload.get("phone") or "").strip()
    message = str(payload.get("message") or "").strip()

    if len(name) < 2:
        errors.append("Please enter your name (at least 2 characters).")
    if len(name) > 120:
        errors.append("Your name is too long (120 characters maximum).")
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        errors.append("Please enter a valid email address.")
    if len(phone) > 40:
        errors.append("The phone number is too long (40 characters maximum).")
    if len(message) < 10:
        errors.append("Please write at least 10 characters in your message.")
    if len(message) > 1200:
        errors.append("The message is too long (1200 characters maximum).")

    cleaned = {
        "name": name,
        "email": email.lower(),
        "phone": phone or None,
        "message": message,
    }
    return cleaned, errors


@bp.route("/experiences", methods=["GET", "POST"])
def index():
    """Search mapped OpenStreetMap features around a submitted destination."""
    params = request.values
    category = params.get("category", "All types")
    if category == "All types":
        category = "All Places"
    destination_selection = " ".join(params.get("destination", "").split())[:200]
    custom_destination = " ".join(params.get("custom_destination", "").split())[:200]
    destination_query = custom_destination if destination_selection == "__custom__" else destination_selection
    keyword = " ".join(params.get("keyword", "").split())[:100]
    origin_mode = params.get("origin", "destination")
    try:
        radius_km = int(params["radius"]) if params.get("radius") else 25
    except ValueError:
        radius_km = 25
    if radius_km not in {5, 10, 25, 50}:
        radius_km = 25
    if category not in CATEGORY_LABELS:
        category = "All Places"
    destinations = Place.query.filter(Place.is_published.is_(True)).order_by(Place.name.asc()).all()
    destination_options = []
    for place in destinations:
        area = place.locality or (place.district.name if place.district else "")
        label = place.name
        if area and area.casefold() not in place.name.casefold():
            label = f"{place.name}, {area}, Tripura, India"
        destination_options.append(label)
    if not destination_query and origin_mode != "current":
        destination_query = next(
            (label for label in destination_options if label.casefold().startswith("dumboor lake")),
            "Dumboor Lake, Tripura, India",
        )
    origin = None
    origin_name = destination_query or None
    if origin_mode == "current":
        try:
            lat, lng = float(params.get("latitude", "")), float(params.get("longitude", ""))
            if not (math.isfinite(lat) and math.isfinite(lng) and -90 <= lat <= 90 and -180 <= lng <= 180):
                raise ValueError
            origin = SimpleNamespace(latitude=lat, longitude=lng, name="Current location", district=None)
            origin_name = "Current location"
        except (ValueError, TypeError):
            origin = None
    results, error, searched = [], None, params.get("search") == "1"
    error_retryable = False
    results_limited = False
    geocode_error = None
    if searched:
        if origin is None:
            try:
                resolved = geocode_destination(destination_query)
                if resolved:
                    origin = SimpleNamespace(**resolved, district=None)
                    origin_name = destination_query
                else:
                    geocode_error = "Could not find this destination in Tripura. Try another location."
            except OSMServiceError as exc:
                geocode_error = exc.public_message
                error_retryable = exc.retryable
        if origin is None:
            error = geocode_error or "Choose a destination or use your current location for this search."
        else:
            try:
                results = search_nearby(origin.latitude, origin.longitude, radius_km, category, keyword)
                if category in {"All Places", "Food & Restaurants"}:
                    persist_discovered_restaurants(results)
                results_limited = bool(getattr(results, "truncated", False))
            except OSMServiceError as exc:
                current_app.logger.warning("OpenStreetMap nearby search failed: status=%s", exc.provider_status)
                error = exc.public_message
                error_retryable = exc.retryable
    return render_template(
        "experiences.html", destinations=destination_options, destination=destination_query, origin=origin,
        origin_name=origin_name, origin_mode=origin_mode,
        search_latitude=params.get("latitude", ""), search_longitude=params.get("longitude", ""),
        category=category, keyword=keyword, radius_km=radius_km, results=results,
        search_error=error, searched=searched, categories=CATEGORY_LABELS,
        search_error_retryable=error_retryable,
        results_limited=results_limited,
        destination_selection=destination_selection,
        custom_destination=custom_destination,
        osm_tile_url=current_app.config["MAP_TILE_URL"], map_attribution=current_app.config["MAP_TILE_ATTRIBUTION"],
    )


@bp.get("/api/local-experiences/geocode")
def api_geocode():
    query = " ".join(request.args.get("q", "").split())[:200]
    if not query:
        return jsonify({"error": "Enter a destination in Tripura.", "error_code": "invalid_destination", "retryable": False}), 400
    try:
        result = geocode_destination(query)
    except OSMServiceError as exc:
        return jsonify({"error": exc.public_message, "error_code": exc.provider_status, "retryable": exc.retryable}), exc.http_status
    if result is None:
        return jsonify({"error": "We couldn’t find that destination in Tripura. Check the spelling or choose a listed place.", "error_code": "invalid_destination", "retryable": False}), 404
    return jsonify({"result": result, "attribution": "© OpenStreetMap contributors · Nominatim"})


@bp.get("/api/local-experiences")
def api_local_experiences():
    """Search OSM features around supplied coordinates or explicitly geocode a destination."""
    category = request.args.get("category", "All Places")
    if category == "All types":
        category = "All Places"
    if category not in CATEGORY_LABELS:
        return jsonify({"error": "Choose a supported place type.", "error_code": "invalid_category", "retryable": False}), 400
    keyword = " ".join(request.args.get("keyword", "").split())[:100]
    try:
        radius = int(request.args["radius"]) if request.args.get("radius") else 25
    except ValueError:
        radius = None
    if radius not in {5, 10, 25, 50}:
        return jsonify({"error": "Radius must be 5, 10, 25 or 50 km.", "error_code": "invalid_radius", "retryable": False}), 400
    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        page = 0
    if not 1 <= page <= 9:
        return jsonify({"error": "Page must be between 1 and 9.", "error_code": "invalid_page", "retryable": False}), 400

    try:
        if request.args.get("origin") == "current" or "lat" in request.args or "latitude" in request.args:
            lat = float(request.args.get("lat", request.args.get("latitude", "")))
            lon = float(request.args.get("lon", request.args.get("longitude", "")))
            if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError
            destination = SimpleNamespace(latitude=lat, longitude=lon, name="Current location", district=None)
        else:
            name = " ".join(request.args.get("destination", "").split())[:200]
            if not name:
                return jsonify({"error": "Choose a Tripura destination or use current location.", "error_code": "invalid_destination", "retryable": False}), 400
            resolved = geocode_destination(name)
            if not resolved:
                return jsonify({"error": "We couldn’t find that destination in Tripura. Check the spelling or choose a listed place.", "error_code": "invalid_destination", "retryable": False}), 404
            destination = SimpleNamespace(**resolved, district=None)
    except (ValueError, TypeError):
        return jsonify({"error": "Valid latitude and longitude are required for a location search.", "error_code": "invalid_coordinates", "retryable": False}), 400
    except OSMServiceError as exc:
        return jsonify({"error": exc.public_message, "error_code": exc.provider_status, "retryable": exc.retryable}), exc.http_status
    try:
        records = search_nearby(destination.latitude, destination.longitude, radius, category, keyword)
    except ValueError:
        return jsonify({"error": "Unknown experience category."}), 400
    except OSMServiceError as exc:
        return jsonify({"error": exc.public_message, "error_code": exc.provider_status, "retryable": exc.retryable}), exc.http_status
    if category in {"All Places", "Food & Restaurants"}:
        persist_discovered_restaurants(records)
    start = (page - 1) * LOCAL_EXPERIENCE_PAGE_SIZE
    page_records = records[start:start + LOCAL_EXPERIENCE_PAGE_SIZE]
    has_more = start + len(page_records) < len(records)
    truncated = bool(getattr(records, "truncated", False))
    return jsonify({
        "destination": {"name": destination.name,
                        "latitude": destination.latitude, "longitude": destination.longitude},
        "search_coverage_km": radius, "results": page_records,
        "results_returned": len(page_records), "result_count": None if truncated else len(records),
        "result_count_is_exact": not truncated, "has_more": has_more,
        "next_page": page + 1 if has_more else None, "result_set_limited": truncated,
        "attribution": "© OpenStreetMap contributors",
    })


@bp.get("/api/local-experiences/place/<osm_type>/<int:osm_id>")
def api_local_experience_details(osm_type: str, osm_id: int):
    """Return cached provider details or the persisted OSM restaurant model."""
    if osm_type not in {"node", "way", "relation"}:
        return jsonify({"error": "Invalid OpenStreetMap element type."}), 400
    item = find_cached_place(osm_type, osm_id)
    if item is None:
        item = find_persisted_restaurant(osm_type, osm_id)
    if item is None:
        return jsonify({"error": "Search for nearby places again to load this listing."}), 404
    return jsonify(item)


@bp.get("/experiences/<slug>")
def detail(slug: str):
    provider = Business.query.filter(Business.slug == slug).first()
    if provider is None or not provider.is_approved:
        abort(404)
    related = (
        Business.query.filter(
            Business.approval_status == "approved",
            Business.category == provider.category,
            Business.id != provider.id,
        )
        .order_by(Business.name.asc())
        .limit(3)
        .all()
    )
    return render_template(
        "business_detail.html",
        provider=provider,
        related=related,
        form=InquiryForm(),
        inquiry_sent=request.args.get("sent") == "1",
    )


@bp.post("/api/inquiries")
def api_create_inquiry():
    payload = request.get_json(silent=True) or request.form
    business_id = payload.get("business_id") or payload.get("business_slug")
    provider = None
    if str(business_id or "").isdigit():
        provider = db.session.get(Business, int(business_id))
    elif business_id:
        provider = Business.query.filter(Business.slug == str(business_id)).first()

    if provider is None or not provider.is_approved:
        return jsonify({"error": "not_found", "message": "Provider not found."}), 404

    cleaned, errors = validate_inquiry_payload(payload)
    if errors:
        return jsonify({"error": "validation_failed", "errors": errors}), 400

    inquiry = Inquiry(
        business_id=provider.id,
        user_id=current_user.id if current_user.is_authenticated else None,
        name=cleaned["name"],
        email=cleaned["email"],
        phone=cleaned["phone"],
        message=cleaned["message"],
    )
    db.session.add(inquiry)
    db.session.commit()
    return (
        jsonify(
            {
                "status": "received",
                "inquiry_id": inquiry.id,
                "message": (
                    "Thank you. Your inquiry has been recorded and an administrator will review it. "
                    "This prototype does not confirm bookings."
                ),
            }
        ),
        201,
    )


@bp.post("/experiences/<slug>/inquire")
def submit_inquiry_form(slug: str):
    """No-JavaScript fallback for the inquiry form."""
    provider = Business.query.filter(Business.slug == slug).first()
    if provider is None or not provider.is_approved:
        abort(404)
    form = InquiryForm()
    if form.validate_on_submit():
        inquiry = Inquiry(
            business_id=provider.id,
            user_id=current_user.id if current_user.is_authenticated else None,
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            phone=(form.phone.data or "").strip() or None,
            message=form.message.data.strip(),
        )
        db.session.add(inquiry)
        db.session.commit()
        flash("Thank you — your inquiry has been recorded for review.", "success")
        return redirect(url_for("experiences.detail", slug=provider.slug, sent=1))
    for field_errors in form.errors.values():
        for error in field_errors:
            flash(error, "error")
    return redirect(url_for("experiences.detail", slug=provider.slug))
