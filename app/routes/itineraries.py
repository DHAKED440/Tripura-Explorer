"""Trip planner, saved trips and the itinerary API."""
from __future__ import annotations

from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.forms import ItinerarySettingsForm
from app.models import Itinerary, ItineraryStop, Place
from app.services.destination_service import get_interest_options
from app.services.itinerary_service import (
    MAX_STOPS_PER_DAY,
    ItineraryPreferences,
    generate_plan,
    summarise_plan,
)
from app.services.search_service import search_places_for_interests

bp = Blueprint("itineraries", __name__)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _request_payload() -> dict:
    if request.is_json:
        return request.get_json(silent=True) or {}
    payload = request.form.to_dict(flat=True)
    payload["interests"] = request.form.getlist("interests")
    return payload


def _build_preferences(payload: dict):
    return ItineraryPreferences.from_payload(
        payload,
        min_days=current_app.config["MIN_ITINERARY_DAYS"],
        max_days=current_app.config["MAX_ITINERARY_DAYS"],
        allowed_interests=get_interest_options(),
    )


def serialise_plan(plan: dict) -> dict:
    """Turn the service output into JSON friendly data."""
    days = []
    for day in plan.get("days", []):
        days.append(
            {
                "day": day["day"],
                "stops": [
                    {
                        "place": stop["place"].to_dict(),
                        "day_number": stop["day_number"],
                        "stop_order": stop["stop_order"],
                        "leg_km": stop["leg_km"],
                        "area": stop["area"],
                    }
                    for stop in day["stops"]
                ],
            }
        )
    return {
        "days": days,
        "notes": plan.get("notes", []),
        "warnings": plan.get("warnings", []),
        "matched_count": plan.get("matched_count", 0),
        "uses_coordinates": plan.get("uses_coordinates", False),
        "max_stops_per_day": MAX_STOPS_PER_DAY,
    }


def _preferences_dict(preferences: ItineraryPreferences) -> dict:
    return {
        "duration_days": preferences.duration_days,
        "starting_location": preferences.starting_location,
        "interests": preferences.interests,
        "budget": preferences.budget,
        "travel_date": preferences.travel_date.isoformat() if preferences.travel_date else None,
    }


def _owned_itinerary(itinerary_id: int) -> Itinerary:
    """Load a trip and enforce ownership on every read, update and delete."""
    itinerary = db.session.get(Itinerary, itinerary_id)
    if itinerary is None:
        abort(404)
    if not current_user.is_authenticated or itinerary.user_id != current_user.id:
        abort(403)
    return itinerary


def _save_plan(itinerary: Itinerary, preferences: ItineraryPreferences, plan: dict) -> None:
    """Replace the stored stops with a freshly generated plan."""
    for stop in list(itinerary.stops):
        db.session.delete(stop)
    db.session.flush()
    for day in plan.get("days", []):
        for stop in day["stops"]:
            db.session.add(
                ItineraryStop(
                    itinerary_id=itinerary.id,
                    place_id=stop["place"].id,
                    day_number=stop["day_number"],
                    stop_order=stop["stop_order"],
                )
            )
    itinerary.duration_days = preferences.duration_days
    itinerary.starting_location = preferences.starting_location
    itinerary.budget = preferences.budget
    itinerary.travel_date = preferences.travel_date
    itinerary.set_interests(preferences.interests)
    itinerary.generation_notes = summarise_plan(plan)


def next_free_slot(itinerary: Itinerary):
    """Return ``(day_number, stop_order)`` for the next free planning slot."""
    grouped = itinerary.stops_by_day()
    for day in sorted(grouped):
        if len(grouped[day]) < MAX_STOPS_PER_DAY:
            return day, len(grouped[day]) + 1
    return None


