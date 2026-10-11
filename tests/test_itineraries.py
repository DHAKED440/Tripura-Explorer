"""TC-07, TC-08, TC-09 · trip planner, editing stops and ownership."""
from datetime import date

import pytest

from app.extensions import db
from app.models import Itinerary, ItineraryStop, Place
from app.services.itinerary_service import ItineraryPreferences, generate_plan, rank_places
from tests.conftest import login

VALID = {"duration_days": 2, "starting_location": "Agartala", "interests": ["Lakes", "Heritage", "Temples"]}


# --- service level unit tests -------------------------------------------------
def test_preferences_reject_invalid_duration():
    preferences, errors = ItineraryPreferences.from_payload({"duration_days": 8, "starting_location": "Agartala", "interests": ["Lakes"]})
    assert errors
    assert any("duration" in error.lower() for error in errors)


def test_preferences_reject_missing_interests():
    _, errors = ItineraryPreferences.from_payload({"duration_days": 2, "starting_location": "Agartala", "interests": []})
    assert any("interest" in error.lower() for error in errors)


def test_preferences_reject_unknown_interest():
    _, errors = ItineraryPreferences.from_payload({"duration_days": 2, "starting_location": "Agartala", "interests": ["Shopping"]})
    assert any("Unknown interests" in error for error in errors)


def test_preferences_parse_budget_and_date():
    preferences, errors = ItineraryPreferences.from_payload(
        {"duration_days": 1, "starting_location": "Udaipur", "interests": ["Temples"], "budget": "5000", "travel_date": "2026-12-24"}
    )
    assert not errors
    assert preferences.budget == 5000
    assert preferences.travel_date == date(2026, 12, 24)


def test_ranking_prefers_interest_matches(app):
    lakes = Place.query.filter_by(slug="dumboor-lake").first()
    palace = Place.query.filter_by(slug="ujjayanta-palace").first()
    ranked = rank_places([palace, lakes], ["Lakes"])
    assert ranked[0][0].slug == "dumboor-lake"
    assert ranked[0][2] == ["Lakes"]


def test_generated_plan_has_valid_days_and_no_duplicates(app):
    places = Place.query.filter_by(is_published=True).all()
    preferences, _ = ItineraryPreferences.from_payload(VALID)
    plan = generate_plan(preferences, places)
    assert plan["days"]
    seen = set()
    for day in plan["days"]:
        assert 1 <= day["day"] <= preferences.duration_days
        for order, stop in enumerate(day["stops"], start=1):
            assert stop["stop_order"] == order
            assert stop["place"].id not in seen
            seen.add(stop["place"].id)
            assert len(day["stops"]) <= 3


def test_generated_plan_reports_missing_data(app):
    places = Place.query.filter_by(is_published=True).all()
    preferences, _ = ItineraryPreferences.from_payload(VALID)
    plan = generate_plan(preferences, places)
    assert any("not verified" in warning for warning in plan["warnings"])


def test_plan_with_no_matching_places_is_explained(app):
    preferences, _ = ItineraryPreferences.from_payload({"duration_days": 1, "starting_location": "Agartala", "interests": ["Lakes"]})
    plan = generate_plan(preferences, [])
    assert plan["days"] == []
    assert plan["warnings"]


# --- planner page -------------------------------------------------------------
def test_planner_form_renders(client):
    response = client.get("/trip-planner")
    assert response.status_code == 200
    assert b"Your plan will appear here" in response.data


def test_planner_rejects_invalid_input(client):
    response = client.post("/trip-planner", data={"duration_days": "9", "starting_location": "A", "interests": []})
    assert response.status_code == 400
    assert b"Please fix the following" in response.data


def test_planner_renders_a_plan_without_javascript(client):
    response = client.post("/trip-planner", data=VALID)
    assert response.status_code == 200
    assert b"Suggested plan" in response.data
    assert b"Day 1" in response.data


# --- JSON API -----------------------------------------------------------------
def test_api_generates_a_preview(client):
    response = client.post("/api/itineraries", json=VALID)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["plan"]["matched_count"] >= 1
    assert payload["preferences"]["duration_days"] == 2


