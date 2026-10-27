"""OpenStreetMap-backed destination geocoding and nearby place discovery.

OSM data coverage varies by area. This adapter exposes only facts supplied in
OSM tags and never turns absent ratings, prices, hours, or photos into claims.
"""
from __future__ import annotations

import json
import math
import random
import re
import threading
import time
from collections import OrderedDict
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from flask import current_app, has_app_context, has_request_context, request
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db

CATEGORY_LABELS = {
    "All Places": "All Places",
    "Accommodation": "Accommodation",
    "Food & Restaurants": "Food & Restaurants",
    "Tourist Attractions": "Tourist Attractions",
    "Local Guide": "Local Guide",
    "Useful Services": "Useful Services",
}

# These are provider query filters, not a local inventory of businesses.
# Local-guide results are only actual mapped guide offices or travel agencies.
TAG_FILTERS = {
    "Accommodation": {
        "tourism": ["hotel", "guest_house", "hostel", "motel", "apartment", "chalet", "camp_site", "caravan_site", "alpine_hut"],
        "office": ["tourist_accommodation"],
    },
    "Food & Restaurants": {
        "amenity": ["restaurant", "cafe", "fast_food", "food_court", "ice_cream", "bar", "pub"],
        "shop": ["bakery", "pastry", "confectionery", "deli", "tea", "coffee"],
    },
    "Tourist Attractions": {
        "tourism": ["attraction", "viewpoint", "museum", "zoo", "theme_park", "artwork", "picnic_site"],
        "historic": ["monument", "archaeological_site", "castle", "ruins", "memorial", "fort", "yes"],
        "leisure": ["park", "nature_reserve"],
        "natural": ["waterfall", "peak", "cave_entrance"],
    },
    "Local Guide": {
        "office": ["guide", "travel_agent"],
        "shop": ["travel_agency"],
    },
    "Useful Services": {
        "amenity": ["fuel", "pharmacy", "hospital", "clinic", "doctors", "atm", "toilets", "bank", "parking", "charging_station", "bus_station", "taxi", "car_rental", "police", "fire_station", "post_office", "drinking_water", "visitor_centre", "ferry_terminal"],
        "healthcare": ["hospital", "clinic", "doctor", "pharmacy"],
        "railway": ["station", "halt"],
        "public_transport": ["station"],
        "shop": ["car_repair"],
        "craft": ["car_repair"],
        "tourism": ["information"],
    },
}

_CACHE: OrderedDict[tuple, tuple[float, object]] = OrderedDict()
_CACHE_MISS = object()
_CACHE_LIMIT = 512
_CACHE_LOCK = threading.Lock()
_NOMINATIM_LOCK = threading.Lock()
_OVERPASS_LOCK = threading.Lock()
_OVERPASS_COOLDOWNS: dict[str, tuple[float, str]] = {}
_LAST_NOMINATIM_REQUEST = 0.0
_GEOCODE_TTL = 86400
_SEARCH_TTL = 300
_MAX_RESULTS = 200


def _place_search_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def _resolve_published_destination(query: str) -> dict | None:
    """Use the app's own published destination coordinates before geocoding."""
    if not has_app_context():
        return None
    from app.models import Place

    requested = _place_search_key(query)
    if not requested:
        return None
    try:
        places = Place.query.filter(Place.is_published.is_(True)).all()
    except SQLAlchemyError:
        current_app.logger.warning("Could not check published Tripura destinations before geocoding")
        db.session.rollback()
        return None
    for place in places:
        if not place.has_tripura_coordinates:
            continue
        district = place.district.name if place.district else ""
        area = place.locality or district
        labels = {
            place.name,
            f"{place.name}, Tripura, India",
            f"{place.name}, {area}, Tripura, India" if area else "",
            f"{place.name}, {district}, Tripura, India" if district else "",
        }
        if requested in {_place_search_key(label) for label in labels if label}:
            return {
                "name": place.name,
                "latitude": float(place.latitude),
                "longitude": float(place.longitude),
                "osm_type": None,
                "osm_id": None,
                "source": "Tripura Explorer published destination",
            }
    return None
_API_PAGE_SIZE = 24


class SearchResults(list):
    """A list compatible with existing callers that records provider truncation."""

    def __init__(self, values=(), *, truncated: bool = False, provider_degraded: bool = False):
        super().__init__(values)
        self.truncated = truncated
        self.provider_degraded = provider_degraded


