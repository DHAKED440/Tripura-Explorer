import io
path = "tests/test_itineraries.py"
text = io.open(path, encoding="utf-8").read()
start = text.index("def test_move_a_stop_to_another_day")
end = text.index("def test_move_stop_to_an_invalid_day_is_rejected")
new = '''def test_move_a_stop_to_another_day(auth_client, app):
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


'''
io.open(path, "w", encoding="utf-8", newline="\n").write(text[:start] + new + text[end:])
print("move-stop test rewritten")
