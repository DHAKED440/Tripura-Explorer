"""Local experiences directory and inquiry handling."""
from app.models import Business, Inquiry
from app.services.local_experience_search import search_nearby
from unittest.mock import MagicMock, patch
import json
from io import BytesIO
from urllib.error import HTTPError


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
    body = client.get("/experiences?category=Homestay").data
    assert b"Choose destination to travel to" in body
    assert b"Homestay" in body
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


def test_experiences_page_offers_verified_destinations_and_no_seed_providers(client):
    body = client.get("/experiences").data
    assert b"Neermahal" in body
    assert b"Choose destination to travel to" in body
    assert b"Demo" not in body


def test_local_experiences_search_omits_radius_and_posts_location_to_this_app(client):
    page = client.get("/experiences").get_data(as_text=True)
    assert 'name="radius"' not in page
    assert "Search radius" not in page
    assert 'method="post"' in page
    assert "Use my location" in page

    result = {"id": "ChIJ-live", "name": "Provider result", "category": "Restaurant",
              "address": "Agartala", "distance_km": 1.2, "search_coverage_km": 10,
              "photo": None, "photo_attributions": []}
    with patch("app.routes.experiences.search_nearby", return_value=[result]) as search:
        client.application.config["GOOGLE_MAPS_API_KEY"] = "test-server-key"
        response = client.post("/experiences", data={
            "csrf_token": "", "search": "1", "origin": "current", "latitude": "23.83",
            "longitude": "91.28", "category": "Restaurant", "keyword": "",
        })
    assert response.status_code == 200
    assert b"1.2 km straight-line" in response.data
    assert "Current location" in response.get_data(as_text=True)
    assert search.call_args.args[1].latitude == 23.83
    assert search.call_args.args[1].longitude == 91.28
    assert search.call_args.args[3] is None


def test_search_requires_server_places_configuration(client):
    response = client.get("/experiences?search=1&destination=neermahal&category=Restaurant")
    assert response.status_code == 200
    assert b"backend has no GOOGLE_MAPS_API_KEY" in response.data
    assert b"Khangsar Traditional Tripuri Restaurant" not in response.data


def test_local_experiences_api_reports_missing_provider_configuration(client):
    response = client.get("/api/local-experiences?destination=neermahal&category=Restaurant")
    assert response.status_code == 503
    assert "backend has no GOOGLE_MAPS_API_KEY" in response.get_json()["error"]


def test_local_experiences_api_exposes_provider_diagnostic_without_api_secret(client, app):
    from app.services.local_experience_search import PlacesSearchError
    app.config["GOOGLE_MAPS_API_KEY"] = "never-return-this-secret"
    with patch("app.routes.experiences.search_nearby", side_effect=PlacesSearchError(
        "Google Places denied request (403): API key rejected", "PERMISSION_DENIED"
    )):
        response = client.get("/api/local-experiences?destination=neermahal&category=Restaurant")
    assert response.status_code == 502
    assert response.get_json()["provider_status"] == "PERMISSION_DENIED"
    assert "never-return-this-secret" not in response.get_data(as_text=True)


def test_local_experiences_api_rejects_unknown_destinations(client):
    response = client.get("/api/local-experiences?destination=missing&category=Restaurant")
    assert response.status_code == 400


def test_search_radius_filters_and_sorts_google_places_records(app):
    from app.models import Place
    center = Place.query.filter_by(slug="neermahal").first()
    payload = {"places": [
        {"id": "far", "displayName": {"text": "Too far"}, "location": {"latitude": 23.70, "longitude": 91.31}},
        {"id": "near", "displayName": {"text": "Nearby cafe"}, "location": {"latitude": center.latitude, "longitude": center.longitude}, "formattedAddress": "Melaghar"},
    ]}
    mocked_response = MagicMock()
    mocked_response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
    with patch("app.services.local_experience_search.urlopen", return_value=mocked_response) as request:
        results = search_nearby("server-key", center, "Restaurant", 5)
    assert [item["id"] for item in results] == ["near"]
    assert results[0]["distance_km"] == 0
    sent = json.loads(request.call_args.args[0].data)
    assert sent["locationRestriction"]["circle"]["center"] == {
        "latitude": center.latitude, "longitude": center.longitude,
    }
    assert sent["locationRestriction"]["circle"]["radius"] == 5000


def test_default_search_expands_provider_coverage_and_ranks_nearest(app):
    from app.models import Place
    center = Place.query.filter_by(slug="neermahal").first()

    def provider_response(request):
        body = json.loads(request.data)
        radius = body["locationRestriction"]["circle"]["radius"]
        count = 2 if radius == 10000 else 8
        places = [{"id": f"near-{index}", "displayName": {"text": f"Listing {index}"},
                   "location": {"latitude": center.latitude + index * 0.01, "longitude": center.longitude}}
                  for index in range(count)]
        return {"places": places}

    with patch("app.services.local_experience_search._provider_request", side_effect=provider_response) as provider:
        results = search_nearby("server-key", center, "Restaurant")
    assert len(results) == 8
    assert results[0]["distance_km"] <= results[-1]["distance_km"]
    assert all(record["search_coverage_km"] == 25 for record in results)
    assert [json.loads(call.args[0].data)["locationRestriction"]["circle"]["radius"]
            for call in provider.call_args_list] == [10000, 25000]