# --------------------------------------------------------------------------- #
# pages
# --------------------------------------------------------------------------- #
@bp.route("/trip-planner", methods=["GET", "POST"])
def trip_planner():
    """Planner form plus a no-JavaScript fallback that renders the plan inline."""
    preselected = (request.args.get("place") or "").strip()
    prefilled_place = Place.query.filter(Place.slug == preselected, Place.is_published.is_(True)).first()

    if request.method == "POST":
        payload = _request_payload()
        preferences, errors = _build_preferences(payload)
        if errors:
            return (
                render_template(
                    "trip_planner.html",
                    errors=errors,
                    preferences=preferences,
                    form_values=payload,
                    plan=None,
                    prefilled_place=prefilled_place,
                ),
                400,
            )
        places = search_places_for_interests(preferences.interests, limit=60)
        plan = generate_plan(preferences, places)
        return render_template(
            "trip_planner.html",
            errors=[],
            preferences=preferences,
            form_values=payload,
            plan=plan,
            serialised_plan=serialise_plan(plan),
            prefilled_place=prefilled_place,
        )

    return render_template(
        "trip_planner.html",
        errors=[],
        preferences=None,
        form_values={"duration_days": 2, "interests": [], "starting_location": "Agartala"},
        plan=None,
        prefilled_place=prefilled_place,
    )


@bp.post("/trip-planner/save")
@login_required
def save_generated_plan():
    """No-JavaScript save path: regenerate the plan on the server and store it."""
    payload = _request_payload()
    preferences, errors = _build_preferences(payload)
    if errors:
        for error in errors:
            flash(error, "error")
        return redirect(url_for("itineraries.trip_planner"))

    places = search_places_for_interests(preferences.interests, limit=60)
    plan = generate_plan(preferences, places)
    if not plan["days"]:
        flash("No published destination matched those interests, so nothing was saved.", "error")
        return redirect(url_for("itineraries.trip_planner"))

    title = str(payload.get("title") or "").strip() or _default_title(preferences)
    itinerary = Itinerary(
        user_id=current_user.id,
        title=title,
        duration_days=preferences.duration_days,
        starting_location=preferences.starting_location,
        budget=preferences.budget,
        travel_date=preferences.travel_date,
    )
    itinerary.set_interests(preferences.interests)
    db.session.add(itinerary)
    db.session.flush()
    _save_plan(itinerary, preferences, plan)
    db.session.commit()
    flash("Itinerary saved. You can now reorder stops or share a read-only link.", "success")
    return redirect(url_for("itineraries.itinerary_detail", itinerary_id=itinerary.id))


@bp.get("/my-trips")
@login_required
def my_trips():
    trips = (
        Itinerary.query.filter(Itinerary.user_id == current_user.id)
        .order_by(Itinerary.updated_at.desc())
        .all()
    )
    return render_template("my_trips.html", trips=trips)


@bp.get("/itineraries/<int:itinerary_id>")
@login_required
def itinerary_detail(itinerary_id: int):
    itinerary = _owned_itinerary(itinerary_id)
    form = ItinerarySettingsForm(obj=itinerary)
    return render_template("itinerary_detail.html", itinerary=itinerary, form=form)


@bp.get("/shared/<token>")
def shared_itinerary(token: str):
    """Read-only itinerary link - only works when the owner enabled sharing."""
    itinerary = Itinerary.query.filter_by(share_token=token, is_shared=True).first()
    if itinerary is None:
        abort(404)
    return render_template("shared_itinerary.html", itinerary=itinerary)


@bp.post("/itineraries/<int:itinerary_id>/settings")
@login_required
def update_settings(itinerary_id: int):
    itinerary = _owned_itinerary(itinerary_id)
    form = ItinerarySettingsForm()
    if form.validate_on_submit():
        itinerary.title = form.title.data.strip()
        itinerary.starting_location = form.starting_location.data.strip()
        itinerary.budget = form.budget.data
        itinerary.travel_date = form.travel_date.data
        if form.duration_days.data != itinerary.duration_days:
            itinerary.duration_days = form.duration_days.data
            # Removing days must not leave stops pointing at a day that no longer exists.
            for stop in list(itinerary.stops):
                if stop.day_number > itinerary.duration_days:
                    db.session.delete(stop)
            itinerary.normalise_stops()
        db.session.commit()
        flash("Trip details saved.", "success")
    else:
        flash("Please check the trip details and try again.", "error")
    return redirect(url_for("itineraries.itinerary_detail", itinerary_id=itinerary.id))


@bp.post("/itineraries/<int:itinerary_id>/share")
@login_required
def toggle_share(itinerary_id: int):
    itinerary = _owned_itinerary(itinerary_id)
    itinerary.is_shared = not itinerary.is_shared
    if itinerary.is_shared:
        itinerary.ensure_share_token()
    db.session.commit()
    flash(
        "Sharing is on. Anyone with the link can view this plan (read only)."
        if itinerary.is_shared
        else "Sharing is off.",
        "success",
    )
    return redirect(url_for("itineraries.itinerary_detail", itinerary_id=itinerary.id))


