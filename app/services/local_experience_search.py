"""Google Places search for businesses around a verified Tripura destination."""
from __future__ import annotations

import json
import math
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
PLACES_NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"
PLACE_DETAILS_URL = "https://places.googleapis.com/v1/places/{}"
FIELD_MASK = ",".join((
    "places.id", "places.displayName", "places.formattedAddress", "places.location",
    "places.primaryType", "places.types", "places.rating", "places.userRatingCount",
    "places.businessStatus", "places.regularOpeningHours", "places.nationalPhoneNumber",
    "places.currentOpeningHours.openNow",
    "places.websiteUri", "places.googleMapsUri", "places.photos",
    "places.photos.authorAttributions",
))
CATEGORY_QUERIES = {
    "Homestay": "homestays guest houses lodges accommodation",
    "Local Guide": "local tour guides tourism guide services",
    "Restaurant": "restaurants cafes eateries",
    "Transport": "taxi services car rentals local transport tour operators",
    "Handicrafts": "handicraft shops bamboo cane crafts handloom artisan shops",
    "Cultural Experience": "cultural tours workshops traditional craft community tourism experiences",
}
CATEGORY_LABELS = {"All types": "All types", **{key: key for key in CATEGORY_QUERIES}}
CATEGORY_TYPES = {
    "Homestay": ["bed_and_breakfast", "guest_house", "hotel", "lodging", "hostel", "inn", "cottage", "farmstay"],
    "Restaurant": ["restaurant", "cafe", "bakery", "meal_takeaway", "meal_delivery"],
    "Transport": ["taxi_service", "taxi_stand", "car_rental", "chauffeur_service", "transportation_service"],
}


class PlacesSearchError(Exception):
    """Provider error with a safe, actionable message and provider status."""

    def __init__(self, message: str, provider_status: str | None = None):
        super().__init__(message)
        self.public_message = message
        self.provider_status = provider_status


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def _provider_request(request: Request) -> dict:
    try:
        with urlopen(request, timeout=8) as response:
            return json.loads(response.read())
    except HTTPError as exc:
        try:
            detail = json.loads(exc.read()).get("error", {})
        except (ValueError, AttributeError):
            detail = {}
        status = detail.get("status", f"HTTP_{exc.code}")
        api_key = next((value for name, value in request.headers.items() if name.lower() == "x-goog-api-key"), "")
        provider_message = str(detail.get("message", ""))
        if api_key:
            provider_message = provider_message.replace(api_key, "[redacted]")
        if exc.code == 403:
            message = ("Google Places denied the server key (403). Verify Places API (New) is enabled, billing is active, "
                       "and the key's API and server IP restrictions allow this request.")
            if provider_message:
                message += f" Provider detail: {provider_message[:400]}"
        elif exc.code == 429:
            message = "Google Places quota or rate limit reached (429). Check project quotas and billing."
        else:
            message = f"Google Places error {status}: {provider_message or 'request rejected'}"
        raise PlacesSearchError(message, status) from exc
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise PlacesSearchError("Google Places could not be reached. Check backend network access and try again.") from exc


def _place_record(place: dict, destination, category: str, radius_km: int) -> dict | None:
    location = place.get("location") or {}
    lat, lng = location.get("latitude"), location.get("longitude")
    if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
        return None
    distance = haversine_km(destination.latitude, destination.longitude, lat, lng)
    if distance > radius_km or not place.get("id"):
        return None
    photo = (place.get("photos") or [{}])[0]
    return {
        "id": place["id"], "name": (place.get("displayName") or {}).get("text", "").strip(),
        "category": category, "address": place.get("formattedAddress"),
        "latitude": lat, "longitude": lng, "distance_km": round(distance, 1),
        "rating": place.get("rating"), "review_count": place.get("userRatingCount"),
        "business_status": place.get("businessStatus"),
        "opening_hours": place.get("regularOpeningHours", {}).get("weekdayDescriptions"),
        "open_now": (place.get("currentOpeningHours") or {}).get("openNow"),
        "phone": place.get("nationalPhoneNumber"), "website": place.get("websiteUri"),
        "directions": "https://www.google.com/maps/dir/?" + urlencode({
            "api": "1", "destination": f"{float(lat):.7f},{float(lng):.7f}",
            "destination_place_id": place["id"], "travelmode": "driving",
        }),
        "maps_url": place.get("googleMapsUri"),
        "photo": photo.get("name"), "photo_attributions": photo.get("authorAttributions", []),
        "types": place.get("types", []), "price_level": place.get("priceLevel"),
    }


