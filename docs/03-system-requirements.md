# 03 · System Requirements Specification

---

## 1. Architecture

```
Browser (HTML + CSS + vanilla JS, Leaflet)
        │  HTTP, CSRF-protected forms and JSON fetch
        ▼
Flask application factory  (app/__init__.py)
        │
        ├── Blueprints (routes/)            main · places · map · itineraries · experiences · auth · admin
        ├── Services (services/)            destination_service · search_service · itinerary_service
        ├── Models (models/)                Category · District · Place · Itinerary · ItineraryStop · User
        │                                   Favorite · Business · Inquiry · CorrectionReport
        ├── Templates (templates/)          Jinja2, one template per page + partials/macros
        └── Extensions (extensions.py)      SQLAlchemy · Migrate · LoginManager · CSRFProtect
        │
        ▼
SQLite (development)  →  PostgreSQL-compatible via DATABASE_URL
```

Design rules enforced by the structure:

* Routes never build queries inline: they call a service.
* The itinerary algorithm has no HTTP or database knowledge, so it can be unit-tested directly.
* Templates never hold destination facts; they render model attributes.
* Public read endpoints filter `is_published` in one place (`destination_service.base_query`).

## 2. User roles

| Role | Can do |
| --- | --- |
| Anonymous visitor | Browse, search, filter, see the map, generate a plan (unsaved), read approved providers, send an inquiry, report an incorrect fact |
| Registered traveller | Everything above, plus save trips, edit/reorder/delete their own trips, share a read-only link, keep favourites |
| Administrator | Everything above, plus create/edit/publish/unpublish/delete destinations, manage categories, approve/reject providers, review inquiries and correction reports, change user roles |

## 3. Functional requirements

| ID | Requirement | Where it is implemented |
| --- | --- | --- |
| FR-1 | Show featured destinations from the database on the homepage | `routes/main.py:home`, `index.html` |
| FR-2 | Search destinations by name/keyword | `services/search_service.py:build_query` |
| FR-3 | Filter by category and district, preserve filters in the URL | `routes/places.py:explore` |
| FR-4 | Sort and paginate results | `sort_query`, `pagination` |
| FR-5 | Serve details for a published slug, 404 otherwise | `routes/places.py:detail` |
| FR-6 | Never expose unpublished records publicly | `base_query`, `get_place_by_slug` |
| FR-7 | Return map markers only for records with valid coordinates | `routes/map.py:api_map_places` |
| FR-8 | Validate latitude/longitude ranges | DB `CheckConstraint` + `PlaceForm` |
| FR-9 | Generate a 1–3 day itinerary from interests | `services/itinerary_service.py:generate_plan` |
| FR-10 | Persist itineraries with owner association | `routes/itineraries.py:api_create_itinerary` |
| FR-11 | Add, remove, move and re-order stops | `/api/itineraries/<id>/stops…` |
| FR-12 | Enforce itinerary ownership on read/write/delete | `_owned_itinerary` |
| FR-13 | Share a read-only itinerary link | `share_token`, `/shared/<token>` |
| FR-14 | Register/login/logout with hashed passwords | `routes/auth.py`, `User.set_password` |
| FR-15 | Store and remove favourites without duplicates | `Favorite` unique constraint |
| FR-16 | List approved providers only, with filters | `routes/experiences.py:index` |
| FR-17 | Store inquiries for admin review, hide them publicly | `Inquiry`, `admin/inquiries` |
| FR-18 | Let admins maintain destinations and publish/unpublish | `routes/admin.py` |
| FR-19 | Approve/reject provider listings | `routes/admin.py:approve_provider` |
| FR-20 | Review user-submitted correction reports | `CorrectionReport`, `admin/corrections` |
| FR-21 | Record what is verified and by whom | `is_verified`, `verified_by`, `last_verified_at`, `verification_notes` |
| FR-22 | Report an issue from a destination page | `routes/places.py:report_problem` |
| FR-23 | Fallback flows without JavaScript | `POST /trip-planner`, `POST /places/<slug>/report`, `POST /experiences/<slug>/inquire`, `POST /places/<slug>/favorite` |

## 4. Non-functional requirements

