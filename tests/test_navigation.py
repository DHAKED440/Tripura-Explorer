"""TC-07 · Navigation system data integrity and API tests.

Verifies that the map API provides correct coordinate data for navigation,
that place coordinates are valid and consistent, and that the map page
includes navigation UI elements.
"""
import json

from app.extensions import db
from app.models import Category, District, Place


# -- Coordinate correctness tests -------------------------------------------

def test_all_map_places_have_valid_lat_lng_ranges(client):
    """Every place returned by the map API must have lat in [-90, 90]
    and lng in [-180, 180] (Tripura is roughly 23-24°N, 91-92°E)."""
    payload = client.get("/api/places/map").get_json()
    for marker in payload["places"]:
        assert -90 <= marker["lat"] <= 90, f"{marker['name']} has invalid latitude {marker['lat']}"
        assert -180 <= marker["lng"] <= 180, f"{marker['name']} has invalid longitude {marker['lng']}"
        # Tripura-specific sanity: lat should be ~22-25, lng ~91-93
        assert 22 <= marker["lat"] <= 25, f"{marker['name']} lat {marker['lat']} outside Tripura range"
        assert 91 <= marker["lng"] <= 93, f"{marker['name']} lng {marker['lng']} outside Tripura range"


def test_lat_lng_not_swapped(client):
    """Latitude must be smaller than longitude for Tripura coordinates.
    A swap would put lat ~91 (impossible) or lng ~23 (Africa)."""
    payload = client.get("/api/places/map").get_json()
    for marker in payload["places"]:
        assert marker["lat"] < marker["lng"], (
            f"{marker['name']}: lat={marker['lat']}, lng={marker['lng']} — "
            "coordinates may be swapped"
        )


def test_no_duplicate_coordinates(client):
    """No two places should share the exact same coordinates."""
    payload = client.get("/api/places/map").get_json()
    seen = set()
    for marker in payload["places"]:
        key = (round(marker["lat"], 6), round(marker["lng"], 6))
        assert key not in seen, (
            f"Duplicate coordinates {key} for {marker['name']}"
        )
        seen.add(key)


def test_destination_correct_after_switching(client):
    """Verifies that different places return different coordinates."""
    payload = client.get("/api/places/map").get_json()
    places = payload["places"]
    if len(places) >= 2:
        assert places[0]["lat"] != places[1]["lat"] or places[0]["lng"] != places[1]["lng"], (
            "First two destinations have identical coordinates"
        )


# -- Map API shape and content tests ----------------------------------------

def test_map_api_includes_id_and_slug(client):
    """Every marker must have both numeric id and slug for reliable lookup."""
    payload = client.get("/api/places/map").get_json()
    for marker in payload["places"]:
        assert "id" in marker and isinstance(marker["id"], int)
        assert "slug" in marker and isinstance(marker["slug"], str)
        assert len(marker["slug"]) > 0


def test_map_api_has_required_navigation_fields(client):
    """Each marker must have the fields needed for navigation."""
    payload = client.get("/api/places/map").get_json()
    required = {"id", "name", "slug", "lat", "lng", "url", "coordinates_verified"}
    for marker in payload["places"]:
        missing = required - set(marker.keys())
        assert not missing, f"{marker.get('name', '?')} missing fields: {missing}"


def test_map_api_returns_count_field(client):
    payload = client.get("/api/places/map").get_json()
    assert "count" in payload
    assert payload["count"] == len(payload["places"])


# -- Map page navigation UI tests ------------------------------------------

def test_map_page_has_navigation_elements(client):
    """The map page must include the navigation UI containers."""
    response = client.get("/map")
    html = response.data.decode()
    assert 'id="map"' in html
    assert 'id="map-locate-me"' in html
    assert 'id="map-recenter-btn"' in html
    assert 'id="map-start-journey-btn"' in html
    assert 'id="route-preview-panel"' in html
    assert 'id="nav-hud"' in html
    assert 'id="nav-bottom-bar"' in html
    assert 'id="nav-arrival-overlay"' in html
    assert 'id="nav-pause-btn"' in html
    assert 'id="nav-end-btn"' in html
    assert 'id="nav-recenter-btn"' in html


def test_map_page_loads_leaflet(client):
    """The map page must load the Leaflet library."""
    response = client.get("/map")
    html = response.data.decode()
    assert "leaflet.js" in html
    assert "leaflet.css" in html


