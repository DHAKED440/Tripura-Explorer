"""Local Experiences directory and inquiry handling.

Only administrators can create or approve providers. Public visitors see
approved listings only, and inquiries are stored for review instead of being
treated as a confirmed booking.
"""
from __future__ import annotations

import json
import math
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from flask import Blueprint, Response, abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from email_validator import EmailNotValidError, validate_email
from flask_login import current_user
from app.extensions import db
from app.forms import InquiryForm
from app.models import Business, Inquiry, Place
from app.services.destination_service import get_place_by_slug
from app.services.local_experience_search import CATEGORY_LABELS, PlacesSearchError, photo_resource_path, search_nearby

bp = Blueprint("experiences", __name__)


@bp.get("/api/health")
def api_health():
    """Report whether server-side Places credentials are configured, never the secret."""
    return jsonify({"google_key_loaded": bool(current_app.config.get("GOOGLE_MAPS_API_KEY", "").strip())})


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
    """Search real businesses around the selected coordinate-verified attraction."""
    params = request.values
    category = params.get("category", "All types")
    slug = params.get("destination", "")
    keyword = " ".join(params.get("keyword", "").split())[:100]
    origin_mode = params.get("origin", "destination")
    try:
        radius_km = int(params["radius"]) if params.get("radius") else None
    except ValueError:
        radius_km = None
    if radius_km not in {5, 10, 25, 50}:
        radius_km = None
    if category not in CATEGORY_LABELS:
        category = "All types"
    destinations = (Place.query.filter(
        Place.is_published.is_(True), Place.latitude.is_not(None), Place.longitude.is_not(None)
    ).order_by(Place.name.asc()).all())
    destination = get_place_by_slug(slug) if slug else None
    origin = destination
    origin_name = destination.name if destination else None
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
    if searched:
        if origin is None:
            error = "Choose a Tripura destination or use the Current location button to share your location for this search."
        elif not (getattr(origin, "latitude", None) is not None and getattr(origin, "longitude", None) is not None):
            error = "Choose a destination with valid coordinates before searching."
        elif not current_app.config.get("GOOGLE_MAPS_API_KEY"):
            error = "The backend has no GOOGLE_MAPS_API_KEY. Add it to the project .env or deployment environment, then restart Flask."
        else:
            try:
                results = search_nearby(current_app.config["GOOGLE_MAPS_API_KEY"], origin, category,
                                        radius_km, keyword)
            except PlacesSearchError as exc:
                current_app.logger.exception("Local experience Places search failed")
                error = exc.public_message
    return render_template(
        "experiences.html", destinations=destinations, destination=destination, origin=origin,
        origin_name=origin_name, origin_mode=origin_mode,
        search_latitude=params.get("latitude", ""), search_longitude=params.get("longitude", ""),
        category=category, keyword=keyword, radius_km=radius_km, results=results,
        search_error=error, searched=searched, categories=CATEGORY_LABELS,
        photo_endpoint=url_for("experiences.place_photo"),
    )


@bp.get("/experiences/place-photo")
def place_photo():
    """Fetch a Places photo server-side so the provider key is not exposed."""
    api_key = current_app.config.get("GOOGLE_MAPS_API_KEY")
    resource = photo_resource_path(request.args.get("name", ""))
    if not api_key or not resource:
        abort(404)
    upstream = Request(resource, headers={"User-Agent": "TripuraExplore/1.0", "X-Goog-Api-Key": api_key})
    try:
        with urlopen(upstream, timeout=8) as response:
            photo_uri = json.loads(response.read()).get("photoUri", "")
        parsed_photo = urlparse(photo_uri)
        if parsed_photo.scheme != "https" or not (parsed_photo.hostname or "").endswith(".googleusercontent.com"):
            abort(404)
        with urlopen(Request(photo_uri, headers={"User-Agent": "TripuraExplore/1.0"}), timeout=8) as response:
            content = response.read(8_000_000)
            content_type = response.headers.get_content_type()
    except (HTTPError, URLError, TimeoutError, OSError):
        current_app.logger.info("Google Places photo unavailable")
        abort(404)
    except (ValueError, json.JSONDecodeError):
        abort(404)
    if not content_type.startswith("image/"):
        abort(404)
    return Response(content, content_type=content_type, headers={"Cache-Control": "no-store"})


