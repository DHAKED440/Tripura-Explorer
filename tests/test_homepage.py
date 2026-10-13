"""TC-01 · homepage, navigation and the featured place feed."""
from tests.conftest import login


def test_homepage_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hidden Beauty of" in response.data


def test_homepage_contains_navigation_links(client):
    body = client.get("/").data
    for path in [b'href="/explore"', b'href="/map"', b'href="/trip-planner"', b'href="/experiences"']:
        assert path in body


def test_featured_places_render_from_the_database(client, app):
    from app.models import Place

    most_popular = Place.query.filter_by(is_published=True).order_by(Place.popularity.desc()).first()
    body = client.get("/").data
    assert most_popular.name.encode() in body
    assert f"/places/{most_popular.slug}".encode() in body


def test_featured_places_api(client):
    payload = client.get("/api/featured-places").get_json()
    assert payload["places"]
    assert all(item["latitude"] is None or -90 <= item["latitude"] <= 90 for item in payload["places"])
    assert all("url" in item for item in payload["places"])


def test_about_page(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert b"Data and verification" in response.data


def test_categories_carry_their_counts(client):
    body = client.get("/").data
    assert b"Popular Destinations" in body
    assert b"Nature" in body


def test_homepage_without_published_places(client, app):
    """The empty state must not crash when an administrator unpublishes everything."""
    from app.extensions import db
    from app.models import Place

    Place.query.update({"is_published": False})
    db.session.commit()
    response = client.get("/")
    assert response.status_code == 200
    assert b"No destinations published yet" in response.data


def test_signed_in_navigation_shows_saved_trips(client):
    login(client)
    body = client.get("/").data
    assert b"Saved Trips" in body