# 07 · Analytics and Evaluation Report

**Honest status: there is no real usage data yet.** The prototype has been exercised by automated tests and
by the developer, not by tourists. Every number in this document is therefore either (a) a count taken from
the seeded database, or (b) a *definition* of the metric to collect once real visitors arrive. Nothing here
is invented.

---

## 1. What can be measured today (from the database)

| Metric | Value | Source |
| --- | --- | --- |
| Published destinations | 15 | `places WHERE is_published = 1` |
| Draft destinations | 1 | `places WHERE is_published = 0` |
| Categories | 7 | `categories` |
| Districts | 8 | `districts` |
| Districts with at least one destination | 7 | Khowai has none (the filter shows an empty state) |
| Records with verified information | 0 | `places WHERE is_verified = 1` |
| Records with verified coordinates | 0 | `places WHERE coordinates_verified = 1` |
| Destination records with any fee or opening hours | 0 | fees/hours are NULL until verified |
| Approved providers | 4 (all demo listings) | `businesses WHERE approval_status = 'approved'` |
| Providers awaiting approval | 2 | `businesses WHERE approval_status = 'pending'` |
| Saved trips | 0 | created by users, not seeded |
| Inquiries | 0 | created by visitors, not seeded |

These are *content-completeness* numbers. They already tell the team something useful: the product is fully
built but the data is not, and the biggest single gap is field verification.

## 2. Metrics to collect once visitors use the prototype

| Metric | Definition | Event / query needed | Why it matters |
| --- | --- | --- | --- |
| Search usage | Number of searches per session, and the share of searches with a result | Log `query`, `result_count`, `category`, `district` | Shows whether discovery works |
| Search success rate | Sessions with ≥ 1 destination detail view after a search ÷ sessions with a search | Join search log with page views (session id) | The clearest discovery quality signal |
| Empty-result rate | Searches/filters with 0 results ÷ all searches | `result_count = 0` | Guides the next data-collection trip |
| Popular destinations | Detail-page views per destination | `place_view` events | Refines the editorial `popularity` field |
| Category vs district filter usage | Which filter actually narrows results | `filter_applied` events | Decides which filters stay |
| Map engagement | Marker clicks and filter changes per session | `map_marker_click`, `map_filter` | Tests whether the map earns its place |
| Planner engagement | Sessions opening the planner after viewing a destination | Funnel: view → planner | Measures whether discovery turns into planning |
| Itinerary creation | Plans generated ÷ planner sessions | `plan_generated` with `duration_days`, `interests` | Core feature health |
| Plan completion | Plans saved ÷ plans generated | `plan_saved` | The most important conversion |
| Plan editing depth | Stops added, moved or removed per saved trip | Stop API calls | Tells whether the generated order is good enough |
| Share usage | Trips shared ÷ trips saved | `share_enabled` | Profile of group travellers |
| Provider interest | Inquiries per provider per month | `inquiries` table | Decides whether the directory deserves investment |
| Correction reports | Reports per destination | `correction_reports` | Data quality feedback loop |
| Mobile share | Sessions by viewport class | User-agent / client hint | Confirms the mobile-first bet |

## 3. How collection would be implemented (privacy-first)

1. **Server-side events only.** Log the event name, an anonymous session id (a random value in the signed
   session cookie), the route, the filter values and the outcome. No raw IP storage, no third-party
   trackers, no advertising pixels.
2. **Aggregate after 30 days.** Raw rows are summarised and then deleted, because the Digital Personal Data
   Protection Act 2023 expects data minimisation.
3. **Never log personal data.** Inquiry messages, emails and passwords never enter the analytics table.
4. **No location tracking.** The product deliberately does not request device GPS in this version.
5. **A visible privacy note** on the About page explaining what is collected and why, before any logging
   ships.

A minimal schema for the future work:

```
events(id, session_id, name, route, payload_json, created_at)
```

## 4. Evaluation of the current build

**What the prototype proves**

* The whole primary journey works end to end and is covered by automated tests: search → details → map →
  planner → save → edit → share.
* A single destination record can drive six screens without duplicated facts.
* The honesty rules are enforceable in the product, not just in a document: unverified fields render as
  "Not verified", approximate coordinates are labelled on both the map and the details page, and the
  planner states what it cannot estimate.
* Administration does not require touching the database.

**What cannot be claimed**

* No tourist has used the site, so no usability or conversion claim is possible.
* No provider has been approached, so the inquiry directory's value is unproven.
* The itinerary quality cannot be judged against real travel times, because verified coordinates, visit
  durations and opening hours do not exist yet.
* Mobile usability on physical devices has not been measured (see `KNOWN-LIMITATIONS.md`).

## 5. Proposed next measurements

| Order | Measurement | Trigger to proceed |
| --- | --- | --- |
| 1 | Content completeness after the first field survey (fees, hours, coordinates per record) | ≥ 10 records fully verified |
| 2 | Moderated usability sessions with 5–8 tourists on their own phones | Task success ≥ 80 % for "find a place and plan one day" |
| 3 | Instrumented search and planner funnel for two weeks with consent | Enough sessions to read a funnel (~200) |
| 4 | Provider interviews and inquiry response rates | 3–5 providers, ≥ 50 % responding |
| 5 | Only then: consider reviews, bookings or paid listings | Positive provider and traveller signals |