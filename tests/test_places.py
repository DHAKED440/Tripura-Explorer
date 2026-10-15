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


def test_trishna_uses_recovered_plus_code_coordinates_and_numeric_directions(app):
    trishna = Place.query.filter_by(slug="trishna-wildlife-sanctuary").one()

    assert trishna.plus_code == "7CH2+PFW"
    assert trishna.address == (
        "7CH2+PFW, Belonia - Bhabanipur Rd, Rajnagar, Joychandrapur, Tripura 799150"
    )
    assert trishna.latitude == pytest.approx(23.2793625)
    assert trishna.longitude == pytest.approx(91.401203125)
    assert trishna.coordinates_verified is False
    assert trishna.directions_url == (
        "https://www.google.com/maps/dir/?api=1&destination=23.27936,91.40120&travelmode=driving"
    )

    api_place = trishna.to_dict()
    assert api_place["plus_code"] == trishna.plus_code
    assert api_place["address"] == trishna.address
    assert api_place["latitude"] == trishna.latitude
    assert api_place["longitude"] == trishna.longitude


def test_trishna_detail_uses_numeric_destination_for_live_directions(client):
    response = client.get("/places/trishna-wildlife-sanctuary")
    html = response.data

    assert response.status_code == 200
    assert b'data-live-directions' in html
    assert b'data-lat="23.27936"' in html
    assert b'data-lng="91.40120"' in html
    assert b'destination=23.27936,91.40120' in html
    assert b'destination=7CH2%2BPFW' not in html


def test_place_detail_renders_live_directions_attributes(client, place):
    response = client.get(f"/places/{place.slug}")
    assert response.status_code == 200
    assert b"data-live-directions" in response.data
    assert f'data-lat="{place.latitude:.5f}"'.encode() in response.data
    assert f'data-lng="{place.longitude:.5f}"'.encode() in response.data
    assert b"Get directions" in response.data


def test_rudrasagar_and_neermahal_have_distinct_correct_coordinates(app):
    """Rudrasagar Lake and Neermahal must have distinct, verified GPS coordinates and URLs."""
    rudrasagar = Place.query.filter_by(slug="rudrasagar-lake").first()
    neermahal = Place.query.filter_by(slug="neermahal").first()

    assert rudrasagar is not None, "Rudrasagar Lake must exist in the database"
    assert neermahal is not None, "Neermahal must exist in the database"
    assert rudrasagar.id != neermahal.id
    assert rudrasagar.name == "Rudrasagar Lake"
    assert neermahal.name == "Neermahal"

    # Distinct verified coordinates
    assert round(rudrasagar.latitude, 4) == 23.5042
    assert round(rudrasagar.longitude, 4) == 91.3150
    assert round(neermahal.latitude, 4) == 23.5069
    assert round(neermahal.longitude, 4) == 91.3156
    assert (rudrasagar.latitude, rudrasagar.longitude) != (neermahal.latitude, neermahal.longitude)

    # Distinct Google Maps URLs
    assert rudrasagar.directions_url != neermahal.directions_url
    assert "destination=23.50420,91.31500" in rudrasagar.directions_url
    assert "destination=23.50690,91.31560" in neermahal.directions_url


def test_every_published_place_has_unique_verified_coordinates_and_url(app):
    """Every published place must have its own distinct coordinates and valid directions URL."""
    places = Place.query.filter_by(is_published=True).all()
    assert len(places) >= 16

    coords_seen = set()
    for p in places:
        assert p.latitude is not None and p.longitude is not None, f"{p.name} missing coordinates"
        assert 22.0 <= p.latitude <= 25.0, f"{p.name} latitude {p.latitude} outside Tripura"
        assert 91.0 <= p.longitude <= 93.0, f"{p.name} longitude {p.longitude} outside Tripura"
        assert p.latitude < p.longitude, f"{p.name} coordinates appear swapped"

        coord_key = (round(p.latitude, 4), round(p.longitude, 4))
        assert coord_key not in coords_seen, f"Duplicate coordinates {coord_key} found for {p.name}"
        coords_seen.add(coord_key)

        url = p.directions_url
        assert url is not None
        assert url.startswith("https://www.google.com/maps/dir/?api=1&destination=")
        assert f"{p.latitude:.5f},{p.longitude:.5f}" in url
        assert url.endswith("&travelmode=driving")


def test_place_without_coordinates_returns_none_for_directions_url(app):
    """Places without verified coordinates must return None instead of ambiguous text query."""
    category = Category.query.first()
    district = District.query.first()
    unmapped = Place(
        name="Unmapped Destination",
        slug="unmapped-destination",
        category_id=category.id,
        district_id=district.id,
        is_published=True,
        latitude=None,
        longitude=None,
    )
    db.session.add(unmapped)
    db.session.commit()

    assert unmapped.has_coordinates is False
    assert unmapped.directions_url is None
    assert unmapped.get_google_maps_url() is None
    assert unmapped.get_google_maps_url(23.83, 91.28) is None


def test_get_google_maps_url_with_origin(place):
    """get_google_maps_url must accept and format valid origin coordinates."""
    url = place.get_google_maps_url(origin_lat=23.8374, origin_lng=91.2827)
    assert url is not None
    assert f"destination={place.latitude:.5f},{place.longitude:.5f}" in url
    assert "origin=23.83740,91.28270" in url
    assert "travelmode=driving" in url


def test_place_detail_renders_rudrasagar_lake_exact_destination(client):
    """The place detail page for Rudrasagar Lake must render its own exact coordinates."""
    response = client.get("/places/rudrasagar-lake")
    assert response.status_code == 200
    assert b"Rudrasagar Lake" in response.data
    assert b'data-lat="23.50420"' in response.data
    assert b'data-lng="91.31500"' in response.data
    assert b'destination=23.50420,91.31500' in response.data
    assert b"Neermahal water palace" in response.data or b"Rudrasagar" in response.data


def test_jampui_hills_detail_uses_kanchanpur_coordinates_and_directions(client, app):
    """Jampui Hills must direct to Kanchanpur sub-division along the Mizoram border (23.96677, 92.27516), never YMA Hall."""
    jampui = Place.query.filter_by(slug="jampui-hills").one()
    assert round(jampui.latitude, 5) == 23.96677
    assert round(jampui.longitude, 5) == 92.27516
    assert "Kanchanpur" in jampui.address
    assert "799269" in jampui.address
    assert jampui.plus_code == "X78G+P3"
    assert "destination=23.96677,92.27516" in jampui.directions_url
    assert "travelmode=driving" in jampui.directions_url
    assert "X7QH" not in jampui.directions_url
    assert "YMA Hall" not in jampui.directions_url

    response = client.get("/places/jampui-hills")
    html = response.data.decode()
    assert response.status_code == 200
    assert "data-live-directions" in html
    assert 'data-lat="23.96677"' in html
    assert 'data-lng="92.27516"' in html
    assert "Kanchanpur" in html
    assert "799269" in html
    assert "destination=23.96677,92.27516" in html
    assert "X7QH" not in html
    assert "YMA Hall" not in html

