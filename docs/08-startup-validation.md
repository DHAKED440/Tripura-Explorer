# 08 · Startup Validation and Business Report

**Honest status: the validation work has not been done.** No tourist has been interviewed, no local provider
has been approached, no competitor benchmark has been measured, and no financial data has been collected.
Everything in this document is either (a) a description of what the prototype already demonstrates, or
(b) a plan, clearly marked as pending. Invented interviews, market figures or revenue results would make
this report worthless, so they are absent.

---

## 1. What has actually been validated

| Question | Evidence | Status |
| --- | --- | --- |
| Can the tourism information be organised so one record drives every screen? | 16 seeded destination records drive the homepage, Explore, details, map and planner; 111 automated tests cover the behaviour | Validated as a technical decision |
| Can a rule-based planner produce a readable 1–3 day plan without route data? | The planner groups matching published destinations by proximity/district and spreads them over the days, with explicit warnings about missing travel-time data | Validated as a technical decision |
| Can an administrator maintain the data safely? | Dashboard CRUD with verification fields, publishing, provider approval and inquiry review, all server-side protected | Validated as a technical decision |
| Do tourists find it useful? | No participants have used it | **Pending** |
| Will local providers respond to inquiries? | No provider has been approached | **Pending** |
| Can the product make money? | No pricing test has been run | **Pending** |

## 2. Planned validation work (not started)

### 2.1 Tourist problem interviews — plan
* 8–12 short interviews: 4 first-time visitors to Tripura, 3 residents who host guests, 3 people who
  planned a Tripura trip in the last year but did not go.
* Questions to ask: how they chose destinations, which sources they trusted, what went wrong, what they
  gave up on, whether they would have used a day-wise plan.
* Recruit through local hostels, the Agartala university network and travel groups.
* Output: a short evidence table of quotes mapped to the feature they justify.

### 2.2 Prototype usability sessions — plan
* 5–8 moderated sessions, each participant on their own phone.
* Tasks: find Neermahal by search; filter for lakes in Dhalai; find a homestay and send an inquiry; build a
  2-day plan from Agartala and save it; remove and move a stop.
* Record task success, time on task, and where they hesitated. Fix the top three friction points before
  any further feature work.

### 2.3 Local provider interviews — plan
* 6–10 providers across homestays, guides, food and handicrafts in Agartala, Udaipur, Melaghar and
  Jampui Hills.
* Ask what they currently pay for visibility, what contact details they are willing to publish, and
  whether an inquiry inbox (rather than a booking system) solves a real problem.
* Output: a list of willing partners plus the data-collection form filled in for each.

### 2.4 Competitor and alternative research — plan
* Compare against: state tourism department pages, large travel aggregators, map apps, travel blogs and
  social-media trip threads.
* For each, record coverage of Tripura destinations, whether day-wise planning exists, how fees/hours are
  presented, and the freshness of the data (a dated page is a finding in itself).
* Output: one comparison table and a written statement of where a focused Tripura product can differ.

## 3. Revenue hypotheses (untested)

| Model | Description | Why it might work | Risk |
| --- | --- | --- | --- |
| Verified provider listings | Annual listing fee for homestays, guides, restaurants, transport operators | Providers want discovery; the directory already exists | Requires a sales process and trust infrastructure |
| Feature/placement | Providers can highlight a listing; never inside search results | Standard marketplace revenue | Must be labelled or it damages trust |
| Commission on qualified inquiries | A fee only when an inquiry converts into a booking | Aligns incentives | Requires booking tracking that does not exist yet |
| Tourism department / DMO contract | The state pays for an official Tripura discovery layer | Public data stewardship is a natural fit | Public procurement cycle |
| Content licensing | Licensing the verified dataset and photographs to partners | The dataset is the hard part | Needs licensing clarity per record |
| Sponsorship of itineraries | A local transport operator sponsors a route | Local relevance | Editorial independence risk |

**Cost hypotheses (also untested):** hosting for a small Flask/PostgreSQL application; a tile service once
OpenStreetMap's public tiles are outgrown; field-survey travel and photography; ongoing data-verification
time (the real recurring cost); and content translation into Bengali and Kokborok.

No figure is quoted here on purpose: none has been gathered.

## 4. Business risks

| Risk | Severity | Mitigation |
| --- | --- | --- |
| Wrong fees/hours damage trust faster than missing features | High | Keep unknown fields blank, verify before publishing, show the verification date |
| Data goes stale | High | Six-month re-verification cycle; the admin dashboard records `last_verified_at` |
| Provider expectations exceed the MVP (bookings, payments) | Medium | The product is labelled an inquiry directory everywhere |
| Dependence on a free tile server | Medium | Configurable tile URL; document the migration |
| Single-maintainer risk | Medium | Beginner-friendly structure, seed data, tests, documented runbook |
| Community sensitivity of cultural content | Medium | "Pending community review" labels until reviewed; review before launch |
| Unlicensed imagery | High | Placeholder artwork only; a licence field exists for every real photograph |
| Personal data misuse | High | Collect the minimum, admin-only visibility, privacy note, retention policy |

## 5. Roadmap

**Phase 0 — now (done):** working prototype, test suite, reports, honest data labelling.

**Phase 1 — data (next, the real bottleneck):**
1. Confirm district assignments against official records.
2. Field-survey the six prototype destinations: GPS, fees, hours, closed days, visit duration, photos.
3. Record a verifier and date on each record so `is_verified` and `coordinates_verified` can become true.
4. Replace placeholder illustrations with licensed photographs and credits.

**Phase 2 — validation:** the interviews and usability sessions in section 2.

**Phase 3 — product:** reviews with moderation (only after real users), Bengali/Kokborok interface,
saved-trip sharing improvements, and a considered decision on availability/booking — driven by provider
evidence, not by ambition.

**Phase 4 — operations:** PostgreSQL, a proper tile provider, backups, monitoring, and a named data
maintainer with a review cadence.

## 6. Recommended next three tasks

1. **Verify six destination records properly** (Neermahal, Unakoti, Tripura Sundari Temple, Ujjayanta
   Palace, Jampui Hills, Dumboor Lake) — GPS, fees, hours and licensed photographs — and enter them through
   the admin dashboard so the verification flags become true.
2. **Run the eight usability sessions** on real phones, fix the top three friction points, and record the
   results in this report in place of the "pending" rows.
3. **Approach three local providers**, get their consent and contact preferences, replace the demo listings
   with real approved records, and track whether inquiries receive a response.