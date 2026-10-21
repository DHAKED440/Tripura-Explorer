"""Local experiences directory and inquiry handling."""
from app.models import Business, Inquiry
from app.services.local_experience_search import (
    OSMServiceError,
    SearchResults,
    _normalize_element,
    _overpass_query,
    search_nearby,
)
from app.models import OSMRestaurant
from unittest.mock import MagicMock, patch
import json
import pytest
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit


def test_seeded_provider_records_are_not_presented_as_live_businesses(client, app):
    body = client.get("/experiences").data
    for provider in Business.query.filter_by(approval_status="approved").all():
        assert provider.name.encode() not in body
    for provider in Business.query.filter_by(approval_status="pending").all():
        assert provider.name.encode() not in body


def test_pending_provider_detail_is_hidden(client, app):
    pending = Business.query.filter_by(approval_status="pending").first()
    assert client.get(f"/experiences/{pending.slug}").status_code == 404


def test_approved_provider_detail_renders(client, app):
    approved = Business.query.filter_by(approval_status="approved").first()
    response = client.get(f"/experiences/{approved.slug}")
    assert response.status_code == 200
    assert b"Send an inquiry" in response.data


def test_inquiry_filters_by_category_and_district(client):
    body = client.get("/experiences?category=Food%20%26%20Restaurants").data
    assert b"Destination in Tripura" in body
    assert b"Food &amp; Restaurants" in body
    assert b"Demo Homestay" not in body


def test_valid_inquiry_is_stored(client, app):
    approved = Business.query.filter_by(approval_status="approved").first()
    response = client.post(
        "/api/inquiries",
        json={
            "business_id": approved.id,
            "name": "Prospective Guest",
            "email": "guest@example.com",
            "phone": "+91 00000 00000",
            "message": "Do you have a room for two nights in December?",
        },
    )
    assert response.status_code == 201
    inquiry = Inquiry.query.filter_by(business_id=approved.id).first()
    assert inquiry is not None
    assert inquiry.status == "new"


def test_invalid_inquiry_is_rejected(client, app):
    approved = Business.query.filter_by(approval_status="approved").first()
    response = client.post(
        "/api/inquiries",
        json={"business_id": approved.id, "name": "X", "email": "not-an-email", "message": "hi"},
    )
    assert response.status_code == 400
    assert len(response.get_json()["errors"]) >= 2
    assert Inquiry.query.count() == 0


def test_inquiry_for_unknown_provider(client):
    response = client.post(
        "/api/inquiries",
        json={"business_id": 999999, "name": "Someone", "email": "a@b.com", "message": "Hello there."},
    )
    assert response.status_code == 404


