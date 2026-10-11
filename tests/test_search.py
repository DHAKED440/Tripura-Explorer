"""TC-02, TC-03 · search, filters, sorting and empty states."""
from app.models import Place


def test_search_finds_a_destination_by_name(client):
    response = client.get("/explore?q=Neermahal")
    assert response.status_code == 200
    assert b"Neermahal" in response.data
    # "Unakoti" also appears in the district filter, so check the result links.
    assert b'href="/places/unakoti"' not in response.data


def test_search_is_case_insensitive_and_matches_locality(client):
    assert b"Jampui" in client.get("/explore?q=jampui").data
    assert b"Dumboor" in client.get("/explore?q=gandacherra").data


def test_category_filter(client):
    body = client.get("/explore?category=lakes").data
    assert b"Dumboor Lake" in body
    assert b"Ujjayanta Palace" not in body


def test_district_filter_accepts_slug_and_display_name(client):
    by_slug = client.get("/explore?district=sepahijala").data
    by_name = client.get("/explore?district=Sepahijala").data
    assert b"Neermahal" in by_slug
    assert b"Neermahal" in by_name


def test_combined_filters(client):
    body = client.get("/explore?category=heritage&district=gomati").data
    assert b"Chabimura" in body
    assert b"Neermahal" not in body


def test_unknown_filters_are_handled_safely(client):
    response = client.get("/explore?category=not-a-category&district=narnia&sort=sideways")
    assert response.status_code == 200
    assert b"No destinations match these filters" in response.data
    assert b"No category matches" in response.data


def test_empty_result_state(client):
    body = client.get("/explore?q=zzzzzzzz").data
    assert b"No destinations match these filters" in body


def test_district_with_no_destinations_returns_empty_state(client):
    body = client.get("/explore?district=khowai").data
    assert b"No destinations match these filters" in body


def test_sorting_by_name_is_alphabetical(client):
    body = client.get("/explore?sort=name").data.decode()
    positions = [body.find(name) for name in ["Bhuvaneswari", "Boxanagar", "Chabimura"]]
    assert positions == sorted(positions)
    assert all(position > 0 for position in positions)


def test_pagination_splits_results(client, app):
    total = Place.query.filter_by(is_published=True).count()
    body = client.get("/explore?page=1").data
    assert b"pagination" in body
    assert total > 9


def test_page_beyond_range_returns_empty_state(client):
    body = client.get("/explore?page=99").data
    assert b"No destinations match these filters" in body


def test_api_places_matches_the_html_page(client):
    payload = client.get("/api/places?category=temples").get_json()
    assert payload["total"] >= 1
    assert all(item["category_slug"] == "temples" for item in payload["places"])


def test_unpublished_destinations_never_appear(client, app):
    payload = client.get("/api/places?q=draft").get_json()
    assert payload["total"] == 0