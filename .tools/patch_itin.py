import io
path = "app/routes/itineraries.py"
text = io.open(path, encoding="utf-8").read()

anchor = '@bp.get("/my-trips")'
route = '''@bp.post("/trip-planner/save")
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


'''
assert anchor in text
text = text.replace(anchor, route + anchor, 1)

old_token = '    token = request.args.get("token") or (request.json or {}).get("token") if request.is_json else request.args.get("token")\n'
new_token = '    token = request.args.get("token")\n    if not token and request.is_json:\n        token = (request.get_json(silent=True) or {}).get("token")\n'
assert old_token in text
text = text.replace(old_token, new_token, 1)

io.open(path, "w", encoding="utf-8", newline="\n").write(text)
print("itinerary route patched")
