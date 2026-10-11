# 06 · Testing Report

**Build tested:** Tripura Explore prototype, commit state at the end of the build session
**Environment:** Windows 11 · Python 3.14.8 · Flask 3.1.0 · pytest 8.4.2 · SQLite in-memory (tests) / SQLite file (manual)
**Tester:** the developer (self-testing). Independent user testing has **not** happened yet — see section 4.

---

## 1. Automated test suite

```powershell
python -m pytest
```

**Executed result: `111 passed in 35.22s`** (0 failed, 0 skipped at the time of writing; two tests in the
suite contain `pytest.skip` guards that only trigger if the generated plan is too small to exercise the
scenario, and neither triggered).

| Test file | Tests | What it covers |
| --- | --- | --- |
| `tests/test_homepage.py` | 7 | Homepage renders, navigation links, featured places from the DB, `GET /api/featured-places`, about page, empty state when nothing is published, signed-in navigation |
| `tests/test_places.py` | 10 | Valid slug, unknown slug → 404, unpublished slug → 404, missing optional data renders, public pages never expose drafts, place API, latitude `CHECK` constraint, correction report stored/rejected |
| `tests/test_search.py` | 12 | Search by name/locality (case-insensitive), category filter, district filter by slug and display name, combined filters, unknown filters, empty state, district with no destinations, name sorting, pagination, page beyond range, API parity |
| `tests/test_map.py` | 8 | Map page renders, only published + valid coordinates, drafts excluded, places without coordinates excluded and counted, category filter, unknown category, verified-only filter, marker payload shape |
| `tests/test_itineraries.py` | 26 | Preference validation (duration, interests, budget, date), ranking, plan structure (day range, ≤ 3 stops/day, no duplicates), warnings, empty plan, planner page, no-JS rendering, API preview/save/login, saved trips page, stop add/duplicate/unknown/remove/move/reorder validation, settings update, delete, ownership across users, share link read-only |
| `tests/test_auth.py` | 14 | Registration, hashing (plain text never stored), duplicate email, password mismatch, short password, login/logout, wrong password, unknown email, protected-page redirects, profile content, `next=` cannot leave the site, favourites add/remove/duplicate/login, admin sign-in, ordinary user forbidden |
| `tests/test_admin.py` | 13 | Anonymous redirect, ordinary user 403 on every admin route, cannot publish, destination list, publish/unpublish round trip, create destination, half-filled coordinates rejected, verification needs a name, edit destination, approve provider, add category, inquiry/correction queues, cannot change own role, `seed-data` is idempotent |
| `tests/test_experiences.py` | 9 | Only approved providers listed, pending detail 404, approved detail renders, filters, valid inquiry stored, invalid inquiry rejected, unknown provider, no-JS inquiry form, private inquiry data not public, no admin controls on public pages, demo content labelled |

**How to reproduce:** from the project root run `python -m pytest`. The tests use the `testing`
configuration (in-memory SQLite, CSRF disabled) and never touch `instance/tripura_explore.db`.

Fast, focused runs:

```powershell
python -m pytest tests/test_itineraries.py -v
python -m pytest -k "search or map" -v
```

## 2. Manual test cases (TC-01 … TC-12)

The table below is the project's manual checklist. "Actual result" describes what the executed build did.
Statuses were set after running the step; nothing is marked passed without a result.

