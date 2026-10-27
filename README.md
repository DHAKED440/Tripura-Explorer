# Tripura Explore

**Discover the hidden beauty of Tripura.**

A working full-stack tourism discovery and trip-planning prototype for Tripura, India. It is built with
Flask, SQLAlchemy, Jinja templates, hand-written CSS and a small amount of vanilla JavaScript, and it ships
with a real database, an interactive Leaflet map, a rule-based trip planner, saved trips, a local-experience
directory, an administrator dashboard, an automated test suite and the eight project reports.

> **Prototype status.** The application is functional and tested, but the *destination facts* are not fully
> verified yet. Entry fees, opening hours, closed days, best seasons and exact coordinates are intentionally
> left blank or labelled "approximate" until they are confirmed with the managing authorities. See
> [`docs/DATA-VERIFICATION.md`](docs/DATA-VERIFICATION.md) and [`docs/KNOWN-LIMITATIONS.md`](docs/KNOWN-LIMITATIONS.md).

---

## 1. What works

| Area | Status |
| --- | --- |
| Homepage with search, category shortcuts, featured destinations, planner and map entry points | Working |
| Explore page: keyword search, category filter, district filter, sorting, pagination, bookmarkable URL filters, empty/error states | Working |
| Destination details: gallery, tabs, quick facts, directions link, favourite, "add to trip", mini map, report-an-issue form | Working |
| Interactive map: Leaflet + OpenStreetMap tiles, markers from the database, category/district filters, marker popups, approximate-coordinate labels | Working |
| Trip planner: 1–3 days, interests, start point, optional budget/date, rule-based generation, day-wise result, notes and honest warnings | Working |
| Saved trips: save, reopen, remove a stop, move a stop between days, drag to reorder, rename, change duration, delete, read-only share link | Working |
| Authentication: register, sign in, sign out, profile, favourites, per-user ownership checks | Working |
| Local experiences: Nominatim destination search, Overpass nearby OSM discovery, map/list view and internal map directions | Working, public-service availability varies |
| Admin dashboard: destinations CRUD + publish/unpublish + verification fields, categories, provider approval, inquiries, correction reports, users | Working |
| Automated tests (pytest + Flask test client) | Passing |
| Eight project reports and a data-verification checklist | Written in `docs/` |

**Deliberately not implemented:** reviews and star ratings (they need moderation and real users), online
booking or payments, live provider availability, multi-language content, and route-optimised itineraries.
Each one is listed with a reason in the reports.

---

## 2. Technology

* **Frontend** – HTML5, CSS3 (custom design system, no framework), vanilla JavaScript, Jinja2 templates.
  Bootstrap 5 is deliberately not used: the project has its own small design system so the two-colour
  travel identity (`#17365D` navy + `#F7F5F0` ivory) is not fought by a utility framework.
* **Maps** – Leaflet 1.9.4 with OpenStreetMap tiles (loaded from a CDN, attribution shown in the footer and
  on the map page).
* **Backend** – Python 3, Flask 3, Flask-SQLAlchemy, Flask-Migrate (Alembic), Flask-Login, Flask-WTF.
* **Database** – SQLite for development. SQLAlchemy models and a configurable `DATABASE_URL` keep the layer
  portable to PostgreSQL.
* **Tests** – pytest with the Flask test client.
* **Tooling** – `python-dotenv`, `.env` configuration, custom `flask` CLI tasks.

---

## 3. Quick start

```powershell
# 1. From the project root, create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate           # macOS / Linux

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Create your local configuration
Copy-Item .env.example .env
#   then edit .env and set a long random SECRET_KEY:
#   python -c "import secrets; print(secrets.token_hex(32))"

# 4. Create the database and load the prototype dataset
$env:FLASK_APP = "run.py"
python -m flask init-db        # create the tables
python -m flask seed-data      # load categories, districts, destinations, demo providers

# 5. (optional) create an administrator
python -m flask create-admin   # interactive, hashes the password before storing it

# 6. Run the development server
python run.py                  # http://127.0.0.1:5000
```

On macOS/Linux use `export FLASK_APP=run.py` instead of `$env:FLASK_APP`.

### Local demo accounts

`flask create-admin` is the supported way to make an administrator. If you want the same throw-away local
account used while building this prototype:

```powershell
python -m flask create-admin --email "admin@tripura-explore.local" --name "Site Administrator" --password "admin-demo-password"
```

The credentials live only in your local `instance/tripura_explore.db` (git-ignored). **Change the password
before showing the site to anybody else, and never reuse it in production.**

---

## 4. Useful commands