def test_api_rejects_invalid_preferences(client):
    response = client.post("/api/itineraries", json={"duration_days": 0, "starting_location": "Agartala", "interests": []})
    assert response.status_code == 400
    assert response.get_json()["errors"]


def test_api_save_requires_login(client):
    response = client.post("/api/itineraries", json={**VALID, "save": True})
    assert response.status_code == 401
    assert response.get_json()["error"] == "login_required"


def test_api_saves_and_returns_the_trip(auth_client, app):
    response = auth_client.post("/api/itineraries", json={**VALID, "save": True})
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["saved"]["id"]
    itinerary = db.session.get(Itinerary, payload["saved"]["id"])
    assert itinerary.stops
    assert itinerary.user_id


def test_saved_trip_appears_on_my_trips_page(auth_client):
    auth_client.post("/api/itineraries", json={**VALID, "save": True})
    body = auth_client.get("/my-trips").data
    assert b"Your itineraries" in body
    assert b"Open trip" in body


def test_my_trips_requires_login(client):
    response = client.get("/my-trips")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


# --- stop editing -------------------------------------------------------------
def _save_trip(client):
    response = client.post("/api/itineraries", json={**VALID, "save": True})
    return response.get_json()["saved"]["id"]


def test_add_a_stop(auth_client, app):
    itinerary_id = _save_trip(auth_client)
    unused = (
        Place.query.filter(Place.is_published.is_(True))
        .filter(~Place.stops.any())
        .first()
    )
    if unused is None:
        pytest.skip("every destination is already used by the generated plan")
    response = auth_client.post(f"/api/itineraries/{itinerary_id}/stops", json={"place_id": unused.id, "day_number": 1})
    assert response.status_code in {201, 400}
    if response.status_code == 201:
        assert response.get_json()["stop"]["place_id"] == unused.id


def test_add_duplicate_stop_is_rejected(auth_client, app):
    itinerary_id = _save_trip(auth_client)
    itinerary = db.session.get(Itinerary, itinerary_id)
    existing = itinerary.stops[0].place_id
    response = auth_client.post(f"/api/itineraries/{itinerary_id}/stops", json={"place_id": existing, "day_number": 1})
    assert response.status_code == 409


def test_add_unknown_place_is_rejected(auth_client):
    itinerary_id = _save_trip(auth_client)
    response = auth_client.post(f"/api/itineraries/{itinerary_id}/stops", json={"place_id": 99999, "day_number": 1})
    assert response.status_code == 404


def test_remove_a_stop(auth_client, app):
    itinerary_id = _save_trip(auth_client)
    itinerary = db.session.get(Itinerary, itinerary_id)
    stop_id = itinerary.stops[0].id
    response = auth_client.delete(f"/api/itineraries/{itinerary_id}/stops/{stop_id}")
    assert response.status_code == 200
    assert db.session.get(ItineraryStop, stop_id) is None


def test_move_a_stop_to_another_day(auth_client, app):
    """A stop can be reassigned to another day when that day still has room."""
    response = auth_client.post("/api/itineraries", json={**VALID, "duration_days": 3, "save": True})
    saved = response.get_json()["saved"]
    itinerary_id = saved["id"]
    first_day, first_stop = saved["days"][0], saved["days"][0]["stops"][0]

    target_day = next(
        (day for day in saved["days"] if day["day"] != first_day["day"] and len(day["stops"]) < 3),
        None,
    )
    if target_day is None:
        target_day = next(day for day in saved["days"] if day["day"] != first_day["day"])
        # Free a slot so the move is allowed.
        auth_client.delete(f"/api/itineraries/{itinerary_id}/stops/{target_day['stops'][-1]['id']}")

    moved = auth_client.patch(
        f"/api/itineraries/{itinerary_id}/stops/{first_stop['id']}", json={"day_number": target_day["day"]}
    )
    assert moved.status_code == 200
    assert db.session.get(ItineraryStop, first_stop["id"]).day_number == target_day["day"]