| ID | Requirement | How it is met |
| --- | --- | --- |
| NFR-1 | Responsive on phones, tablets and desktops | Mobile-first CSS with three breakpoints; verified at 1080/820/520 px rules |
| NFR-2 | Accessible | Skip link, landmarks, labels, focus rings, ARIA tabs/live regions, alt text, contrast |
| NFR-3 | Secure by default | CSRF on every state change; hashed passwords; server-side authorization; ownership checks; no secrets in templates |
| NFR-4 | Portable data layer | SQLAlchemy models + configurable `DATABASE_URL`; migrations via Flask-Migrate |
| NFR-5 | Maintainable by a beginner | Small modules, service layer, comments where logic is non-obvious, one template per page |
| NFR-6 | Honest data | Unverified values stay NULL and render as "Not verified"; approximate coordinates are labelled |
| NFR-7 | Performance on modest hosting | Pagination, `limit()` on list queries, indexed columns (slug, district, category, status), no N+1-heavy pages |
| NFR-8 | Testability | 111 pytest tests; testing config with in-memory SQLite and CSRF disabled |
| NFR-9 | Recoverable operations | `reset-db` requires confirmation; seed data is idempotent |
| NFR-10 | Traceable content | Every destination stores a `source_note`, `coordinate_source` and verification fields |

## 5. Use cases

**UC-1 Find a destination and decide to visit it**
Actor: anonymous visitor. Precondition: at least one published destination.
Main flow: open `/` → enter "Neermahal" → Explore shows the matching card → open details → read overview →
check Travel information (sees "Not verified" for fees) → click Get directions.
Postcondition: the visitor reaches an external navigation service with the correct coordinates.
Failure: the search returns nothing → empty state offers to clear filters or open the map.

**UC-2 Build and save a trip**
Actor: registered traveller. Main flow: `/trip-planner` → 2 days, Agartala, interests Lakes + Heritage →
Generate → review day columns → Save → the trip opens in the editor → drag a stop into a new order →
share the read-only link.
Failure: no destination matches → an explanatory message, nothing is saved.
Failure: not signed in → the API returns `401` with a login link.

**UC-3 Find a local provider and send an inquiry**
Actor: anonymous visitor. Main flow: `/experiences` → filter by Homestay → open a provider → submit name,
email and message → the inquiry is stored with status `new` → confirmation shown.
Failure: invalid email or short message → validation errors, nothing stored.

**UC-4 Maintain destination data**
Actor: administrator. Main flow: sign in → `/admin/places` → edit a destination → fill verified fee and
hours, tick "coordinates verified", record the verifier and date → save → publish.
Failure: half-filled coordinates or a missing verifier name → the form shows an error and refuses to save.

**UC-5 Review a reported error**
Actor: administrator. Main flow: `/admin/corrections` → open a report → set status to "reviewing" → fix the
destination → mark "resolved" with a note.

## 6. Security and privacy requirements

| Area | Rule | Implementation |
| --- | --- | --- |
| Passwords | Never store plain text; use a salted hash | `werkzeug.security.generate_password_hash` (scrypt/PBKDF2) |
| Sessions | Signed cookies, HttpOnly, SameSite=Lax, Secure in production | `config.py`, Flask session |
| CSRF | Every POST/PATCH/DELETE requires a token | `CSRFProtect`, `X-CSRFToken` header from the meta tag |
| Authorization | Server-side on every protected route | `@login_required`, `admin_required`, `_owned_itinerary` |
| Object ownership | A user can only read/modify their own itineraries | `user_id` check on all four verbs |
| Private data | Inquiries and correction reporter emails are never rendered publicly | Admin-only templates |
| Admin access | Hiding a link is not access control | Every `/admin/*` route wrapped in `admin_required` |
| Input validation | Validate on the server, not just the browser | WTForms + service-layer validation |
| Redirects | `?next=` cannot leave the site | `auth._safe_next` rejects absolute/foreign URLs |
| Secrets | No credentials in code, templates or JavaScript | `.env` + `.env.example` placeholders only |
| Privacy | Collect only what is needed for an inquiry; state the purpose on the form | Inquiry form fields + explanatory text |
| Destructive actions | Confirmed and POST-only | `reset-db --yes`, confirm dialogs, POST delete routes |

## 7. Constraints

* Python 3.10+ (developed and tested on 3.14).
* JavaScript is optional for the core journey; the map and the drag-to-reorder editor need it.
* Internet access is required for map tiles (the CDN libraries and tiles), not for the rest of the site.
* SQLite has no deferred constraints, which is why stop ordering is normalised in the service layer rather
  than enforced by a composite unique index.