| Command | What it does |
| --- | --- |
| `python run.py` | Start the development server on port 5000 |
| `python -m flask init-db` | Create every table from the models |
| `python -m flask seed-data` | Load/refresh the repeatable prototype data (safe to run twice) |
| `python -m flask seed-data --with-admin` | Also create/refresh the admin from `ADMIN_EMAIL` / `ADMIN_PASSWORD` in `.env` |
| `python -m flask create-admin` | Create or update an administrator interactively |
| `python -m flask reset-db --yes` | Drop and recreate an empty database (**destructive**) |
| `python -m flask db upgrade` | Apply Alembic migrations (after `flask db init`/`migrate`) |
| `python -m pytest` | Run the automated test suite |
| `python tools/generate_place_images.py` | Regenerate the placeholder SVG artwork |

---

## 5. Project structure

```
Tripura Explorer/
├── app/
│   ├── __init__.py            # application factory, blueprints, error pages, CLI wiring
│   ├── config.py              # Development / Testing / Production configuration
│   ├── extensions.py          # db, migrate, login_manager, csrf
│   ├── forms.py               # WTForms with CSRF + server-side validation
│   ├── cli.py                 # init-db, seed-data, create-admin, reset-db
│   ├── seed_data.py           # the repeatable prototype dataset (with source notes)
│   ├── data/                  # editorial cultural highlights (kept out of templates)
│   ├── models/                # Category, District, Place, Itinerary, User, Business, Feedback
│   ├── routes/                # main, places, map, itineraries, experiences, auth, admin
│   ├── services/              # destination, search and itinerary (rule-based) logic
│   ├── templates/             # base + one template per page + partials/macros + admin/
│   └── static/                # css/ (style, components, responsive), js/, images/
├── docs/                      # the eight reports, data policy, deployment and limitations
├── tests/                     # 111 pytest tests
├── tools/generate_place_images.py
├── instance/                  # local SQLite database (git-ignored)
├── .env.example
├── pytest.ini
├── requirements.txt
├── run.py
└── README.md
```

---

## 6. Routes

**Pages**

| Route | Description |
| --- | --- |
| `GET /` | Homepage |
| `GET /explore` | Destination discovery with filters, sorting and pagination |
| `GET /places/<slug>` | Destination details (404 for unknown *or unpublished*) |
| `GET /map` | Interactive map |
| `GET /trip-planner` | Trip planner (also accepts `POST` as a no-JavaScript fallback) |
| `GET /my-trips` | Saved trips (sign-in required) |
| `GET /itineraries/<id>` | One saved trip with editing controls (owner only) |
| `GET /shared/<token>` | Read-only shared itinerary |
| `GET /experiences`, `GET /experiences/<slug>` | Local provider directory and detail (approved only) |
| `GET /profile` | Account, trips and favourites (sign-in required) |
| `GET /about` | Prototype background, data policy and limitations |
| `GET /admin`, `/admin/places`, `/admin/categories`, `/admin/providers`, `/admin/inquiries`, `/admin/corrections`, `/admin/users` | Administrator dashboard (admin only) |

**JSON API**

| Method + route | Auth | Notes |
| --- | --- | --- |
| `GET /api/featured-places` | – | Homepage feed |
| `GET /api/places` | – | Same filters as `/explore` |
| `GET /api/places/<slug>` | – | Single destination (404 when unpublished) |
| `GET /api/places/map` | – | Published destinations with valid coordinates |
| `POST /api/itineraries` | – / session for `save: true` | Generate a plan, optionally save it |
| `GET /api/itineraries/<id>` | owner or share token | Private by default |
| `PATCH /api/itineraries/<id>` | owner | Rename / re-plan |
| `DELETE /api/itineraries/<id>` | owner | Delete a trip |
| `PATCH /api/itineraries/<id>/stops` | owner | Re-order one day |
| `POST` / `PATCH` / `DELETE /api/itineraries/<id>/stops[/<stop_id>]` | owner | Add, move, edit or remove a stop |
| `POST` / `DELETE /api/favorites[/<place_id>]` | signed in | Add / remove a favourite |
| `POST /api/inquiries` | – | Store a provider inquiry for admin review |

Full request/response examples: [`docs/05-api-documentation.md`](docs/05-api-documentation.md).

Every state-changing request is protected by Flask-WTF CSRF. The JavaScript reads the token from the
`<meta name="csrf-token">` tag and sends it as `X-CSRFToken`.

---

## 7. Tests

```powershell
python -m pytest            # or: python -m pytest -v
```

**Latest executed result: 111 passed in 35.22 s** (Python 3.14, pytest 8.4.2, Flask 3.1).

The suite covers the homepage, search and filters, destination details, 404 handling, the map endpoint,
the itinerary service and API, stop editing and ownership, authentication, favourites, the admin
authorization boundary, provider approval and inquiry handling. `tests/conftest.py` builds the app with
the `testing` configuration (in-memory SQLite, CSRF off) and seeds the same prototype data used by the
development server; it never touches your real database file.

---

## 8. Configuration

