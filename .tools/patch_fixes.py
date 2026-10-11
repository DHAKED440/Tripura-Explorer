import io

# 1. Flask-Login caches the user on ``g``; a long-lived app context in tests reuses it.
path = "app/__init__.py"
text = io.open(path, encoding="utf-8").read()
text = text.replace(
    "from flask import Flask, render_template\n",
    "from flask import Flask, g, render_template\n",
    1,
)
old = """    if app.config.get("TESTING"):
        # Session protection relies on client IP/user agent, which the Flask test
        # client does not vary. Turning it off keeps the tests deterministic.
        login_manager.session_protection = None
"""
new = """    if app.config.get("TESTING"):
        # Session protection relies on client IP/user agent, which the Flask test
        # client does not vary. Turning it off keeps the tests deterministic.
        login_manager.session_protection = None

        @app.before_request
        def _reset_test_login_state():
            # A test can run several clients inside one long-lived app context, so
            # purge the user Flask-Login cached on ``g`` during a previous request.
            # Production requests always get a fresh context and never need this.
            g.pop("_login_user", None)
"""
assert old in text
text = text.replace(old, new, 1)
io.open(path, "w", encoding="utf-8", newline="\n").write(text)

# 2. A unique (itinerary, day, order) index fights with re-ordering stops; a unique
#    (itinerary, place) index enforces the rule that matters (no duplicate stops).
path = "app/models/itinerary.py"
text = io.open(path, encoding="utf-8").read()
old = """        UniqueConstraint("itinerary_id", "day_number", "stop_order", name="uq_stop_day_order"),
        CheckConstraint("day_number >= 1 AND day_number <= 3", name="ck_stops_day"),"""
new = """        # A stop cannot appear twice in the same trip. The day/order pair is
        # re-numbered by Itinerary.normalise_stops() instead of being locked by a
        # unique index, because re-ordering inside a day would violate it.
        UniqueConstraint("itinerary_id", "place_id", name="uq_stops_itinerary_place"),
        CheckConstraint("day_number >= 1 AND day_number <= 3", name="ck_stops_day"),"""
assert old in text
text = text.replace(old, new, 1)
io.open(path, "w", encoding="utf-8", newline="\n").write(text)

# 3. Test fixes.
path = "tests/test_itineraries.py"
text = io.open(path, encoding="utf-8").read()
old = """def test_move_a_stop_to_another_day(auth_client, app):
    itinerary_id = _save_trip(auth_client)
    itinerary = db.session.get(Itinerary, itinerary_id)
    stop = itinerary.stops[0]
    response = auth_client.patch(
        f"/api/itineraries/{itinerary_id}/stops/{stop.id}", json={"day_number": 2}
    )
    assert response.status_code == 200
    assert db.session.get(ItineraryStop, stop.id).day_number == 2
"""
new = """def test_move_a_stop_to_another_day(auth_client, app):
    # Use a three day trip so the target day has a free slot.
    response = auth_client.post("/api/itineraries", json={**VALID, "duration_days": 3, "save": True})
    itinerary_id = response.get_json()["saved"]["id"]
    itinerary = db.session.get(Itinerary, itinerary_id)
    stop = itinerary.stops[0]
    moved = auth_client.patch(
        f"/api/itineraries/{itinerary_id}/stops/{stop.id}", json={"day_number": 3}
    )
    assert moved.status_code == 200
    assert db.session.get(ItineraryStop, stop.id).day_number == 3
"""
assert old in text
text = text.replace(old, new, 1)
io.open(path, "w", encoding="utf-8", newline="\n").write(text)

path = "tests/test_search.py"
text = io.open(path, encoding="utf-8").read()
old = """    assert b"Neermahal" in response.data
    assert b"Unakoti" not in response.data"""
new = """    assert b"Neermahal" in response.data
    # "Unakoti" also appears in the district filter, so check the result links.
    assert b'href="/places/unakoti"' not in response.data"""
assert old in text
text = text.replace(old, new, 1)
io.open(path, "w", encoding="utf-8", newline="\n").write(text)
print("patched app, model and tests")