@bp.post("/itineraries/<int:itinerary_id>/delete")
@login_required
def delete_itinerary_form(itinerary_id: int):
    itinerary = _owned_itinerary(itinerary_id)
    title = itinerary.title
    db.session.delete(itinerary)
    db.session.commit()
    flash(f"Deleted the trip “{title}”.", "success")
    return redirect(url_for("itineraries.my_trips"))


@bp.post("/trip/add-place")
@login_required
def add_place_to_trip():
    """'Add to Trip' from a destination page."""
    slug = (request.form.get("slug") or "").strip()
    place = Place.query.filter(Place.slug == slug, Place.is_published.is_(True)).first()
    if place is None:
        abort(404)

    trip_id = request.form.get("itinerary_id") or ""
    if not trip_id.isdigit():
        flash("Choose one of your saved trips, or generate a new plan first.", "error")
        return redirect(url_for("itineraries.trip_planner", place=place.slug))

    itinerary = _owned_itinerary(int(trip_id))

    already = any(stop.place_id == place.id for stop in itinerary.stops)
    if already:
        flash(f"{place.name} is already in “{itinerary.title}”.", "info")
        return redirect(url_for("itineraries.itinerary_detail", itinerary_id=itinerary.id))

    slot = next_free_slot(itinerary)
    if slot is None:
        flash(
            f"“{itinerary.title}” already has {MAX_STOPS_PER_DAY} stops on every day. "
            "Remove a stop first or create a new trip.",
            "error",
        )
        return redirect(url_for("itineraries.itinerary_detail", itinerary_id=itinerary.id))

    day_number, stop_order = slot
    db.session.add(
        ItineraryStop(
            itinerary_id=itinerary.id,
            place_id=place.id,
            day_number=day_number,
            stop_order=stop_order,
        )
    )
    db.session.commit()
    flash(f"Added {place.name} to day {day_number} of “{itinerary.title}”.", "success")
    return redirect(url_for("itineraries.itinerary_detail", itinerary_id=itinerary.id))


# --------------------------------------------------------------------------- #
# JSON API
# --------------------------------------------------------------------------- #
@bp.post("/api/itineraries")
def api_create_itinerary():
    """Generate a plan.

    ``{"save": false}`` (the default) returns a preview without touching the
    database. ``{"save": true}`` requires a signed-in user and stores the trip
    together with its owner.
    """
    payload = _request_payload()
    preferences, errors = _build_preferences(payload)
    if errors:
        return jsonify({"error": "validation_failed", "errors": errors}), 400

    places = search_places_for_interests(preferences.interests, limit=60)
    plan = generate_plan(preferences, places)
    response = {"preferences": _preferences_dict(preferences), "plan": serialise_plan(plan)}

    save = str(payload.get("save", "")).lower() in {"1", "true", "yes", "on"}
    if not save:
        return jsonify(response)

    if not current_user.is_authenticated:
        return (
            jsonify(
                {
                    "error": "login_required",
                    "message": "Sign in to save trips to your account.",
                    "login_url": url_for("auth.login", next=url_for("itineraries.trip_planner")),
                }
            ),
            401,
        )
    if not plan["days"]:
        return jsonify({"error": "empty_plan", "message": "No destination matched, so nothing was saved."}), 400

    title = (str(payload.get("title") or "").strip() or _default_title(preferences))
    itinerary = Itinerary(
        user_id=current_user.id,
        title=title,
        duration_days=preferences.duration_days,
        starting_location=preferences.starting_location,
        budget=preferences.budget,
        travel_date=preferences.travel_date,
    )
    itinerary.set_interests(preferences.interests)
    db.session.add(itinerary)
    db.session.flush()
    _save_plan(itinerary, preferences, plan)
    try:
        db.session.commit()
    except SQLAlchemyError:  # pragma: no cover - defensive
        db.session.rollback()
        return jsonify({"error": "save_failed", "message": "The trip could not be saved."}), 500

    response["saved"] = itinerary.to_dict()
    response["saved"]["url"] = url_for("itineraries.itinerary_detail", itinerary_id=itinerary.id)
    return jsonify(response), 201