class OSMServiceError(Exception):
    """A safe, classified provider error for the UI and API."""

    def __init__(self, public_message: str, provider_status: str | None = None, http_status_code: int | None = None):
        super().__init__(public_message)
        self.public_message = public_message
        self.provider_status = provider_status or "unavailable"
        self.http_status_code = http_status_code

    @property
    def retryable(self) -> bool:
        return self.provider_status in {"rate_limited", "timeout", "unavailable"}

    @property
    def http_status(self) -> int:
        return 429 if self.provider_status == "rate_limited" else 504 if self.provider_status == "timeout" else 502


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def _cached(key: tuple):
    with _CACHE_LOCK:
        item = _CACHE.get(key)
        if item and item[0] > time.monotonic():
            _CACHE.move_to_end(key)
            return item[1]
        if item:
            _CACHE.pop(key, None)
    return _CACHE_MISS


def _store(key: tuple, value, ttl: int):
    with _CACHE_LOCK:
        _CACHE[key] = (time.monotonic() + ttl, value)
        _CACHE.move_to_end(key)
        while len(_CACHE) > _CACHE_LIMIT:
            _CACHE.popitem(last=False)


def _provider_headers() -> dict[str, str]:
    headers = {"User-Agent": current_app.config["OSM_USER_AGENT"], "Accept": "application/json"}
    referer = current_app.config.get("APPLICATION_URL", "") or (request.url_root if has_request_context() else "")
    if referer:
        headers["Referer"] = referer
    return headers


def _safe_provider_error(exc: HTTPError, action: str) -> OSMServiceError:
    if exc.code == 429:
        return OSMServiceError(f"{action} is rate-limited by OpenStreetMap right now. Wait a moment, then retry.", "rate_limited", exc.code)
    if exc.code in {408, 504}:
        return OSMServiceError(f"{action} took too long. The public map service may be busy; please retry shortly.", "timeout", exc.code)
    if exc.code in {500, 502, 503}:
        return OSMServiceError("The OpenStreetMap search service is temporarily unavailable. Retry shortly.", "unavailable", exc.code)
    return OSMServiceError(f"{action} could not be completed by the OpenStreetMap service. Check the destination and retry.", "provider_error", exc.code)


