# Tripura Explore

Tripura Explore is a tourism discovery and trip-planning web application for Tripura, India. Visitors can browse destinations, explore them on a map, plan and save trips, and discover local experiences. The **Smart Route Lab** adds interactive demonstrations of graph algorithms used to study routes across destinations.

This repository contains a Flask web application and a separate React/Vite frontend prototype. The Flask application is the main application and serves the pages, APIs, and Smart Route Lab. The React frontend can be run separately during frontend development.

## How the application works

1. A visitor opens a page served by Flask. Most pages are rendered with Jinja templates; browser JavaScript adds interactive behavior.
2. The page requests destination and route data from Flask endpoints. Flask routes validate requests and call services for searching, itinerary planning, graph algorithms, and external map data.
3. SQLAlchemy reads or writes the configured database. The default local database is SQLite in `instance/tripura_explore.db`.
4. Flask returns rendered HTML or JSON. The browser updates the page, including maps and route visualizations.

The separate React app in `frontend/` uses Vite and calls the Flask API through a development proxy. It is not the frontend used by the Flask-rendered pages.

## Main features

- Search and filter Tripura destinations by keyword, category, and district.
- View destination details and locations on an interactive Leaflet map.
- Generate and manage multi-day itineraries; signed-in users can save and edit their trips.
- Find local experiences and nearby mapped places using OpenStreetMap services.
- Register, sign in, manage favourites, and use an administrator dashboard.
- Explore **Smart Route Lab**, which demonstrates shortest paths, A*, Bellman–Ford, minimum spanning trees, breadth-first and depth-first search, multi-stop routing, and route comparisons.

Destination details and map coverage are prototype data. External OpenStreetMap geocoding and nearby-search services can be rate-limited or unavailable, and mapped coverage varies.

## Technologies used

| Area | Technologies | Purpose |
| --- | --- | --- |
| Main web application | Python 3, Flask, Jinja2 | Page routes, server-rendered HTML, and JSON APIs |
| Data and accounts | SQLAlchemy, Flask-SQLAlchemy, Flask-Migrate, SQLite, Flask-Login | Database models, migrations, and login sessions |
| Forms and security | Flask-WTF, WTForms, email-validator | Form validation and CSRF protection |
| Main browser interface | HTML, CSS, vanilla JavaScript | Page layout and interactive features |
| Maps | Leaflet, OpenStreetMap | Destination and route maps |
| Optional frontend prototype | React 18, Vite, Tailwind CSS, Lucide React | Separate frontend development app in `frontend/` |
| Route algorithms | Python services in `app/services/` | Graph search, route optimization, and itinerary planning |
| Automated checks | pytest, Flask test client | Application and API tests |

## Project layout

```text
.
├── app/
│   ├── routes/       # Flask page and API endpoints
│   ├── services/     # Search, itinerary, map, and route algorithm logic
│   ├── models/       # SQLAlchemy database models
│   ├── templates/    # Jinja HTML pages and reusable page fragments
│   └── static/       # CSS, browser JavaScript, and images
├── frontend/         # Separate React and Vite frontend prototype
├── docs/             # Project, API, database, testing, and algorithm notes
├── tests/            # pytest test suite
├── run.py            # Flask development entry point
├── requirements.txt  # Python dependencies
└── README.md
```

## Run the Flask application locally

You need Python 3.10 or newer. From the repository root:

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux, activate it with `source .venv/bin/activate`.

### 2. Install Python packages

```powershell
python -m pip install -r requirements.txt
```

### 3. Configure local settings

```powershell
Copy-Item .env.example .env
```

For local development, the application has a development-only secret fallback. Before deploying, set a unique `SECRET_KEY` in `.env`; generate one with:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Create and populate the database

```powershell
$env:FLASK_APP = "run.py"
python -m flask init-db
python -m flask seed-data
```

`init-db` creates the tables. `seed-data` adds the sample destinations, categories, districts, and demo providers. The default database file is created under the ignored `instance/` directory.

### 5. Start the web server

```powershell
python run.py
```

Open <http://127.0.0.1:5000> in a browser. Flask runs in development mode when started this way.

### Optional: create an administrator account

```powershell
python -m flask create-admin
```

Follow the prompts to set the email, display name, and password. Passwords are hashed before being stored.

## Run the optional React frontend

The React app is a separate development project. It expects the Flask server to be running on port 5000 because Vite forwards API requests to it.

```powershell
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite (by default <http://localhost:3000>). To create a production frontend bundle, run `npm run build` from `frontend/`; the output goes to `frontend/dist/`.

## Useful commands

Run these from the repository root unless otherwise specified:

| Command | What it does |
| --- | --- |
| `python run.py` | Start the Flask development server |
| `python -m flask init-db` | Create database tables |
| `python -m flask seed-data` | Add or refresh sample data |
| `python -m flask create-admin` | Create or update an administrator |
| `python -m flask reset-db` | Drop all tables and recreate an empty database; asks for confirmation |
| `python -m pytest` | Run the automated test suite |
| `npm run dev` (in `frontend/`) | Start the Vite development server |
| `npm run build` (in `frontend/`) | Build the React frontend |

## Configuration and external services

The app reads settings from environment variables and an optional root `.env` file. `.env` is local configuration and must not be committed.

| Setting | Purpose |
| --- | --- |
| `SECRET_KEY` | Signs session cookies and CSRF tokens; use a strong value outside local development |
| `DATABASE_URL` | Optional SQLAlchemy database URL; defaults to the local SQLite database |
| `FLASK_CONFIG` | Selects `development`, `testing`, or `production` configuration |
| `COOKIE_SECURE` | Enables secure cookies when the site is served over HTTPS |
| `MAP_TILE_URL` | Map tile URL; defaults to OpenStreetMap tiles |
| `OSM_USER_AGENT`, `APPLICATION_URL` | Identify the app when it requests public OpenStreetMap data |
| `GEOCODER_URL`, `OVERPASS_URL`, `OVERPASS_FALLBACK_URLS` | Configure geocoding and nearby map-data services |
| `OSM_GEOCODER_TIMEOUT`, `OSM_OVERPASS_TIMEOUT` | Set request timeouts for those services |

Local experience search uses the public Nominatim geocoder and Overpass API. These services do not require API keys for this prototype, but their availability and usage policies apply. For sustained production use, configure a service appropriate for your expected traffic.

## Tests

```powershell
python -m pytest
```

The test suite uses pytest and Flask's test client. Its testing configuration uses an in-memory SQLite database so tests do not use the local development database.

## Further documentation

- [`docs/01-project-proposal.md`](docs/01-project-proposal.md) — goals and project scope
- [`docs/03-system-requirements.md`](docs/03-system-requirements.md) — requirements and system overview
- [`docs/04-database-design.md`](docs/04-database-design.md) — database structure
- [`docs/05-api-documentation.md`](docs/05-api-documentation.md) and [`docs/api-reference.md`](docs/api-reference.md) — API information
- [`docs/06-testing-report.md`](docs/06-testing-report.md) — testing notes
- [`docs/smart-route-lab-overview.md`](docs/smart-route-lab-overview.md) — Smart Route Lab design
- [`docs/algorithm-design.md`](docs/algorithm-design.md), [`docs/graph-theory.md`](docs/graph-theory.md), and [`docs/route-optimization.md`](docs/route-optimization.md) — route algorithms and concepts