def _default_title(preferences: ItineraryPreferences) -> str:
    interests = ", ".join(preferences.interests[:3]) or "Trip"
    return f"{preferences.duration_days}-day {interests} trip from {preferences.starting_location}"


@bp.get("/api/itineraries/<int:itinerary_id>")
def api_get_itinerary(itinerary_id: int):
    itinerary = db.session.get(Itinerary, itinerary_id)
    if itinerary is None:
        return jsonify({"error": "not_found"}), 404

    is_owner = current_user.is_authenticated and itinerary.user_id == current_user.id
    token = request.args.get("token")
    if not token and request.is_json:
        token = (request.get_json(silent=True) or {}).get("token")
    if not is_owner:
        if not (itinerary.is_shared and token and token == itinerary.share_token):
            return jsonify({"error": "forbidden"}), 403

    data = itinerary.to_dict()
    data["is_owner"] = bool(is_owner)
    data["is_shared"] = itinerary.is_shared
    return jsonify({"itinerary": data})


@bp.patch("/api/itineraries/<int:itinerary_id>")
@login_required
def api_update_itinerary(itinerary_id: int):
    itinerary = _owned_itinerary(itinerary_id)
    payload = _request_payload()
    regenerate = str(payload.get("regenerate", "")).lower() in {"1", "true", "yes", "on"}

    if payload.get("title"):
        itinerary.title = str(payload["title"]).strip()[:160]

    wants_new_plan = regenerate or "duration_days" in payload or "interests" in payload or "starting_location" in payload
    if wants_new_plan:
        merged = {
            "duration_days": payload.get("duration_days", itinerary.duration_days),
            "starting_location": payload.get("starting_location", itinerary.starting_location),
            "interests": payload.get("interests", itinerary.interests_list),
            "budget": payload.get("budget", itinerary.budget),
            "travel_date": payload.get("travel_date", itinerary.travel_date.isoformat() if itinerary.travel_date else None),
        }
        preferences, errors = _build_preferences(merged)
        if errors:
            return jsonify({"error": "validation_failed", "errors": errors}), 400
        places = search_places_for_interests(preferences.interests, limit=60)
        plan = generate_plan(preferences, places)
        _save_plan(itinerary, preferences, plan)
    else:
        if "budget" in payload:
            try:
                itinerary.budget = int(payload["budget"]) if str(payload["budget"]).strip() else None
            except (TypeError, ValueError):
                return jsonify({"error": "validation_failed", "errors": ["Budget must be a number."]}), 400

    try:
        db.session.commit()
    except SQLAlchemyError:  # pragma: no cover - defensive
        db.session.rollback()
        return jsonify({"error": "update_failed"}), 500
    return jsonify({"itinerary": itinerary.to_dict()})


@bp.delete("/api/itineraries/<int:itinerary_id>")
@login_required
def api_delete_itinerary(itinerary_id: int):
    itinerary = _owned_itinerary(itinerary_id)
    db.session.delete(itinerary)
    db.session.commit()
    return jsonify({"deleted": itinerary_id}), 200


@bp.patch("/api/itineraries/<int:itinerary_id>/stops")
@login_required
def api_reorder_stops(itinerary_id: int):
    """Re-order every stop inside one day: ``{"day_number": 1, "order": [12, 9]}``."""
    itinerary = _owned_itinerary(itinerary_id)
    payload = _request_payload()
    try:
        day_number = int(payload.get("day_number"))
    except (TypeError, ValueError):
        return jsonify({"error": "validation_failed", "errors": ["day_number is required."]}), 400
    if day_number < 1 or day_number > itinerary.duration_days:
        return jsonify({"error": "validation_failed", "errors": ["That day is not part of this trip."]}), 400

    order = payload.get("order") or []
    if not isinstance(order, list):
        return jsonify({"error": "validation_failed", "errors": ["order must be a list of stop ids."]}), 400

    day_stop_ids = {stop.id for stop in itinerary.stops if stop.day_number == day_number}
    if set(int(stop_id) for stop_id in order) != day_stop_ids:
        return jsonify({"error": "validation_failed", "errors": ["Send every stop of that day exactly once."]}), 400

    itinerary.reorder_day(day_number, [int(stop_id) for stop_id in order])
    itinerary.normalise_stops()
    db.session.commit()
    return jsonify({"itinerary": itinerary.to_dict()})