@bp.get("/api/local-experiences")
def api_local_experiences():
    """JSON endpoint used by the optional React frontend for nearby searches."""
    destination = get_place_by_slug(request.args.get("destination", ""))
    if request.args.get("origin", "destination") == "current":
        try:
            lat, lng = float(request.args.get("latitude", "")), float(request.args.get("longitude", ""))
            if not (math.isfinite(lat) and math.isfinite(lng) and -90 <= lat <= 90 and -180 <= lng <= 180):
                raise ValueError
            destination = SimpleNamespace(latitude=lat, longitude=lng, name="Current location", district=None)
        except (ValueError, TypeError):
            return jsonify({"error": "Valid current-location coordinates are required."}), 400
    elif not destination or not destination.map_ready or not destination.has_tripura_coordinates:
        return jsonify({"error": "Choose a destination with valid Tripura coordinates."}), 400
    if not current_app.config.get("GOOGLE_MAPS_API_KEY"):
        return jsonify({"error": "The backend has no GOOGLE_MAPS_API_KEY. Add it to the project .env or deployment environment, then restart Flask."}), 503
    category = request.args.get("category", "All types")
    keyword = " ".join(request.args.get("keyword", "").split())[:100]
    try:
        radius = int(request.args["radius"]) if request.args.get("radius") else None
    except ValueError:
        radius = None
    if radius not in {None, 5, 10, 25, 50}:
        return jsonify({"error": "Radius must be 5, 10, 25 or 50 km."}), 400
    try:
        records = search_nearby(current_app.config["GOOGLE_MAPS_API_KEY"], destination, category, radius, keyword)
    except ValueError:
        return jsonify({"error": "Unknown experience category."}), 400
    except PlacesSearchError as exc:
        current_app.logger.exception("Local experience API search failed")
        return jsonify({"error": exc.public_message, "provider_status": exc.provider_status}), 502
    for record in records:
        if record["photo"]:
            record["photo"] = url_for("experiences.place_photo", name=record["photo"])
    return jsonify({
        "destination": {"id": getattr(destination, "slug", None), "name": destination.name,
                        "district": destination.district.name if destination.district else None,
                        "latitude": destination.latitude, "longitude": destination.longitude},
        "search_coverage_km": records[0].get("search_coverage_km") if records else (radius or 50), "results": records,
        "attribution": "Google Places",
    })


@bp.get("/api/local-experiences/<place_id>")
def api_local_experience_details(place_id: str):
    """Retrieve expanded Place data only when the user opens a result."""
    from app.services.local_experience_search import fetch_place_details

    api_key = current_app.config.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return jsonify({"error": "The backend has no GOOGLE_MAPS_API_KEY. Add it to the project .env or deployment environment, then restart Flask."}), 503
    destination = get_place_by_slug(request.args.get("destination", ""))
    if request.args.get("origin") == "current":
        try:
            origin_lat, origin_lng = float(request.args.get("latitude", "")), float(request.args.get("longitude", ""))
            if not (math.isfinite(origin_lat) and math.isfinite(origin_lng) and -90 <= origin_lat <= 90 and -180 <= origin_lng <= 180):
                raise ValueError
            destination = SimpleNamespace(latitude=origin_lat, longitude=origin_lng, name="Current location")
        except (ValueError, TypeError):
            return jsonify({"error": "Valid current-location coordinates are required."}), 400
    elif not destination or not destination.map_ready or not destination.has_tripura_coordinates:
        return jsonify({"error": "The selected destination has no valid Tripura coordinates."}), 400
    try:
        details = fetch_place_details(api_key, place_id)
    except ValueError:
        return jsonify({"error": "Invalid business Place ID."}), 400
    except PlacesSearchError as exc:
        current_app.logger.exception("Local experience details request failed")
        return jsonify({"error": exc.public_message, "provider_status": exc.provider_status}), 502
    location = details.get("location") or {}
    lat, lng = location.get("latitude"), location.get("longitude")
    if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
        return jsonify({"error": "Google Places did not provide a business location."}), 502
    from app.services.local_experience_search import haversine_km
    photos = []
    for photo in details.get("photos", [])[:5]:
        if photo.get("name"):
            photos.append({"url": url_for("experiences.place_photo", name=photo["name"]),
                           "attributions": photo.get("authorAttributions", [])})
    return jsonify({
        "id": details.get("id"), "name": (details.get("displayName") or {}).get("text"),
        "address": details.get("formattedAddress"), "latitude": lat, "longitude": lng,
        "distance_km": round(haversine_km(destination.latitude, destination.longitude, lat, lng), 1),
        "category": (details.get("primaryTypeDisplayName") or {}).get("text"),
        "types": details.get("types", []), "rating": details.get("rating"),
        "review_count": details.get("userRatingCount"), "business_status": details.get("businessStatus"),
        "open_now": (details.get("currentOpeningHours") or {}).get("openNow"),
        "opening_hours": (details.get("regularOpeningHours") or {}).get("weekdayDescriptions"),
        "phone": details.get("nationalPhoneNumber"), "website": details.get("websiteUri"),
        "maps_url": details.get("googleMapsUri"), "price_level": details.get("priceLevel"),
        "photos": photos,
        "menu_available": False,
        "menu_message": "Menu not available online from this listing. Contact the business or check its official website for current dishes and prices.",
        "data_source": "Google Places",
    })


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