Copy `.env.example` to `.env` and fill in the values. Nothing secret is hard-coded in the application.

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | **Required in production.** Signs session cookies and CSRF tokens |
| `DATABASE_URL` | Optional override (defaults to `instance/tripura_explore.db`) |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Optional, used only by `flask seed-data --with-admin` |
| `COOKIE_SECURE` | Set to `true` behind HTTPS |
| `SESSION_LIFETIME_MINUTES` | Session length (default 120) |
| `MAP_TILE_URL`, `MAP_TILE_ATTRIBUTION`, `MAP_MAX_ZOOM` | Tile provider configuration |
| `OSM_USER_AGENT`, `APPLICATION_URL`, `GEOCODER_URL`, `OVERPASS_URL`, `OVERPASS_FALLBACK_URLS` | Identify the app and configure the primary and comma-separated compatible OSM data services |
| `OSM_GEOCODER_TIMEOUT`, `OSM_OVERPASS_TIMEOUT` | Bound destination and nearby-search provider waits (defaults: 8 and 18 seconds) |
| `PLACES_PER_PAGE`, `LOG_LEVEL`, `FLASK_CONFIG` | Development tuning |

Local Experiences uses Nominatim for submitted place names and Overpass for nearby
mapped features. Set a descriptive `OSM_USER_AGENT` with real maintainer contact
information and `APPLICATION_URL` to the deployed site. The public Nominatim
service does not permit client-side autocomplete, so the page offers the app's
published Tripura locations plus an explicit place/address search on submit.
Public OSM endpoints have no availability SLA, and OSM coverage in Tripura varies;
the page reports outages and missing facts instead of substituting demo results.
Nearby-search failures are logged by provider hostname, HTTP status, elapsed time,
category, and search area. A failing endpoint is briefly cooled down; 429 responses
are held for at least 30 seconds, and a single jittered retry is made only for 502/503
gateway responses. Configure a self-hosted or licensed compatible Overpass endpoint
in `OVERPASS_URL` and `OVERPASS_FALLBACK_URLS` for dependable production availability.
Restaurant results discovered by food searches are upserted by OSM element ID into the separate
`osm_restaurants` table. This grows from searches people make; it is not a complete Tripura-wide
restaurant inventory. Mapped cuisine, hours, contact details, service options, and image links appear
when present in OSM tags. Public Nominatim and Overpass endpoints do not require API keys.
Before production traffic grows, move to an appropriately provisioned or licensed
geocoding/search provider and a tile service suitable for the expected usage.

---

## 9. Deployment

Short version (full notes in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)):

1. Set `FLASK_CONFIG=production`, a strong `SECRET_KEY`, `COOKIE_SECURE=true` and a real `DATABASE_URL`.
2. Install dependencies and run the migrations (`flask db upgrade`) rather than `create_all`.
3. Serve the app with a production WSGI server, for example `waitress-serve --port=8000 run:app` on Windows
   or `gunicorn "app:create_app('production')"` on Linux.
4. Terminate HTTPS at the reverse proxy, keep `instance/` on a persistent volume, and **never** run
   `seed-data` against production.
5. Replace the OpenStreetMap public tile server with a licensed or self-hosted tile service before real
   traffic.

---

## 10. Documentation

| Document | Contents |
| --- | --- |
| [`docs/01-project-proposal.md`](docs/01-project-proposal.md) | Problem, objectives, MVP scope, success metrics, risks |
| [`docs/02-ui-ux-specification.md`](docs/02-ui-ux-specification.md) | Sitemap, personas, page workflows, design tokens, accessibility, states |
| [`docs/03-system-requirements.md`](docs/03-system-requirements.md) | Functional/non-functional requirements, architecture, use cases, security |
| [`docs/04-database-design.md`](docs/04-database-design.md) | ER diagram, tables, keys, constraints, sample records, provenance |
| [`docs/05-api-documentation.md`](docs/05-api-documentation.md) | Setup, routes, request/response examples, error handling |
| [`docs/06-testing-report.md`](docs/06-testing-report.md) | TC-01…TC-12 with executed results, plus the pytest evidence |
| [`docs/test_cases.csv`](docs/test_cases.csv) | The same test cases as a spreadsheet-ready file |
| [`docs/07-analytics-evaluation.md`](docs/07-analytics-evaluation.md) | What is measured, what is still empty, proposed metrics |
| [`docs/08-startup-validation.md`](docs/08-startup-validation.md) | Interviews (pending), competitors, revenue hypotheses, roadmap |
| [`docs/DATA-VERIFICATION.md`](docs/DATA-VERIFICATION.md) | Field-survey checklist and the exact facts still to confirm |
| [`docs/KNOWN-LIMITATIONS.md`](docs/KNOWN-LIMITATIONS.md) | Everything that is deliberately incomplete |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Production configuration, WSGI, tiles, backups |

---

## 11. Image and data licensing

Destination artwork in `app/static/images/` is generated SVG (see `tools/generate_place_images.py`) and is
part of this repository. It exists so that no unlicensed photograph is used. Replace it with licensed
photography, keeping the credit and licence fields described in the data-verification checklist.
Map tiles are © OpenStreetMap contributors and are used under their attribution rules.