@bp.post("/api/itineraries/<int:itinerary_id>/stops")
@login_required
def api_add_stop(itinerary_id: int):
    itinerary = _owned_itinerary(itinerary_id)
    payload = _request_payload()

    place = None
    if payload.get("place_id"):
        place = db.session.get(Place, int(payload["place_id"]))
    elif payload.get("slug"):
        place = Place.query.filter(Place.slug == payload["slug"]).first()
    if place is None or not place.is_published:
        return jsonify({"error": "not_found", "message": "That destination does not exist."}), 404

    try:
        day_number = int(payload.get("day_number") or 1)
    except (TypeError, ValueError):
        return jsonify({"error": "validation_failed", "errors": ["day_number must be a number."]}), 400
    if day_number < 1 or day_number > itinerary.duration_days:
        return jsonify({"error": "validation_failed", "errors": ["That day is not part of this trip."]}), 400

    if any(stop.place_id == place.id for stop in itinerary.stops):
        return jsonify({"error": "duplicate", "message": "That destination is already in this trip."}), 409

    day_stops = [stop for stop in itinerary.stops if stop.day_number == day_number]
    if len(day_stops) >= MAX_STOPS_PER_DAY:
        return (
            jsonify(
                {
                    "error": "day_full",
                    "message": f"Day {day_number} already has {MAX_STOPS_PER_DAY} stops. Remove one first.",
                }
            ),
            400,
        )

    stop = ItineraryStop(
        itinerary_id=itinerary.id,
        place_id=place.id,
        day_number=day_number,
        stop_order=len(day_stops) + 1,
        planned_time=(payload.get("planned_time") or "").strip() or None,
        notes=(payload.get("notes") or "").strip() or None,
    )
    db.session.add(stop)
    db.session.commit()
    return jsonify({"itinerary": itinerary.to_dict(), "stop": stop.to_dict()}), 201


@bp.patch("/api/itineraries/<int:itinerary_id>/stops/<int:stop_id>")
@login_required
def api_update_stop(itinerary_id: int, stop_id: int):
    itinerary = _owned_itinerary(itinerary_id)
    stop = db.session.get(ItineraryStop, stop_id)
    if stop is None or stop.itinerary_id != itinerary.id:
        return jsonify({"error": "not_found"}), 404

    payload = _request_payload()

    if "day_number" in payload:
        try:
            day_number = int(payload["day_number"])
        except (TypeError, ValueError):
            return jsonify({"error": "validation_failed", "errors": ["day_number must be a number."]}), 400
        if day_number < 1 or day_number > itinerary.duration_days:
            return jsonify({"error": "validation_failed", "errors": ["That day is not part of this trip."]}), 400
        target_day = [item for item in itinerary.stops if item.day_number == day_number and item.id != stop.id]
        if len(target_day) >= MAX_STOPS_PER_DAY:
            return jsonify({"error": "day_full", "message": f"Day {day_number} is full."}), 400
        stop.day_number = day_number
        stop.stop_order = len(target_day) + 1

    if "stop_order" in payload:
        try:
            stop.stop_order = max(1, int(payload["stop_order"]))
        except (TypeError, ValueError):
            return jsonify({"error": "validation_failed", "errors": ["stop_order must be a number."]}), 400

    if "planned_time" in payload:
        stop.planned_time = (payload.get("planned_time") or "").strip() or None
    if "notes" in payload:
        stop.notes = (payload.get("notes") or "").strip() or None

    itinerary.normalise_stops()
    db.session.commit()
    return jsonify({"itinerary": itinerary.to_dict()})


@bp.delete("/api/itineraries/<int:itinerary_id>/stops/<int:stop_id>")
@login_required
def api_delete_stop(itinerary_id: int, stop_id: int):
    itinerary = _owned_itinerary(itinerary_id)
    stop = db.session.get(ItineraryStop, stop_id)
    if stop is None or stop.itinerary_id != itinerary.id:
        return jsonify({"error": "not_found"}), 404
    db.session.delete(stop)
    db.session.flush()
    itinerary.normalise_stops()
    db.session.commit()
    return jsonify({"itinerary": itinerary.to_dict()})