# 05 · Technical and API Documentation

---

## 1. Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env      # then set SECRET_KEY
$env:FLASK_APP = "run.py"
python -m flask init-db
python -m flask seed-data
python run.py                    # http://127.0.0.1:5000
```

Installed and tested with: Python 3.14.8, Flask 3.1.0, Flask-SQLAlchemy 3.1.1, Flask-Migrate 4.1.0,
Flask-Login 0.6.3, Flask-WTF 1.2.2, WTForms 3.2.1, SQLAlchemy 2.0.44, pytest 8.4.2.

## 2. Environment variables

| Variable | Required | Default | Notes |
| --- | --- | --- | --- |
| `SECRET_KEY` | Production: yes | `dev-only-secret-key-change-me` | Signs sessions and CSRF tokens |
| `DATABASE_URL` | No | `sqlite:///instance/tripura_explore.db` | Use `postgresql+psycopg://…` for PostgreSQL |
| `FLASK_CONFIG` | No | `development` | `development` / `testing` / `production` |
| `COOKIE_SECURE` | Production: yes | `false` | `true` behind HTTPS |
| `SESSION_LIFETIME_MINUTES` | No | `120` | |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | No | – | Only read by `flask seed-data --with-admin` |
| `MAP_TILE_URL` | No | OSM standard tiles | Replace for production traffic |
| `MAP_TILE_ATTRIBUTION` | No | OSM attribution | |
| `MAP_MAX_ZOOM` | No | `18` | |
| `PLACES_PER_PAGE` | No | `9` | Explore pagination |
| `LOG_LEVEL` | No | `INFO` | |

## 3. Route inventory

### 3.1 Pages

| Method | Route | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `/` | – | Homepage |
| GET | `/explore` | – | Filtered destination grid |
| GET | `/places/<slug>` | – | Destination details (404 if unknown or unpublished) |
| GET | `/map` | – | Leaflet map page |
| GET, POST | `/trip-planner` | – | Planner; POST renders the plan server-side |
| POST | `/trip-planner/save` | signed in | Save a server-rendered plan |
| GET | `/my-trips` | signed in | List of saved trips |
| GET | `/itineraries/<int:id>` | owner | Trip editor |
| POST | `/itineraries/<int:id>/settings` | owner | Rename / change days, budget, date |
| POST | `/itineraries/<int:id>/share` | owner | Toggle the read-only link |
| POST | `/itineraries/<int:id>/delete` | owner | Delete the trip |
| POST | `/trip/add-place` | signed in | "Add to trip" from a destination page |
| GET | `/shared/<token>` | – | Read-only shared itinerary |
| GET | `/experiences` | – | Approved provider directory |
| GET | `/experiences/<slug>` | – | Provider detail (404 unless approved) |
| POST | `/experiences/<slug>/inquire` | – | Inquiry form fallback |
| GET, POST | `/auth/register` | – | Registration |
| GET, POST | `/auth/login` | – | Sign in |
| POST | `/auth/logout` | signed in | Sign out |
| GET | `/profile` | signed in | Account, trips, favourites |
| POST | `/places/<slug>/favorite` | signed in | Toggle favourite (form fallback) |
| POST | `/places/<slug>/report` | – | Report incorrect information |
| GET | `/about` | – | Data policy and limitations |
| GET | `/admin` and `/admin/*` | admin | Dashboard, destinations, categories, providers, inquiries, corrections, users |

### 3.2 JSON API

| Method | Route | Auth | Notes |
| --- | --- | --- | --- |
| GET | `/api/featured-places` | – | 6 most popular published destinations |
| GET | `/api/places` | – | Same filters/sorting/pagination as `/explore` |
| GET | `/api/places/<slug>` | – | Single destination, 404 when unpublished |
| GET | `/api/places/map` | – | Markers for published destinations with coordinates |
| POST | `/api/itineraries` | – / session for `save` | Generate a plan, optionally persist |
| GET | `/api/itineraries/<id>` | owner or share token | `?token=<share_token>` for shared access |
| PATCH | `/api/itineraries/<id>` | owner | Rename, change budget, or re-plan |
| DELETE | `/api/itineraries/<id>` | owner | Delete |
| PATCH | `/api/itineraries/<id>/stops` | owner | Re-order one day |
| POST | `/api/itineraries/<id>/stops` | owner | Add a stop |
| PATCH | `/api/itineraries/<id>/stops/<stop_id>` | owner | Move/edit a stop |
| DELETE | `/api/itineraries/<id>/stops/<stop_id>` | owner | Remove a stop |
| POST | `/api/favorites` | signed in | Add a favourite |
| DELETE | `/api/favorites/<place_id>` | signed in | Remove a favourite |
| POST | `/api/inquiries` | – | Store a provider inquiry |

All mutating endpoints require the CSRF token in the `X-CSRFToken` header (or a `csrf_token` form field).