def geocode_destination(query: str) -> dict | None:
    """Resolve a submitted Tripura place name through configured geocoding."""
    global _LAST_NOMINATIM_REQUEST
    normalized = " ".join(str(query or "").split())[:200]
    if not normalized:
        return None
    local_result = _resolve_published_destination(normalized)
    if local_result:
        return local_result
    cache_key = ("geocode", normalized.casefold())
    cached = _cached(cache_key)
    if cached is not _CACHE_MISS:
        return cached

    provider = current_app.config.get("GEOCODER_URL", "https://nominatim.openstreetmap.org/search")
    provider_query = normalized if "tripura" in normalized.casefold() else f"{normalized}, Tripura, India"
    params = {"q": provider_query, "format": "jsonv2", "limit": 5, "countrycodes": "in", "addressdetails": 1}
    req = Request(f"{provider}?{urlencode(params)}", headers=_provider_headers())
    with _NOMINATIM_LOCK:
        wait = 1.0 - (time.monotonic() - _LAST_NOMINATIM_REQUEST)
        if wait > 0:
            time.sleep(wait)
        _LAST_NOMINATIM_REQUEST = time.monotonic()
        try:
            with urlopen(req, timeout=current_app.config.get("OSM_GEOCODER_TIMEOUT", 8)) as response:
                payload = json.loads(response.read(1_000_000))
        except HTTPError as exc:
            error = _safe_provider_error(exc, "Destination search")
            current_app.logger.warning("Nominatim destination search failed: status=%s", error.provider_status)
            raise error from exc
        except TimeoutError as exc:
            error = OSMServiceError("Destination search timed out. Retry shortly or choose a listed Tripura destination.", "timeout")
            current_app.logger.warning("Nominatim destination search timed out")
            raise error from exc
        except URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                error = OSMServiceError("Destination search timed out. Retry shortly or choose a listed Tripura destination.", "timeout")
                current_app.logger.warning("Nominatim destination search timed out")
                raise error from exc
            error = OSMServiceError("Could not connect to the destination search service. Check your connection and retry.", "unavailable")
            current_app.logger.warning("Nominatim destination search connection failed: %s", type(exc).__name__)
            raise error from exc
        except OSError as exc:
            error = OSMServiceError("Could not connect to the destination search service. Check your connection and retry.", "unavailable")
            current_app.logger.warning("Nominatim destination search connection failed: %s", type(exc).__name__)
            raise error from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            error = OSMServiceError("The destination search service returned an unreadable response. Retry shortly.", "bad_response")
            current_app.logger.warning("Nominatim returned an invalid response")
            raise error from exc

    answer = None
    for item in payload if isinstance(payload, list) else []:
        try:
            lat, lon = float(item["lat"]), float(item["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        # The envelope rejects unrelated Indian results. It is intentionally
        # broad enough to include Tripura and nearby named features; no result
        # is described as an official state boundary check.
        if not (22.9 <= lat <= 24.6 and 91 <= lon <= 92.4):
            continue
        display_name = str(item.get("display_name") or normalized)
        address = item.get("address") if isinstance(item.get("address"), dict) else {}
        state = str(address.get("state") or address.get("state_district") or "")
        if state and "tripura" not in state.casefold():
            continue
        if not state and "tripura" not in display_name.casefold() and "tripura" not in provider_query.casefold():
            continue
        answer = {"name": display_name[:300], "latitude": lat,
                  "longitude": lon, "osm_type": item.get("osm_type"), "osm_id": item.get("osm_id")}
        break
    # Do not make a temporary empty provider response stick for a whole day.
    _store(cache_key, answer, _GEOCODE_TTL if answer else 60)
    return answer


def _overpass_query(lat: float, lon: float, radius_m: int, category: str) -> str:
    if category not in CATEGORY_LABELS:
        raise ValueError("Unknown experience category")
    groups = TAG_FILTERS if category == "All Places" else {category: TAG_FILTERS.get(category, {})}
    merged_filters: dict[str, set[str]] = {}
    for tags in groups.values():
        for key, values in tags.items():
            merged_filters.setdefault(key, set()).update(values)
    selectors = []
    for key, values in sorted(merged_filters.items()):
        values_re = "|".join(re.escape(value) for value in sorted(values))
        selectors.append(f'nwr(around:{radius_m},{lat:.7f},{lon:.7f})["{key}"~"^({values_re})$"]["name"];')
    selector_block = "".join(selectors)
    return f"[out:json][timeout:16];({selector_block});out center tags;"


def _matches(tags: dict, filters: dict[str, list[str]]) -> bool:
    return any(tags.get(key) in values for key, values in filters.items())


def _category(tags: dict) -> str:
    # More specific tags win when an element carries multiple OSM features.
    for group in ("Accommodation", "Food & Restaurants", "Local Guide", "Tourist Attractions", "Useful Services"):
        if _matches(tags, TAG_FILTERS[group]):
            return group
    return "Other mapped place"


def _address(tags: dict) -> str | None:
    full = tags.get("addr:full") or tags.get("address")
    if full:
        return str(full).strip() or None
    parts = [tags.get("addr:housenumber"), tags.get("addr:street"), tags.get("addr:neighbourhood"),
             tags.get("addr:suburb"), tags.get("addr:city") or tags.get("addr:town") or tags.get("addr:village"),
             tags.get("addr:state"), tags.get("addr:postcode")]
    value = ", ".join(dict.fromkeys(str(part).strip() for part in parts if part))
    return value or None


def _safe_website(value: str | None) -> str | None:
    if not value:
        return None
    raw = str(value).strip()
    parsed = urlsplit(raw)
    return raw if parsed.scheme.lower() in {"http", "https"} and parsed.netloc else None


def _safe_image(value: str | None) -> str | None:
    """Keep only absolute HTTP(S) image links contributed in OSM tags."""
    if not value:
        return None
    raw = str(value).strip()
    parsed = urlsplit(raw)
    return raw if parsed.scheme.lower() in {"http", "https"} and parsed.netloc else None


def _safe_phone(value: str | None) -> str | None:
    if not value:
        return None
    raw = str(value).strip()[:80]
    return raw if re.fullmatch(r"[+0-9()./; xX#,-]+", raw) else None


def _category_icon(category: str) -> str:
    if category == "Accommodation":
        return "accommodation"
    if category == "Food & Restaurants":
        return "food"
    if category == "Tourist Attractions":
        return "attraction"
    if category == "Local Guide":
        return "guide"
    return "service"


def _normalize_element(element: dict, origin_lat: float, origin_lon: float) -> dict | None:
    tags = element.get("tags") if isinstance(element.get("tags"), dict) else {}
    try:
        lat_value = element.get("lat")
        lon_value = element.get("lon")
        if lat_value is None or lon_value is None:
            center = element.get("center") or {}
            lat_value, lon_value = center.get("lat"), center.get("lon")
        lat, lon = float(lat_value), float(lon_value)
        osm_type, osm_id = str(element["type"]), int(element["id"])
    except (KeyError, TypeError, ValueError):
        return None
    if osm_type not in {"node", "way", "relation"} or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    name = str(tags.get("name") or tags.get("name:en") or "").strip()[:180]
    if not name:
        return None
    category = _category(tags)
    # Facts that OSM normally does not supply remain null. Hotel stars are not
    # interpreted as customer ratings, and no hours parser is used to guess now.
    coordinates = {"latitude": lat, "longitude": lon}
    return {
        "id": f"{osm_type}/{osm_id}", "osm_type": osm_type, "osm_id": osm_id,
        "name": name, "category": category, **coordinates,
        "distance_km": round(haversine_km(origin_lat, origin_lon, lat, lon), 1),
        "distance_type": "straight-line", "address": _address(tags),
        "description": tags.get("description") or tags.get("description:en"),
        "phone": _safe_phone(tags.get("contact:phone") or tags.get("phone")),
        "website": _safe_website(tags.get("contact:website") or tags.get("website")),
        "image_url": _safe_image(tags.get("image") or tags.get("contact:image")),
        "email": tags.get("contact:email") or tags.get("email"),
        "opening_hours": tags.get("opening_hours"), "opening_status": None,
        "operator": tags.get("operator"), "brand": tags.get("brand"),
        "cuisine": tags.get("cuisine"), "fee": tags.get("fee"),
        "wheelchair": tags.get("wheelchair"), "takeaway": tags.get("takeaway"),
        "delivery": tags.get("delivery"), "dine_in": tags.get("dine_in"),
        "photo": _safe_image(tags.get("image") or tags.get("contact:image")),
        "rating": None, "review_count": None, "price": None,
        "raw_tags": tags,
        "osm_url": f"https://www.openstreetmap.org/{osm_type}/{osm_id}",
        "directions": "/map?" + urlencode({"lat": f"{lat:.7f}", "lng": f"{lon:.7f}", "name": name,
                                              "osm_type": osm_type, "osm_id": osm_id, "directions": "1"}),
        "external_directions": f"https://www.google.com/maps/dir/?api=1&destination={lat:.7f}%2C{lon:.7f}",
        "icon_category": _category_icon(category),
    }


def _read_overpass(req: Request) -> dict:
    timeout = current_app.config.get("OSM_OVERPASS_TIMEOUT", 18)
    # Retry only a transient gateway response once. Do not repeat timeouts or
    # 429s against the same public instance.
    for attempt in range(2):
        try:
            with urlopen(req, timeout=timeout) as response:
                payload = json.loads(response.read(12_000_000))
            if not isinstance(payload, dict) or not isinstance(payload.get("elements"), list):
                raise OSMServiceError("The nearby search service returned an unreadable response. Retry shortly.", "bad_response")
            return payload
        except HTTPError as exc:
            if attempt == 0 and exc.code in {502, 503}:
                delay = 0.25 * (2 ** attempt) + random.uniform(0.0, 0.2)
                time.sleep(min(delay, 1.5))
                continue
            raise _safe_provider_error(exc, "Nearby places search") from exc
        except TimeoutError as exc:
            raise OSMServiceError("Nearby search timed out at OpenStreetMap. The public map service may be busy; please retry shortly.", "timeout") from exc
        except URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise OSMServiceError("Nearby search timed out at OpenStreetMap. The public map service may be busy; please retry shortly.", "timeout") from exc
            raise OSMServiceError("Could not connect to the nearby search service. Check your connection and retry.", "unavailable") from exc
        except OSError as exc:
            raise OSMServiceError("Could not connect to the nearby search service. Check your connection and retry.", "unavailable") from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise OSMServiceError("The nearby search service returned an unreadable response. Retry shortly.", "bad_response") from exc
    raise OSMServiceError("The nearby search service is temporarily unavailable. Retry shortly.", "unavailable")


def _cached_restaurant_results(latitude: float, longitude: float, radius_km: int, keyword: str) -> SearchResults:
    """Use previously discovered real OSM restaurants as an explicitly partial fallback."""
    if not has_app_context():
        return SearchResults()
    from app.models import OSMRestaurant

    try:
        rows = OSMRestaurant.query.all()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Could not read cached OSM restaurant fallback")
        return SearchResults()
    needle = keyword.casefold()
    records = []
    for row in rows:
        item = row.to_dict(latitude, longitude)
        if item["distance_km"] > radius_km:
            continue
        if needle and needle not in (item["name"] + " " + json.dumps(item["raw_tags"], ensure_ascii=False)).casefold():
            continue
        records.append(item)
    records.sort(key=lambda item: (item["distance_km"], item["name"].casefold()))
    return SearchResults(records[:_MAX_RESULTS], truncated=len(records) > _MAX_RESULTS, provider_degraded=True)


def search_nearby(latitude: float, longitude: float, radius_km: int, category: str = "All Places", keyword: str = "") -> list[dict]:
    """Search public OSM features near coordinates with distance and tag filters."""
    if category not in CATEGORY_LABELS:
        raise ValueError("Unknown experience category")
    if not (math.isfinite(latitude) and math.isfinite(longitude) and -90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Invalid geographic coordinates")
    if radius_km not in {5, 10, 25, 50}:
        raise ValueError("Invalid search radius")
    normalized_keyword = " ".join(str(keyword or "").split())[:100]
    key = ("overpass", round(latitude, 5), round(longitude, 5), radius_km, category, normalized_keyword.casefold())
    cached = _cached(key)
    if cached is not _CACHE_MISS:
        if isinstance(cached, OSMServiceError):
            raise cached
        return cached

    endpoint = current_app.config.get("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
    fallback_endpoints = current_app.config.get(
        "OVERPASS_FALLBACK_URLS", ("https://overpass.private.coffee/api/interpreter",)
    )
    if isinstance(fallback_endpoints, str):
        fallback_endpoints = fallback_endpoints.split(",")
    endpoints = list(dict.fromkeys(
        str(url).strip() for url in (endpoint, *fallback_endpoints) if str(url).strip()
    ))
    query = _overpass_query(latitude, longitude, radius_km * 1000, category)
    body = urlencode({"data": query}).encode()
    headers = _provider_headers()
    headers.update({"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
    try:
        # Keep public provider load bounded: one search at a time, one retry
        # only for 502/503, then at most one compatible fallback endpoint.
        with _OVERPASS_LOCK:
            last_error = None
            available = [provider for provider in endpoints
                         if _OVERPASS_COOLDOWNS.get(provider, (0.0, ""))[0] <= time.monotonic()]
            if not available:
                last_error = OSMServiceError(
                    "The nearby place providers are temporarily unavailable. Please retry in a few seconds.",
                    "unavailable",
                )
                _store(key, last_error, 4)
                raise last_error
            for index, provider in enumerate(available[:2]):
                started = time.perf_counter()
                req = Request(provider, data=body, method="POST", headers=headers)
                try:
                    payload = _read_overpass(req)
                    _OVERPASS_COOLDOWNS.pop(provider, None)
                    current_app.logger.info(
                        "Overpass search completed provider=%s elapsed_ms=%d elements=%d category=%s radius_km=%d",
                        urlsplit(provider).hostname, round((time.perf_counter() - started) * 1000),
                        len(payload["elements"]), category, radius_km,
                    )
                    break
                except OSMServiceError as exc:
                    last_error = exc
                    elapsed_ms = round((time.perf_counter() - started) * 1000)
                    cooldown = 30 if exc.provider_status == "rate_limited" else 8
                    if exc.provider_status == "rate_limited":
                        try:
                            retry_after = int(exc.__cause__.headers.get("Retry-After", "30"))
                            cooldown = max(30, min(retry_after, 300))
                        except (AttributeError, TypeError, ValueError):
                            cooldown = 30
                    if exc.provider_status in {"timeout", "unavailable", "rate_limited"}:
                        _OVERPASS_COOLDOWNS[provider] = (time.monotonic() + cooldown, exc.provider_status)
                    current_app.logger.warning(
                        "Overpass search failed provider=%s http_status=%s status=%s elapsed_ms=%d category=%s radius_km=%d",
                        urlsplit(provider).hostname, exc.http_status_code or "no-response",
                        exc.provider_status, elapsed_ms, category, radius_km,
                    )
                    if index == len(available[:2]) - 1 or exc.provider_status not in {
                        "timeout", "unavailable", "rate_limited"
                    }:
                        raise
                    current_app.logger.info(
                        "Overpass failover provider=%s after status=%s",
                        urlsplit(available[index + 1]).hostname, exc.provider_status,
                    )
            else:
                raise last_error or OSMServiceError(
                    "The nearby search service is temporarily unavailable. Retry shortly.", "unavailable"
                )
    except OSMServiceError as exc:
        if category in {"All Places", "Food & Restaurants"}:
            partial = _cached_restaurant_results(latitude, longitude, radius_km, normalized_keyword)
            if partial:
                current_app.logger.warning(
                    "Serving cached OSM results after provider failure status=%s count=%d category=%s radius_km=%d",
                    exc.provider_status, len(partial), category, radius_km,
                )
                _store(key, partial, _SEARCH_TTL)
                return partial
        _store(key, exc, 4)
        raise

    records, seen = [], set()
    for element in payload["elements"]:
        item = _normalize_element(element, latitude, longitude)
        if item is None or item["distance_km"] > radius_km:
            continue
        identity = (item["osm_type"], item["osm_id"])
        if identity in seen:
            continue
        seen.add(identity)
        if category != "All Places" and item["category"] != category:
            continue
        if normalized_keyword and normalized_keyword.casefold() not in (
            item["name"] + " " + json.dumps(item["raw_tags"], ensure_ascii=False)
        ).casefold():
            continue
        records.append(item)

    records.sort(key=lambda item: (item["distance_km"], item["name"].casefold()))
    truncated = len(records) > _MAX_RESULTS
    records = SearchResults(records[:_MAX_RESULTS], truncated=truncated)
    _store(key, records, _SEARCH_TTL)
    return records


def find_cached_place(osm_type: str, osm_id: str):
    """Find a detail record only if it was returned from a recent nearby query."""
    with _CACHE_LOCK:
        for key, (expires, records) in reversed(_CACHE.items()):
            if key[0] == "overpass" and expires > time.monotonic():
                for item in records:
                    if item["osm_type"] == osm_type and str(item["osm_id"]) == str(osm_id):
                        return item
    return None


def persist_discovered_restaurants(records: list[dict]) -> int:
    """Upsert restaurant data returned by a user-requested OSM search.

    This is an accumulating provider inventory, not a claim that every Tripura
    restaurant is mapped. Database errors are logged without hiding live search
    results from the visitor.
    """
    if not has_app_context():
        return 0
    restaurants = [
        item for item in records
        if item.get("category") == "Food & Restaurants"
        and item.get("osm_type") in {"node", "way", "relation"}
        and item.get("osm_id") is not None
        and item.get("name") and item.get("latitude") is not None and item.get("longitude") is not None
    ]
    if not restaurants:
        return 0
    from app.models import OSMRestaurant

    saved = 0
    try:
        for item in restaurants:
            row = OSMRestaurant.query.filter_by(
                osm_type=item["osm_type"], osm_id=str(item["osm_id"])
            ).one_or_none()
            if row is None:
                row = OSMRestaurant(osm_type=item["osm_type"], osm_id=str(item["osm_id"]))
                db.session.add(row)
            for field in (
                "name", "latitude", "longitude", "address", "description", "cuisine",
                "opening_hours", "phone", "email", "website", "operator", "brand",
                "takeaway", "delivery", "dine_in", "wheelchair",
            ):
                setattr(row, field, item.get(field))
            row.image_url = item.get("image_url")
            row.raw_tags = item.get("raw_tags") or {}
            row.source_url = item.get("osm_url") or f"https://www.openstreetmap.org/{row.osm_type}/{row.osm_id}"
            row.source_attribution = "© OpenStreetMap contributors"
            row.last_synced_at = datetime.now(timezone.utc)
            saved += 1
        db.session.commit()
    except (SQLAlchemyError, KeyError, TypeError, ValueError):
        db.session.rollback()
        current_app.logger.exception("Could not persist OSM restaurant search results")
        return 0
    return saved


def find_persisted_restaurant(osm_type: str, osm_id: str):
    """Load a restaurant listing saved from a prior nearby OSM search."""
    if not has_app_context():
        return None
    from app.models import OSMRestaurant

    row = OSMRestaurant.query.filter_by(osm_type=osm_type, osm_id=str(osm_id)).one_or_none()
    return row.to_dict() if row else None