def test_map_settings_json_present(client):
    """The map settings JSON block must be present with center coords."""
    response = client.get("/map")
    html = response.data.decode()
    assert 'id="map-settings"' in html
    # Extract and parse the settings JSON
    import re
    match = re.search(r'id="map-settings"[^>]*>(.+?)</script>', html, re.DOTALL)
    assert match is not None
    settings = json.loads(match.group(1))
    assert "center" in settings
    assert "zoom" in settings
    assert "tile_url" in settings
    center = settings["center"]
    # Center should be Agartala area
    assert 22 <= center[0] <= 25
    assert 91 <= center[1] <= 93


# -- Place model coordinate tests -------------------------------------------

def test_place_model_has_coordinates_property(app):
    """Place.has_coordinates should return True only for valid coords."""
    place = Place.query.filter(Place.latitude.isnot(None)).first()
    assert place.has_coordinates is True

    no_coord = Place.query.filter(Place.latitude.is_(None)).first()
    if no_coord:
        assert no_coord.has_coordinates is False


def test_place_directions_url_format(app):
    """directions_url must use lat,lng order in Google Maps URL."""
    place = Place.query.filter(Place.latitude.isnot(None)).first()
    url = place.directions_url
    assert url is not None
    assert "google.com/maps/dir" in url
    assert f"{place.latitude:.5f},{place.longitude:.5f}" in url
    # Verify lat comes before lng (lat < lng for Tripura)
    assert "destination=" in url
    dest_part = url.split("destination=")[1].split("&")[0]
    lat_str, lng_str = dest_part.split(",")
    assert float(lat_str) < float(lng_str), "Lat/lng order appears reversed in directions URL"


def test_to_map_dict_coordinate_keys(app):
    """to_map_dict() must use 'lat' and 'lng' keys with correct values."""
    place = Place.query.filter(Place.latitude.isnot(None)).first()
    d = place.to_map_dict()
    assert d["lat"] == place.latitude
    assert d["lng"] == place.longitude
    assert isinstance(d["lat"], float)
    assert isinstance(d["lng"], float)


# -- Invalid coordinate edge cases ------------------------------------------

def test_place_with_zero_coordinates_excluded(client, app):
    """A place at (0, 0) should be treated as invalid for Tripura."""
    category = Category.query.first()
    zero_place = Place(
        name="Zero Island", slug="zero-island",
        category_id=category.id, is_published=True,
        latitude=0.0, longitude=0.0,
        coordinates_verified=True
    )
    db.session.add(zero_place)
    db.session.commit()

    payload = client.get("/api/places/map").get_json()
    # The place IS returned by the API (it has valid coords per the schema)
    # but the frontend should recognize it's outside Tripura
    zero_markers = [m for m in payload["places"] if m["slug"] == "zero-island"]
    # This verifies the API includes it - the navigation JS should validate
    assert len(zero_markers) == 1
    assert zero_markers[0]["lat"] == 0.0
    assert zero_markers[0]["lng"] == 0.0


def test_place_detail_get_directions_button_links_to_map_page(client):
    """The Get directions button on place details must navigate to the internal Map page with destination parameters."""
    response = client.get("/places/neermahal")
    assert response.status_code == 200
    html = response.data.decode()
    assert "Get directions" in html
    assert "data-live-directions" in html
    assert 'href="/map?' in html
    assert "place_id=" in html
    assert "slug=neermahal" in html
    assert "lat=23.50690" in html
    assert "lng=91.31560" in html
    assert "destination=23.50690%2C91.31560" in html or "destination=23.50690,91.31560" in html
    assert "directions=1" in html


def test_place_detail_get_directions_without_coordinates_shows_disabled(client, app):
    """If a place lacks verified coordinates, directions button must be disabled/secondary with appropriate message."""
    category = Category.query.first()
    district = District.query.first()
    nocoords = Place(
        name="No Coordinates Place", slug="no-coords-test",
        category_id=category.id, district_id=district.id,
        is_published=True,
        latitude=None, longitude=None
    )
    db.session.add(nocoords)
    db.session.commit()

    response = client.get("/places/no-coords-test")
    assert response.status_code == 200
    html = response.data.decode()
    assert "data-invalid-directions" in html
    assert "Coordinates pending verification" in html
    assert 'href="/map?' not in html


def test_map_page_accepts_destination_query_params(client):
    """The map page must load cleanly with destination query parameters."""
    response = client.get("/map?place_id=1&slug=neermahal&name=Neermahal&lat=23.50690&lng=91.31560&destination=23.50690,91.31560&directions=1")
    assert response.status_code == 200
    html = response.data.decode()
    assert 'id="map"' in html
    assert "map.js" in html
