"""TC-06 · map page and marker data."""
from app.extensions import db
from app.models import Category, Place


def test_map_page_loads(client):
    response = client.get("/map")
    assert response.status_code == 200
    assert b'id="map"' in response.data


def test_map_endpoint_returns_only_published_places_with_coordinates(client, app):
    payload = client.get("/api/places/map").get_json()
    assert payload["count"] > 0
    for marker in payload["places"]:
        assert -90 <= marker["lat"] <= 90
        assert -180 <= marker["lng"] <= 180
        place = Place.query.filter_by(slug=marker["slug"]).first()
        assert place is not None
        assert place.is_published is True


def test_unpublished_places_are_not_markers(client, app):
    draft = Place.query.filter_by(is_published=False).first()
    slugs = [marker["slug"] for marker in client.get("/api/places/map").get_json()["places"]]
    assert draft.slug not in slugs


def test_places_without_coordinates_are_excluded_and_counted(client, app):
    category = Category.query.filter_by(slug="nature").first()
    no_coords = Place(name="No Coordinates", slug="no-coordinates", category_id=category.id, is_published=True)
    db.session.add(no_coords)
    db.session.commit()

    payload = client.get("/api/places/map").get_json()
    assert "no-coordinates" not in [marker["slug"] for marker in payload["places"]]
    assert payload["published_without_coordinates"] >= 1


def test_map_category_filter(client):
    payload = client.get("/api/places/map?category=lakes").get_json()
    assert payload["count"] >= 1
    assert all(marker["category"] == "Lakes" for marker in payload["places"])


def test_map_unknown_category_returns_no_markers(client):
    payload = client.get("/api/places/map?category=unknown").get_json()
    assert payload["count"] == 0


def test_verified_only_filter(client):
    payload = client.get("/api/places/map?verified=1").get_json()
    assert payload["count"] >= 1  # Field-verified coordinates are populated
    assert all(marker["coordinates_verified"] for marker in payload["places"])


def test_marker_payload_shape(client):
    marker = client.get("/api/places/map").get_json()["places"][0]
    for key in ["id", "name", "slug", "lat", "lng", "url", "coordinates_verified"]:
        assert key in marker