def test_keyword_restaurant_search_uses_text_search_and_does_not_assert_dietary_attributes(app):
    from app.models import Place
    center = Place.query.filter_by(slug="neermahal").first()
    mocked_response = MagicMock()
    mocked_response.__enter__.return_value.read.return_value = b'{"places": []}'
    with patch("app.services.local_experience_search.urlopen", return_value=mocked_response) as request:
        results = search_nearby("server-key", center, "Restaurant", 10, "pure vegetarian")
    assert results == []
    sent_request = request.call_args.args[0]
    assert sent_request.full_url.endswith("places:searchText")
    assert "pure vegetarian" in json.loads(sent_request.data)["textQuery"]
    assert "dietary" not in str(results).lower()


def test_homestay_search_uses_nearby_lodging_types(app):
    from app.models import Place
    center = Place.query.filter_by(slug="jampui-hills").first()
    payload = {"places": [{"id": "ChIJ-homestay-a", "displayName": {"text": "Nearby guest house"},
                           "location": {"latitude": center.latitude, "longitude": center.longitude},
                           "primaryType": "guest_house", "rating": 4.2}]}
    mocked_response = MagicMock()
    mocked_response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
    with patch("app.services.local_experience_search.urlopen", return_value=mocked_response) as request:
        results = search_nearby("server-key", center, "Homestay", 10)
    sent_request = request.call_args.args[0]
    assert sent_request.full_url.endswith("places:searchNearby")
    assert "guest_house" in json.loads(sent_request.data)["includedTypes"]
    assert results[0]["category"] == "Homestay"
    assert results[0]["id"] == "ChIJ-homestay-a"


def test_requested_destination_category_combinations_show_config_state_without_fabricated_results(client):
    destinations = [
        "neermahal", "jampui-hills", "unakoti", "ujjayanta-palace", "dumboor-lake",
        "trishna-wildlife-sanctuary", "boxanagar", "kamalasagar", "rudrasagar-lake",
        "sepahijala-wildlife-sanctuary", "heritage-park", "tripura-sundari-temple",
        "pilak", "bhuvaneswari-temple", "chabimura-debtamura", "gumti-wildlife-sanctuary",
    ]
    categories = ["All types", "Homestay", "Local Guide", "Restaurant", "Transport", "Handicrafts", "Cultural Experience"]
    for slug in destinations:
        for category in categories:
            response = client.get(f"/experiences?search=1&destination={slug}&category={category}")
            assert response.status_code == 200
            assert b"backend has no GOOGLE_MAPS_API_KEY" in response.data
            assert b"Ujjayanta Heritage Homestay" not in response.data


def test_provider_permission_error_is_actionable_and_does_not_expose_key():
    from app.services.local_experience_search import PlacesSearchError, _provider_request
    request = MagicMock()
    request.headers = {"X-Goog-Api-Key": "secret-test-key"}
    error = HTTPError("https://places.googleapis.com", 403, "Forbidden", {},
                      BytesIO(json.dumps({"error": {"status": "PERMISSION_DENIED", "message": "key secret-test-key denied"}}).encode()))
    with patch("app.services.local_experience_search.urlopen", side_effect=error):
        try:
            _provider_request(request)
            assert False, "expected PlacesSearchError"
        except PlacesSearchError as exc:
            assert exc.provider_status == "PERMISSION_DENIED"
            assert "billing" in exc.public_message
            assert "secret-test-key" not in exc.public_message


def test_configured_search_returns_real_provider_shaped_records(client, app):
    app.config["GOOGLE_MAPS_API_KEY"] = "test-server-key"
    record = {"id": "ChIJ-business-a", "name": "Provider cafe", "category": "Restaurant",
              "distance_km": 1.2, "directions": "https://www.google.com/maps/dir/?api=1&destination_place_id=ChIJ-business-a",
              "photo": None, "photo_attributions": []}
    with patch("app.routes.experiences.search_nearby", return_value=[record]):
        data = client.get("/api/local-experiences?destination=neermahal&category=Restaurant").get_json()
    assert data["destination"]["id"] == "neermahal"
    assert data["results"][0]["id"] == "ChIJ-business-a"
    assert data["results"][0]["directions"].endswith("destination_place_id=ChIJ-business-a")


def test_business_details_are_loaded_on_demand_for_selected_place(client, app):
    app.config["GOOGLE_MAPS_API_KEY"] = "test-server-key"
    payload = {"id": "ChIJ-business-a", "displayName": {"text": "Provider cafe"},
               "location": {"latitude": 23.51, "longitude": 91.32},
               "formattedAddress": "Melaghar, Tripura", "websiteUri": "https://example.test"}
    with patch("app.services.local_experience_search.fetch_place_details", return_value=payload) as fetch:
        response = client.get("/api/local-experiences/ChIJ-business-a?destination=neermahal")
    assert response.status_code == 200
    assert response.get_json()["name"] == "Provider cafe"
    assert response.get_json()["distance_km"] > 0
    fetch.assert_called_once_with("test-server-key", "ChIJ-business-a")
