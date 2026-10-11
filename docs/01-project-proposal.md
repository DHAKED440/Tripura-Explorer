# 01 · Project Proposal / Product Requirements

**Project:** Tripura Explore — tourism discovery and trip-planning website
**Tagline:** Discover the hidden beauty of Tripura.
**Document type:** MVP proposal and product requirements
**Status:** Implemented as a working prototype. Interviews, market research and field verification are **pending**
(see `08-startup-validation.md`).

---

## 1. Problem statement

A tourist planning a Tripura trip has to piece information together from search results, blog posts,
scattered government pages, map apps and word of mouth. The problems that follow are consistent:

* Destination facts (name, district, fees, timings, season) are spread across sources that contradict each other.
* It is hard to see **where** attractions are relative to each other, so multi-day plans are guesswork.
* Lesser-known places and small local providers (homestays, guides, craftspeople) have little visibility.
* Nothing connects discovery to action: a traveller reads about a place but gets no help turning it into a plan.

## 2. Objectives

1. One trustworthy record per destination, used by every screen.
2. Let a visitor find a destination in under a minute (search, category, district, map).
3. Turn interests into a practical 1–3 day plan the traveller can edit and keep.
4. Give local providers a reviewable place to be discovered — without pretending to be a booking engine.
5. Give an administrator a real way to maintain the data instead of editing database files.
6. Be honest about what is verified and what is not.

## 3. Target users

| Persona | Needs | How the product serves them |
| --- | --- | --- |
| First-time tourist (Bengali/English speaker) | Know what to see, how far apart things are, what a day looks like | Explore page, map, day-wise planner |
| Family or budget traveller | Practical, low-risk stops; predictable costs | District/category filtering, quick facts, explicit "not verified" labels |
| Student / weekend traveller (from Agartala) | Short trips, cheap options, less travel | 1–2 day plans grouped by area |
| Nature, lake, hill, heritage, temple and wildlife enthusiast | Filter by interest, not by marketing category | Interest tags and category filters shared across Explore, map and planner |
| Local guide / homestay / restaurant / craftsperson | Somewhere to be found and contacted | Local Experiences directory and inquiry inbox |
| Tourism administrator | Correct data without SQL | Admin dashboard with verification fields and publish/unpublish |

## 4. Proposed solution

A responsive website with seven connected surfaces: **Homepage → Explore → Destination details → Map →
Trip planner → Saved trips → Local experiences**, plus an **admin dashboard** behind authentication.

The single source of truth is the `places` table. Homepage cards, Explore results, map markers, planner
candidates and the details page all read the same row, so a fact can never drift between pages.

## 5. MVP scope (implemented)

* 16 seeded destination records (15 published + 1 draft used to test publishing), 7 categories, 8 districts.
* Search (name, locality, description, tags), category filter, district filter, sorting, pagination.
* Destination details with tabs: Overview, Travel information, Nearby, Data & sources, Report an issue.
* Leaflet map with database-driven markers, filters, popups and approximate-coordinate labels.
* Rule-based trip planner (1–3 days, up to 3 stops per day) with explicit data-quality warnings.
* Database-backed saved trips with stop add/remove/move/reorder and read-only sharing.
* Accounts with hashed passwords, favourites, and ownership checks on every itinerary operation.
* Local Experiences directory with admin approval and stored inquiries (no bookings).
* Admin dashboard: destinations, categories, providers, inquiries, corrections, users.
* 111 automated tests and eight project reports.

## 6. Deferred features (and why)

| Deferred | Reason |
| --- | --- |
| Reviews and star ratings | Need moderation, abuse handling and real users. Showing invented ratings would break the honesty rule. |
| Online booking / payments | Requires provider agreements, availability data and payment compliance. The prototype ships an inquiry inbox instead. |
| Real-time availability | No provider systems to read from. |
| Route optimisation and travel times | Needs a routing service and a real algorithm; the prototype shows a suggested order plus external directions links. |
| Bengali / Kokborok interface | Needs reviewed translations and names; collected but not yet implemented. |
| User-uploaded photos | Needs storage, moderation, licensing and privacy work. |

## 7. Success metrics

**Product metrics (to be measured once people use the prototype):**

| Metric | Definition | Target for the first trial |
| --- | --- | --- |
| Search success rate | Sessions where a search leads to a destination detail view | ≥ 60 % |
| Discovery-to-plan rate | Sessions that open the trip planner after viewing a destination | ≥ 15 % |
| Plan completion rate | Generated plans that are saved | ≥ 25 % |
| Map engagement | Sessions that use a map filter or open a marker popup | ≥ 20 % |
| Empty-result rate | Searches/filters returning nothing | ≤ 10 % |

**Data-quality metrics (measurable today):**

| Metric | Current value | How to check |
| --- | --- | --- |
| Published destinations | 15 | `/admin` overview, or `GET /api/places` |
| Records with verified information | 0 | `is_verified` is false for every seeded record |
| Records with field-verified coordinates | 0 | `GET /api/places/map?verified=1` returns 0 markers |
| Districts without any destination | 1 (Khowai) | District filter returns an empty state |
| Destination facts still to confirm | fee, hours, closed day, season, coordinates, images (per record) | `docs/DATA-VERIFICATION.md` |

The analytics report (`07`) explains how usage events would be collected with privacy safeguards; **no usage
data is claimed yet** because the prototype has not been tested with real visitors.

## 8. Risks and assumptions

| Risk / assumption | Impact | Mitigation in this build |
| --- | --- | --- |
| Unverified fees and hours would mislead travellers | High | Fields are blank; the UI prints "Not verified" and explains why |
| Approximate coordinates shown as exact | High | `coordinates_verified` flag; markers and pages say "approximate"; the map has a "verified only" filter |
| Unlicensed images | Legal | Generated SVG placeholders only; image credit/licence fields exist in the data policy |
| Community content published without review | Ethical | Cultural entries carry "Pending community review" |
| Fabricated reviews or popularity | Trust | No ratings anywhere; `popularity` is an internal editorial score |
| OpenStreetMap public tiles under real traffic | Operational | Documented; the tile URL is configurable |
| Single maintainer / small team | Delivery | One data entry point, repeatable seed data, documented checklist |
| Demo provider listings mistaken for real businesses | Trust | Every demo record and the directory itself say "Demo listing" |

## 9. Assumptions

* Visitors have a browser with JavaScript for the map (-style features) but the core journey works without it.
* SQLite is sufficient for the prototype; PostgreSQL is a configuration change away.
* Fact collection (fees, hours, GPS, photographs) is a separate, funded workstream.