## 4. Request and response examples

### GET /api/places?category=lakes&sort=popular&page=1
```json
{
  "total": 1,
  "pages": 1,
  "page": 1,
  "filters": {"category": "lakes", "sort": "popular"},
  "errors": [],
  "places": [
    {
      "id": 6, "name": "Dumboor Lake", "slug": "dumboor-lake",
      "tagline": "A lake shaped like a small drum",
      "short_description": "A large reservoir in Dhalai district with scattered islands and birdlife.",
      "category": "Lakes", "category_slug": "lakes", "district": "Dhalai",
      "locality": "Gandacherra",
      "image_url": "/static/images/places/dumboor-lake.svg",
      "latitude": 23.845, "longitude": 91.825,
      "coordinates_verified": false, "is_verified": false,
      "url": "/places/dumboor-lake"
    }
  ]
}
```

### GET /api/places/map?category=heritage
```json
{
  "count": 6,
  "published_without_coordinates": 1,
  "coordinates_verified": 0,
  "filters": {"category": "heritage", "district": "", "verified": false},
  "source_note": "Coordinates are stored per destination record. …",
  "places": [
    {"id": 1, "name": "Neermahal", "slug": "neermahal", "category": "Heritage",
     "district": "Sepahijala", "lat": 23.4929, "lng": 91.3145,
     "coordinates_verified": false, "image_url": "/static/images/places/neermahal.svg",
     "url": "/places/neermahal"}
  ]
}
```

### POST /api/itineraries (preview)
Request:
```json
{"duration_days": 2, "starting_location": "Agartala",
 "interests": ["Lakes", "Heritage"], "budget": 8000, "travel_date": "2026-12-01"}
```
Response `200`:
```json
{
  "preferences": {"duration_days": 2, "starting_location": "Agartala",
                  "interests": ["Lakes", "Heritage"], "budget": 8000,
                  "travel_date": "2026-12-01"},
  "plan": {
    "days": [
      {"day": 1, "stops": [
        {"place": {"name": "Neermahal", "slug": "neermahal", "url": "/places/neermahal", "...": "..."},
         "day_number": 1, "stop_order": 1, "leg_km": null, "area": "Sepahijala"}
      ]},
      {"day": 2, "stops": []}
    ],
    "notes": ["Stops in the same day are grouped using straight-line distance …"],
    "warnings": ["Travel time, opening hours and entry fees are not verified yet …",
                 "Budget planning is limited: the prototype has no verified price data …"],
    "matched_count": 8, "uses_coordinates": true, "max_stops_per_day": 3
  }
}
```
Add `"save": true` to store it (requires a session): response `201` adds
`"saved": {"id": 3, "title": "2-day Lakes, Heritage trip from Agartala", "url": "/itineraries/3", …}`.

### POST /api/itineraries (validation failure)
```json
{"error": "validation_failed",
 "errors": ["Trip duration must be between 1 and 3 days.",
            "Choose at least one interest."]}
```
Status `400`.

### PATCH /api/itineraries/3/stops (re-order day 1)
```json
{"day_number": 1, "order": [12, 9, 14]}
```
Response `200`: `{"itinerary": { …regenerated day-by-day structure… }}`.
Errors: `400` when the day is not part of the trip, or when the id list does not contain every stop of
that day exactly once.

### POST /api/inquiries
```json
{"business_id": 1, "name": "Prospective Guest", "email": "guest@example.com",
 "phone": "+91 00000 00000", "message": "Do you have a room for two nights in December?"}
```
Response `201`:
```json
{"status": "received", "inquiry_id": 1,
 "message": "Thank you. Your inquiry has been recorded and an administrator will review it. This prototype does not confirm bookings."}
```

## 5. Error handling

| Status | Meaning | Body |
| --- | --- | --- |
| 400 | Validation failed / bad request | `{"error": "validation_failed", "errors": ["…"]}` |
| 401 | Sign-in required | `{"error": "login_required", "message": "…", "login_url": "…"}` |
| 403 | Not the owner, or not an administrator | `{"error": "forbidden"}` or the 403 HTML page |
| 404 | Unknown slug/id, or an unpublished record | `{"error": "not_found"}` or the 404 HTML page |
| 409 | Duplicate stop / duplicate favourite | `{"error": "duplicate", "message": "…"}` |
| 500 | Unexpected server error | Logged; HTML error page (the session is rolled back) |

HTML routes redirect after a successful POST (Post/Redirect/Get) and show a flash message. JSON routes
return the payload above with no HTML.

## 6. Deployment configuration

See [`DEPLOYMENT.md`](DEPLOYMENT.md). Summary: set `FLASK_CONFIG=production`, a strong `SECRET_KEY`,
`COOKIE_SECURE=true`, a real `DATABASE_URL`, run `flask db upgrade` in the release step, serve with a
production WSGI server, and replace the OpenStreetMap public tile server before real traffic.