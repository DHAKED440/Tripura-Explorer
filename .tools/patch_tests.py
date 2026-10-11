import io

path = "tests/test_itineraries.py"
text = io.open(path, encoding="utf-8").read()
old_start = text.index("def test_update_settings_changes_the_title")
old_end = text.index("def test_delete_trip")
new_test = '''def test_update_settings_changes_the_title(auth_client, app):
    itinerary_id = _save_trip(auth_client)
    patched = auth_client.patch(f"/api/itineraries/{itinerary_id}", json={"title": "Renamed trip"})
    assert patched.status_code == 200
    assert patched.get_json()["itinerary"]["title"] == "Renamed trip"


'''
text = text[:old_start] + new_test + text[old_end:]
io.open(path, "w", encoding="utf-8", newline="\n").write(text)

path = "tests/test_places.py"
text = io.open(path, encoding="utf-8").read()
old = '''def test_shop_pages_do_not_expose_unpublished_records(client):
    assert b"draft record" not in client.get("/explore?q=draft").data.lower().replace(b"<", b" ")
'''
new = '''def test_public_pages_never_expose_unpublished_records(client, app):
    draft = Place.query.filter_by(is_published=False).first()
    assert draft.slug.encode() not in client.get("/explore").data
    assert draft.slug.encode() not in client.get("/api/places").data
    assert draft.slug.encode() not in client.get("/api/places/map").data
'''
assert old in text
text = text.replace(old, new, 1)
io.open(path, "w", encoding="utf-8", newline="\n").write(text)
print("tests patched")