def search_nearby(api_key: str, destination, category: str, radius_km: int, keyword: str = "") -> list[dict]:
    """Search Google Places within the selected circle; validate and sort by Haversine distance."""
    query = CATEGORY_QUERIES.get(category)
    if category == "All types":
        queries = list(CATEGORY_QUERIES.items())
    elif query:
        queries = [(category, query)]
    else:
        raise ValueError("Unknown experience category")

    keyword = " ".join(str(keyword or "").split())[:100]
    results: dict[str, dict] = {}
    for result_category, terms in queries:
        center = {"latitude": destination.latitude, "longitude": destination.longitude}
        circle = {"circle": {"center": center, "radius": radius_km * 1000}}
        use_nearby = not keyword and (result_category in CATEGORY_TYPES or result_category == "All types")
        if use_nearby:
            types = CATEGORY_TYPES.get(result_category) or sorted({t for values in CATEGORY_TYPES.values() for t in values})
            body = {"includedTypes": types, "maxResultCount": 20, "rankPreference": "DISTANCE", "locationRestriction": circle}
            endpoint = PLACES_NEARBY_URL
        else:
            search_terms = f"{terms} {keyword}".strip()
            district = destination.district.name if destination.district else "Tripura"
            body = {"textQuery": f"{search_terms} near {destination.name}, {district}, Tripura",
                    "pageSize": 20, "rankPreference": "DISTANCE", "locationRestriction": circle}
            endpoint = PLACES_SEARCH_URL
        provider_request = Request(endpoint, data=json.dumps(body).encode(), method="POST", headers={
            "Content-Type": "application/json", "X-Goog-Api-Key": api_key, "X-Goog-FieldMask": FIELD_MASK,
        })
        payload = _provider_request(provider_request)
        for place in payload.get("places", []):
            record = _place_record(place, destination, result_category, radius_km)
            if record and record["name"]:
                results.setdefault(record["id"], record)
    return sorted(results.values(), key=lambda item: item["distance_km"])


def fetch_place_details(api_key: str, place_id: str) -> dict:
    """Fetch contact, hours, price and photo data only after the user opens a card."""
    if not place_id or len(place_id) > 200 or not all(ch.isalnum() or ch in "_-" for ch in place_id):
        raise ValueError("Invalid Places ID")
    fields = ("id,displayName,formattedAddress,location,primaryType,primaryTypeDisplayName,types,rating,"
              "userRatingCount,businessStatus,currentOpeningHours.openNow,regularOpeningHours,nationalPhoneNumber,websiteUri,googleMapsUri,"
              "priceLevel,photos,photos.authorAttributions")
    request = Request(PLACE_DETAILS_URL.format(quote(place_id, safe="")), headers={
        "X-Goog-Api-Key": api_key, "X-Goog-FieldMask": fields,
    })
    return _provider_request(request)


def photo_resource_path(photo_name: str) -> str | None:
    """Accept only a Places photo resource name, never an arbitrary upstream URL."""
    if photo_name.startswith("places/") and "/photos/" in photo_name and all(
        part.replace("-", "").replace("_", "").isalnum() for part in photo_name.split("/")
    ):
        return f"https://places.googleapis.com/v1/{quote(photo_name, safe='/')}/media?maxWidthPx=900&skipHttpRedirect=true"
    return None