def test_inquiry_form_works_without_javascript(client, app):
    approved = Business.query.filter_by(approval_status="approved").first()
    response = client.post(
        f"/experiences/{approved.slug}/inquire",
        data={"name": "Form User", "email": "form@example.com", "message": "Please share your rates."},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert Inquiry.query.filter_by(business_id=approved.id).count() == 1


def test_inquiry_personal_data_is_not_public(client, app):
    approved = Business.query.filter_by(approval_status="approved").first()
    client.post(
        "/api/inquiries",
        json={
            "business_id": approved.id,
            "name": "Private Person",
            "email": "private@example.com",
            "message": "I would like to know more about this stay.",
        },
    )
    body = client.get(f"/experiences/{approved.slug}").data
    assert b"private@example.com" not in body
    assert b"Private Person" not in body


def test_public_provider_page_has_no_admin_controls(client):
    approved = Business.query.filter_by(approval_status="approved").first()
    body = client.get(f"/experiences/{approved.slug}").data
    assert b"Approve" not in body


def test_experiences_page_offers_tripura_presets_and_no_seed_providers(client):
    body = client.get("/experiences").data
    assert b"Neermahal" in body
    assert b"Dumboor Lake, Gandacherra, Tripura, India" in body
    assert b"Gumti Wildlife Sanctuary, Mukchhari, Tripura, India" in body
    assert b'data-destination="Udaipur, Tripura' not in body
    assert b"Rowa Wildlife Sanctuary" not in body
    assert b'<select id="destination" name="destination"' in body
    assert b"All types" in body
    from app.models import Place
    assert body.count(b"<option value=") >= Place.query.filter_by(is_published=True).count()
    assert b"Demo" not in body


def test_local_experiences_search_defaults_to_dumboor_and_25km(client):
    page = client.get("/experiences").get_data(as_text=True)
    assert 'name="radius"' in page
    assert 'value="25" selected' in page
    assert "GOOGLE_MAPS_API_KEY" not in page
    assert "Dumboor Lake, Gandacherra, Tripura, India" in page
    assert "OpenStreetMap" in page


def test_local_experiences_current_location_uses_backend_search_without_keys(client):
    page = client.get("/experiences").get_data(as_text=True)
    assert 'method="post"' in page
    assert "Use my location" in page

    result = {"id": "node/42", "osm_type": "node", "osm_id": 42, "name": "Provider result", "category": "Food & Restaurants",
              "address": "Agartala", "distance_km": 1.2, "raw_tags": {}, "latitude": 23.83, "longitude": 91.28,
              "directions": "/map?lat=23.83&lng=91.28&name=Provider+result"}
    with patch("app.routes.experiences.search_nearby", return_value=[result]) as search:
        response = client.post("/experiences", data={
            "csrf_token": "", "search": "1", "origin": "current", "latitude": "23.83",
            "longitude": "91.28", "category": "Food & Restaurants", "radius": "25", "keyword": "",
        })
    assert response.status_code == 200
    assert b"1.2 km straight-line" in response.data
    assert "Current location" in response.get_data(as_text=True)
    assert search.call_args.args[:4] == (23.83, 91.28, 25, "Food & Restaurants")


def test_geocode_api_resolves_submitted_destination_and_returns_attribution(client):
    with patch("app.routes.experiences.geocode_destination", return_value={"name": "Dumboor Lake", "latitude": 23.53, "longitude": 91.82}):
        response = client.get("/api/local-experiences/geocode?q=Dumboor%20Lake%2C%20Tripura")
    assert response.status_code == 200
    assert response.get_json()["result"]["latitude"] == 23.53
    assert "OpenStreetMap" in response.get_json()["attribution"]


def test_published_tripura_destination_uses_saved_coordinates_without_external_geocoder(app):
    from app.services.local_experience_search import geocode_destination

    with app.app_context(), patch("app.services.local_experience_search.urlopen", side_effect=AssertionError("should use local place coordinates")):
        result = geocode_destination("Dumboor Lake, Gandacherra, Tripura, India")
    assert result["name"] == "Dumboor Lake"
    assert result["latitude"] == pytest.approx(23.468)
    assert result["longitude"] == pytest.approx(91.845)
    assert result["source"] == "Tripura Explorer published destination"


def test_custom_destination_geocoder_biases_tripura_and_accepts_bounded_local_result(app):
    from app.services.local_experience_search import geocode_destination

    payload = [{"lat": "23.83", "lon": "91.28", "display_name": "Agartala, India", "address": {}}]
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
    with app.app_context(), patch("app.services.local_experience_search.urlopen", return_value=response) as upstream, \
         patch("app.services.local_experience_search.time.sleep"):
        result = geocode_destination("Agartala Railway Station")
    assert result["name"] == "Agartala, India"
    assert parse_qs(urlsplit(upstream.call_args.args[0].full_url).query)["q"] == [
        "Agartala Railway Station, Tripura, India"
    ]


def test_nearby_api_accepts_verified_coordinates_and_validates_radius(client):
    record = {"id": "node/42", "osm_type": "node", "osm_id": 42, "name": "Cafe", "distance_km": 1.0}
    with patch("app.routes.experiences.search_nearby", return_value=[record]) as search:
        response = client.get("/api/local-experiences?lat=23.53&lon=91.82&radius=25&category=All%20Places")
    assert response.status_code == 200
    assert response.get_json()["results"][0]["id"] == "node/42"
    assert response.get_json()["attribution"] == "© OpenStreetMap contributors"
    assert search.call_args.args[:4] == (23.53, 91.82, 25, "All Places")
    assert client.get("/api/local-experiences?lat=23.53&lon=91.82&radius=99").status_code == 400


def test_overpass_parser_uses_combined_tags_and_exact_distance_filter(app):
    payload = {"elements": [
        {"type": "node", "id": 10, "lat": 23.53, "lon": 91.82, "tags": {"name": "Nearby Cafe", "amenity": "cafe", "cuisine": "bengali", "phone": "123"}},
        {"type": "way", "id": 11, "center": {"lat": 23.531, "lon": 91.821}, "tags": {"name": "Guest House", "tourism": "guest_house", "addr:city": "Melaghar"}},
        {"type": "node", "id": 12, "lat": 23.8, "lon": 91.82, "tags": {"name": "Too far", "amenity": "restaurant"}},
        {"type": "node", "id": 13, "tags": {"name": "No coordinates", "amenity": "restaurant"}},
    ]}
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
    with app.app_context(), patch("app.services.local_experience_search.urlopen", return_value=response) as upstream:
        results = search_nearby(23.53, 91.82, 5, "All Places")
    assert [item["name"] for item in results] == ["Nearby Cafe", "Guest House"]
    assert results[0]["cuisine"] == "bengali"
    assert results[1]["address"] == "Melaghar"
    assert results[1]["osm_type"] == "way"
    query = parse_qs(upstream.call_args.args[0].data.decode())["data"][0]
    assert "nwr(around:5000,23.5300000,91.8200000)" in query
    assert query.count("nwr(around:") < 12
    assert "/map?lat=" in results[0]["directions"]


def test_unresolved_destination_shows_clear_location_error_without_fake_results(client):
    with patch("app.routes.experiences.geocode_destination", return_value=None):
        response = client.post("/experiences", data={"search": "1", "destination": "Unknown place", "category": "All Places", "radius": "25"})
    assert response.status_code == 200
    assert b"Could not find this destination in Tripura" in response.data
    assert b"Google Places" not in response.data


@pytest.mark.parametrize("category,tag,value", [
    ("All Places", "amenity", "restaurant"),
    ("Accommodation", "tourism", "hotel"),
    ("Food & Restaurants", "amenity", "restaurant"),
    ("Tourist Attractions", "tourism", "attraction"),
    ("Local Guide", "office", "guide"),
    ("Useful Services", "amenity", "fuel"),
])
def test_each_place_type_builds_a_category_specific_overpass_query(category, tag, value):
    query = _overpass_query(23.83, 91.28, 10000, category)
    assert f'"{tag}"~' in query
    assert value in query
    assert "nwr(around:10000,23.8300000,91.2800000)" in query
    assert "out center tags" in query


def test_local_guide_query_does_not_return_attractions_as_guides():
    query = _overpass_query(23.83, 91.28, 5000, "Local Guide")
    assert '"office"~"^(guide|travel_agent)$"' in query
    assert "tourism" not in query
    assert "historic" not in query


def test_normalized_osm_result_keeps_missing_business_details_unavailable():
    result = _normalize_element(
        {"type": "node", "id": 17, "lat": 23.83, "lon": 91.28,
         "tags": {"name": "Bengal Cafe", "amenity": "cafe", "cuisine": "bengali"}},
        23.83, 91.28,
    )
    assert result["category"] == "Food & Restaurants"
    assert result["cuisine"] == "bengali"
    assert result["rating"] is None
    assert result["review_count"] is None
    assert result["price"] is None
    assert result["photo"] is None
    assert result["opening_status"] is None


def test_nearby_parser_deduplicates_and_filters_keyword(app):
    payload = {"elements": [
        {"type": "node", "id": 51, "lat": 23.83, "lon": 91.28,
         "tags": {"name": "Bangla Bhoj", "amenity": "restaurant", "cuisine": "bengali"}},
        {"type": "node", "id": 51, "lat": 23.83, "lon": 91.28,
         "tags": {"name": "Bangla Bhoj", "amenity": "restaurant", "cuisine": "bengali"}},
        {"type": "node", "id": 52, "lat": 23.831, "lon": 91.281,
         "tags": {"name": "Other Cafe", "amenity": "cafe"}},
    ]}
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
    with app.app_context(), patch("app.services.local_experience_search.urlopen", return_value=response):
        results = search_nearby(23.83, 91.28, 5, "Food & Restaurants", "bengali")
    assert [item["name"] for item in results] == ["Bangla Bhoj"]


def test_overpass_timeout_has_a_specific_retryable_error(app):
    with app.app_context(), patch("app.services.local_experience_search.urlopen", side_effect=TimeoutError):
        with pytest.raises(OSMServiceError) as caught:
            search_nearby(23.41, 91.61, 5, "Tourist Attractions")
    assert caught.value.provider_status == "timeout"
    assert caught.value.retryable is True
    assert "smaller radius" in caught.value.public_message


def test_overpass_rate_limit_is_not_reported_as_a_generic_failure(app):
    rate_limit = HTTPError("https://overpass.example/api", 429, "rate limit", None, None)
    with app.app_context(), patch("app.services.local_experience_search.urlopen", side_effect=rate_limit):
        with pytest.raises(OSMServiceError) as caught:
            search_nearby(23.42, 91.62, 5, "Useful Services")
    assert caught.value.provider_status == "rate_limited"
    assert caught.value.http_status == 429
    assert caught.value.retryable is True


def test_api_successful_food_search_returns_normalized_results_and_real_directions(client):
    result = {"id": "node/321", "osm_type": "node", "osm_id": 321, "name": "Pahuna Dining",
              "category": "Food & Restaurants", "latitude": 23.83, "longitude": 91.28,
              "distance_km": 0.0, "rating": None, "review_count": None, "price": None,
              "photo": None, "raw_tags": {"amenity": "restaurant", "cuisine": "bengali"},
              "osm_url": "https://www.openstreetmap.org/node/321",
              "directions": "/map?lat=23.8300000&lng=91.2800000&name=Pahuna&directions=1"}
    with patch("app.routes.experiences.search_nearby", return_value=[result]) as search:
        response = client.get("/api/local-experiences?lat=23.83&lon=91.28&radius=10&category=Food%20%26%20Restaurants&keyword=bengali")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["result_count"] == 1
    assert payload["results"][0]["name"] == "Pahuna Dining"
    assert "directions=1" in payload["results"][0]["directions"]
    assert search.call_args.args[2:] == (10, "Food & Restaurants", "bengali")


def test_food_search_persists_osm_restaurant_and_details_can_load_from_model(client):
    from app.services.local_experience_search import find_cached_place

    result = {
        "id": "way/904", "osm_type": "way", "osm_id": 904, "name": "Tripura Bhoj",
        "category": "Food & Restaurants", "latitude": 23.83, "longitude": 91.28,
        "distance_km": 0.0, "address": "Agartala", "description": "Local cuisine",
        "cuisine": "bengali", "opening_hours": "Mo-Su 09:00-21:00", "phone": "+913812123456",
        "website": "https://example.org", "email": "hello@example.org", "operator": "Local operator",
        "brand": None, "takeaway": "yes", "delivery": None, "dine_in": "yes", "wheelchair": "yes",
        "image_url": "https://example.org/restaurant.jpg", "photo": "https://example.org/restaurant.jpg",
        "raw_tags": {"amenity": "restaurant", "cuisine": "bengali"},
        "osm_url": "https://www.openstreetmap.org/way/904",
        "directions": "/map?lat=23.8300000&lng=91.2800000&directions=1",
        "external_directions": "https://www.google.com/maps/dir/?api=1&destination=23.83%2C91.28",
    }
    with patch("app.routes.experiences.search_nearby", return_value=[result]):
        response = client.get("/api/local-experiences?lat=23.83&lon=91.28&radius=10&category=Food%20%26%20Restaurants")
    assert response.status_code == 200
    saved = OSMRestaurant.query.filter_by(osm_type="way", osm_id="904").one()
    assert saved.cuisine == "bengali"
    assert saved.opening_hours == "Mo-Su 09:00-21:00"
    assert saved.raw_tags["amenity"] == "restaurant"
    with patch("app.routes.experiences.find_cached_place", return_value=None):
        details = client.get("/api/local-experiences/place/way/904")
    assert details.status_code == 200
    assert details.get_json()["name"] == "Tripura Bhoj"
    assert details.get_json()["photo"] == "https://example.org/restaurant.jpg"


def test_flask_experiences_page_also_saves_discovered_restaurants(client):
    item = {
        "id": "node/905", "osm_type": "node", "osm_id": 905, "name": "Agartala Cafe",
        "category": "Food & Restaurants", "latitude": 23.83, "longitude": 91.28,
        "distance_km": 0.0, "raw_tags": {"amenity": "cafe"},
        "osm_url": "https://www.openstreetmap.org/node/905",
    }
    with patch("app.routes.experiences.geocode_destination", return_value={"name": "Agartala", "latitude": 23.83, "longitude": 91.28}), \
         patch("app.routes.experiences.search_nearby", return_value=[item]):
        response = client.post("/experiences", data={
            "search": "1", "origin": "destination", "destination": "Agartala, Tripura, India",
            "category": "Food & Restaurants", "radius": "10",
        })
    assert response.status_code == 200
    assert OSMRestaurant.query.filter_by(osm_type="node", osm_id="905").one().name == "Agartala Cafe"


def test_api_returns_empty_search_as_a_valid_empty_result(client):
    with patch("app.routes.experiences.search_nearby", return_value=[]):
        response = client.get("/api/local-experiences?lat=23.83&lon=91.28&radius=5&category=Useful%20Services")
    assert response.status_code == 200
    assert response.get_json()["results"] == []
    assert response.get_json()["result_count"] == 0


def test_api_paginates_cached_results_without_claiming_unsupported_totals(client):
    records = SearchResults([
        {"id": f"node/{index}", "osm_type": "node", "osm_id": index, "name": f"Place {index}",
         "latitude": 23.83, "longitude": 91.28, "distance_km": float(index)}
        for index in range(26)
    ])
    with patch("app.routes.experiences.search_nearby", return_value=records):
        first = client.get("/api/local-experiences?lat=23.83&lon=91.28&radius=5&page=1").get_json()
        second = client.get("/api/local-experiences?lat=23.83&lon=91.28&radius=5&page=2").get_json()
    assert len(first["results"]) == 24
    assert first["has_more"] is True
    assert first["next_page"] == 2
    assert first["result_count"] == 26
    assert len(second["results"]) == 2
    assert second["has_more"] is False


def test_api_marks_a_capped_result_count_as_inexact(client):
    records = SearchResults([
        {"id": f"node/{index}", "osm_type": "node", "osm_id": index, "name": f"Place {index}",
         "latitude": 23.83, "longitude": 91.28, "distance_km": float(index)}
        for index in range(200)
    ], truncated=True)
    with patch("app.routes.experiences.search_nearby", return_value=records):
        payload = client.get("/api/local-experiences?lat=23.83&lon=91.28&radius=5&page=1").get_json()
    assert payload["result_count"] is None
    assert payload["result_count_is_exact"] is False
    assert payload["result_set_limited"] is True


def test_api_provider_timeout_returns_safe_retryable_error(client):
    with patch("app.routes.experiences.search_nearby", side_effect=OSMServiceError("Search timed out.", "timeout")):
        response = client.get("/api/local-experiences?lat=23.83&lon=91.28&radius=25")
    assert response.status_code == 504
    assert response.get_json()["retryable"] is True
    assert response.get_json()["error_code"] == "timeout"
    assert "stack" not in response.get_json()["error"].lower()


def test_geolocation_permission_denial_has_a_manual_search_path(client):
    page = client.get("/experiences").get_data(as_text=True)
    assert "Location permission was denied" in page
    assert "Choose a destination or enter one manually" in page


def test_destination_form_can_search_unlisted_place_names(client):
    with patch("app.routes.experiences.geocode_destination", return_value={"name": "Agartala Railway Station", "latitude": 23.83, "longitude": 91.28}) as geocode, \
         patch("app.routes.experiences.search_nearby", return_value=[]):
        response = client.post("/experiences", data={
            "search": "1", "destination": "__custom__", "custom_destination": "Agartala Railway Station, Tripura, India",
            "category": "Useful Services", "radius": "10", "keyword": "parking",
        })
    assert response.status_code == 200
    assert geocode.call_args.args[0] == "Agartala Railway Station, Tripura, India"
    assert b"No mapped places found" in response.data


def test_clear_search_link_resets_the_existing_form(client):
    page = client.get("/experiences?category=Accommodation&radius=50&keyword=budget").get_data(as_text=True)
    assert 'href="/experiences"' in page
    reset = client.get("/experiences").get_data(as_text=True)
    assert 'value="25" selected' in reset
    assert 'value="budget"' not in reset
