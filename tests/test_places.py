"""TC-04, TC-05 · destination details, 404 handling and the place API."""
import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Place, Category, District


def test_valid_slug_shows_the_destination(client, place):
    response = client.get(f"/places/{place.slug}")
    assert response.status_code == 200
    assert place.name.encode() in response.data
    assert b"Get directions" in response.data


def test_unknown_slug_returns_404(client):
    response = client.get("/places/this-place-does-not-exist")
    assert response.status_code == 404
    assert b"We could not find that page" in response.data


def test_unpublished_place_is_hidden(client, app):
    draft = Place.query.filter_by(is_published=False).first()
    assert draft is not None
    response = client.get(f"/places/{draft.slug}")
    assert response.status_code == 404


def test_place_without_optional_data_still_renders(client, app):
    category = Category.query.filter_by(slug="nature").first()
    district = District.query.filter_by(slug="khowai").first()
    bare = Place(
        name="Bare Record",
        slug="bare-record",
        short_description=None,
        description=None,
        category_id=category.id,
        district_id=district.id,
        is_published=True,
    )
    db.session.add(bare)
    db.session.commit()

    response = client.get("/places/bare-record")
    assert response.status_code == 200
    assert b"Bare Record" in response.data
    assert b"Not verified" in response.data


def test_public_pages_never_expose_unpublished_records(client, app):
    draft = Place.query.filter_by(is_published=False).first()
    assert draft.slug.encode() not in client.get("/explore").data
    assert draft.slug.encode() not in client.get("/api/places").data
    assert draft.slug.encode() not in client.get("/api/places/map").data


def test_place_api_returns_admin_fields(client, place):
    payload = client.get(f"/api/places/{place.slug}").get_json()["place"]
    assert payload["slug"] == place.slug
    assert "is_published" in payload
    assert payload["is_published"] is True


def test_place_api_unknown_slug(client):
    response = client.get("/api/places/nope")
    assert response.status_code == 404
    assert response.get_json()["error"]


def test_latitude_range_is_enforced_by_the_database(app):
    category = Category.query.filter_by(slug="nature").first()
    broken = Place(name="Broken", slug="broken", category_id=category.id, latitude=120.0, longitude=91.0)
    db.session.add(broken)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_correction_report_is_stored(client, app, place):
    from app.models import CorrectionReport

    response = client.post(
        f"/places/{place.slug}/report",
        data={"message": "The opening hours are wrong.", "reporter_email": "visitor@example.com"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    report = CorrectionReport.query.filter_by(place_id=place.id).first()
    assert report is not None
    assert report.status == "new"


def test_short_correction_report_is_rejected(client, app, place):
    from app.models import CorrectionReport

    client.post(f"/places/{place.slug}/report", data={"message": "bad"}, follow_redirects=True)
    assert CorrectionReport.query.filter_by(place_id=place.id).count() == 0


def test_directions_url_structure(place):
    url = place.directions_url
    assert url is not None
    assert "https://www.google.com/maps/dir/?api=1" in url
    assert "travelmode=driving" in url
    assert f"destination={place.latitude:.5f},{place.longitude:.5f}" in url


def test_place_detail_renders_live_directions_attributes(client, place):
    response = client.get(f"/places/{place.slug}")
    assert response.status_code == 200
    assert b"data-live-directions" in response.data
    assert f'data-lat="{place.latitude:.5f}"'.encode() in response.data
    assert f'data-lng="{place.longitude:.5f}"'.encode() in response.data
    assert b"Get directions" in response.data