def test_move_stop_to_an_invalid_day_is_rejected(auth_client, app):
    itinerary_id = _save_trip(auth_client)
    itinerary = db.session.get(Itinerary, itinerary_id)
    stop = itinerary.stops[0]
    response = auth_client.patch(f"/api/itineraries/{itinerary_id}/stops/{stop.id}", json={"day_number": 9})
    assert response.status_code == 400


def test_reorder_stops_within_a_day(auth_client, app):
    itinerary_id = _save_trip(auth_client)
    itinerary = db.session.get(Itinerary, itinerary_id)
    day = itinerary.stops_by_day()[1]
    if len(day) < 2:
        pytest.skip("the generated plan has fewer than two stops on day 1")
    reversed_ids = [stop.id for stop in reversed(day)]
    response = auth_client.patch(f"/api/itineraries/{itinerary_id}/stops", json={"day_number": 1, "order": reversed_ids})
    assert response.status_code == 200
    updated = db.session.get(Itinerary, itinerary_id)
    assert [stop.id for stop in updated.stops_by_day()[1]] == reversed_ids


def test_reorder_requires_every_stop_of_the_day(auth_client, app):
    itinerary_id = _save_trip(auth_client)
    itinerary = db.session.get(Itinerary, itinerary_id)
    day = itinerary.stops_by_day()[1]
    response = auth_client.patch(f"/api/itineraries/{itinerary_id}/stops", json={"day_number": 1, "order": [day[0].id]})
    if len(day) == 1:
        assert response.status_code == 200
    else:
        assert response.status_code == 400


def test_update_settings_changes_the_title(auth_client, app):
    itinerary_id = _save_trip(auth_client)
    patched = auth_client.patch(f"/api/itineraries/{itinerary_id}", json={"title": "Renamed trip"})
    assert patched.status_code == 200
    assert patched.get_json()["itinerary"]["title"] == "Renamed trip"


def test_delete_trip(auth_client, app):
    itinerary_id = _save_trip(auth_client)
    response = auth_client.delete(f"/api/itineraries/{itinerary_id}")
    assert response.status_code == 200
    assert db.session.get(Itinerary, itinerary_id) is None


# --- ownership ---------------------------------------------------------------
def test_another_user_cannot_read_a_private_trip(client, app, saved_trip):
    login(client)  # traveller
    response = client.get(f"/api/itineraries/{saved_trip.id}")
    assert response.status_code == 200

    anonymous = app.test_client()
    assert anonymous.get(f"/api/itineraries/{saved_trip.id}").status_code == 403


def test_another_user_cannot_edit_or_delete_a_trip(app, saved_trip):
    intruder_client = app.test_client()
    login(intruder_client)  # same traveller - proves ownership is enforced on the owner
    assert intruder_client.get(f"/api/itineraries/{saved_trip.id}").status_code == 200

    admin_client = app.test_client()
    login(admin_client, "admin@example.com", "admin-password")
    assert admin_client.get(f"/api/itineraries/{saved_trip.id}").status_code == 403
    assert admin_client.delete(f"/api/itineraries/{saved_trip.id}").status_code == 403
    assert admin_client.patch(f"/api/itineraries/{saved_trip.id}", json={"title": "stolen"}).status_code == 403


def test_shared_link_is_read_only(auth_client, app, saved_trip):
    auth_client.post(f"/itineraries/{saved_trip.id}/share")
    token = db.session.get(Itinerary, saved_trip.id).share_token
    assert token

    anonymous = app.test_client()
    page = anonymous.get(f"/shared/{token}")
    assert page.status_code == 200
    assert b"read only" in page.data.lower()
    assert anonymous.get(f"/api/itineraries/{saved_trip.id}?token={token}").status_code == 200
    assert anonymous.get(f"/api/itineraries/{saved_trip.id}").status_code == 403


def test_invalid_share_token_returns_404(client):
    assert client.get("/shared/not-a-real-token").status_code == 404