| Test ID | Feature | Test action | Expected result | Actual result | Status | Bug ID | Date tested | Tester |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-01 | Homepage | Open the website | Homepage loads successfully | `GET /` → 200, hero, search, 6 featured cards, categories, stats | Pass | – | 2026-10-11 | Developer |
| TC-02 | Search | Search for Neermahal | Matching destination appears | `/explore?q=Neermahal` → 1 card, "Neermahal", other destinations absent from results | Pass | – | 2026-10-11 | Developer |
| TC-03 | Filters | Select Nature category | Only matching places appear | `/explore?category=nature` → only Nature records; `/explore?category=nonsense` shows a warning + empty state | Pass | – | 2026-10-11 | Developer |
| TC-04 | Destination details | Open a valid place | Correct details are displayed | `/places/neermahal` → 200, name, tabs, quick facts, directions link, mini map | Pass | – | 2026-10-11 | Developer |
| TC-05 | Invalid destination | Open a nonexistent slug | A proper 404 page appears | `/places/does-not-exist` → 404 page; the unpublished draft slug also returns 404 | Pass | – | 2026-10-11 | Developer |
| TC-06 | Map | Click a destination marker | Correct destination preview opens | `/api/places/map` → 15 markers with popups (name, image, details link); verified-only filter → 0 and explains why | Pass | – | 2026-10-11 | Developer |
| TC-07 | Trip planner | Submit valid preferences | An itinerary is generated | 2 days / Agartala / Lakes + Heritage → 2 day columns, 6 stops, notes + warnings, submitted via the API and the no-JS form | Pass | – | 2026-10-11 | Developer |
| TC-08 | Trip planner | Submit invalid duration | Validation error is displayed | Duration 9 and no interests → HTTP 400 with both messages listed | Pass | – | 2026-10-11 | Developer |
| TC-09 | Saved trips | Save and reopen an itinerary | Saved data is preserved | Save → 201 with the trip id → `/itineraries/3` shows the stored stops; reorder removed a stop correctly in tests | Pass | – | 2026-10-11 | Developer |
| TC-10 | Admin | Access admin page without authorization | Access is denied | Anonymous → 302 to sign-in; signed-in ordinary user → 403 on all admin routes | Pass | – | 2026-10-11 | Developer |
| TC-11 | Mobile | Open the website on a narrow screen | Layout remains usable | Responsive rules verified in the CSS at 1080/820/520 px; hamburger navigation, single-column grids, 60 vh map. **Not verified on a physical device yet** — see limitations | Partial | – | 2026-10-11 | Developer |
| TC-12 | Directions | Click Get Directions | Correct external directions open | The link is built from the stored coordinates (`google.com/maps/dir/?api=1&destination=lat,lng`); content of the external service not verified | Pass | – | 2026-10-11 | Developer |

A spreadsheet-ready copy of this table lives in [`test_cases.csv`](test_cases.csv).

## 3. Defects found and fixed during testing

| Bug ID | Severity | Description | Root cause | Resolution | Status |
| --- | --- | --- | --- | --- | --- |
| BUG-01 | High | `CorrectionReport` crashed on import (`NameError: utcnow`) | Helper function missing in `models/feedback.py` | Added the `utcnow()` helper | Fixed |
| BUG-02 | High | Jinja macros could not see `current_user` | `{% from %}` imports a macro without the template context | Imported the place-card macro `with context` | Fixed |
| BUG-03 | Medium | Re-ordering stops inside a day raised a database error | Unique index on (itinerary, day, order) is checked per statement, and SQLite cannot defer it | Replaced it with a unique (itinerary, place) index and renumbered in the service layer | Fixed |
| BUG-04 | Medium | Test clients appeared to "stay logged in" as another user | A long-lived app context in the fixture reused Flask-Login's cache on `g` | Purge `g._login_user` at the start of each request in the testing config | Fixed |
| BUG-05 | Low | Placeholder artwork was missing (404 images) | Images are generated, and the generator had never run | Added `tools/generate_place_images.py` and generated 42 SVGs | Fixed |

No open defects are known in the implemented scope. The known *gaps* (unverified data, no reviews, no
bookings) are product decisions documented in `KNOWN-LIMITATIONS.md`, not defects.

## 4. Not yet tested (honest list)

| Item | Why it is outstanding | Planned approach |
| --- | --- | --- |
| Real-device mobile testing | The build was verified through responsive CSS rules and the test client only | Open the site on Android/iOS at 360–430 px, check tap targets, map gestures, sticky header |
| Browser matrix | Verified manually on a Chromium-based desktop browser only | Check Firefox and Safari, including Leaflet interactions |
| Screen-reader testing | ARIA and focus behaviour were designed and reviewed, not audited | NVDA + Firefox pass over the core journey |
| Lighthouse / performance audit | Not run | Run against the homepage, Explore and details pages |
| User acceptance testing with tourists | No participants yet | 5–8 moderated sessions; record task success and confusion points |
| Provider feedback on the inquiry flow | No providers approached yet | 3–5 interviews, then decide whether bookings deserve investment |
| Load testing | Prototype scale only | Only if the tile service and hosting move beyond a demo |

## 5. Quality gates applied before this report

* All 111 automated tests pass.
* No `TODO` placeholders left in the implemented routes or templates.
* Every visible control performs a real action (no dead buttons or `href="#"` links).
* No secrets, API keys or passwords in the repository (`.env` is git-ignored; `.env.example` has
  placeholders only).
* Unpublished records are excluded from all public endpoints (covered by tests).
* Admin authorization is enforced server-side (covered by tests).