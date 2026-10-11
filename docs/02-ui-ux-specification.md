# 02 · UI/UX Specification

**Design intent:** a calm, editorial travel interface that feels trustworthy rather than promotional. Two
colours carry the identity; photography and typography do the rest.

---

## 1. Sitemap

```
Homepage (/)
├── Explore Destinations (/explore)
│   └── Destination Details (/places/<slug>)
│       ├── "Add to trip" → Trip Planner or a saved trip
│       └── Report an incorrect fact (stored for admin review)
├── Interactive Map (/map)
│   └── Marker popup → Destination Details
├── Trip Planner (/trip-planner)
│   └── Saved Trip (/itineraries/<id>)
│       └── Read-only shared link (/shared/<token>)
├── Saved Trips (/my-trips)
├── Local Experiences (/experiences)
│   └── Provider Detail (/experiences/<slug>)
│       └── Send inquiry (stored for admin review)
├── Account
│   ├── Register (/auth/register)
│   ├── Sign in (/auth/login)
│   └── Profile (/profile) — saved trips + favourites
└── Admin (/admin)
    ├── Destinations, Categories, Providers, Inquiries, Corrections, Users
```

## 2. Personas (design-affecting traits)

| Persona | Device | Constraint that shapes the design |
| --- | --- | --- |
| Riya, 27, first-time tourist from Kolkata | Phone | Reads on the move; needs big tap targets, short cards, map-first discovery |
| Subrata, 54, travelling with family | Laptop at home | Needs certainty: fees, hours, accessibility, safety notes, "not verified" honesty |
| Joy, 21, student in Agartala | Phone | Wants a fast 1–2 day plan and cheap options |
| Administrator (tourism office / founder) | Desktop | Needs dense tables, clear status badges, few clicks per record |

## 3. Page workflows

### Homepage
Search or pick a category → either the Explore page (with the filter applied) or a destination card →
details page. Secondary paths: "Plan your trip" → planner, "See where everything is" → map.

### Explore
Filter (keyword, category, district, sort) → the URL carries every filter → cards → details. An empty state
tells the visitor what to change and links to the map.

### Destination details
Overview → Travel information → Nearby → Data & sources → Report an issue. The right-hand card always
offers Directions, Add to trip (or Start a plan) and favourite. Every unknown fact is labelled instead of
hidden.

### Map
Filter → markers update → click a marker for a photo, name, category/district and a details link. The
sidebar mirrors the markers as a text list so the page still works if the tile service is unavailable.

### Trip planner
1. Choose days (1–3), start point, interests, optional budget and date.
2. Generate → the plan appears as day columns with numbered stops, straight-line distances where
   coordinates exist, and warnings where data is missing.
3. Save (sign in) → the trip opens in the editor, where stops can be removed, moved between days or
   dragged into a new order.

### Local experiences
Filter by type and district → provider card → detail page → inquiry form → confirmation. The page states
plainly that this is an inquiry directory, not a booking engine.

### Admin
Dashboard → Destinations (list, edit, publish/unpublish, delete) → Providers (approve/reject) → Inquiries →
Corrections → Users.

## 4. Design tokens

```css
:root{
  --color-primary:      #17365D;  /* navy - brand, headings, primary buttons */
  --color-primary-600:  #1E4A7B;
  --color-background:   #F7F5F0;  /* warm ivory - page background */
  --color-surface:      #FFFFFF;
  --color-text:         #1F2937;
  --color-muted:        #6B7280;
  --color-border:       #E5E7EB;
  --color-accent:       #B08D57;  /* thin editorial accent, never a dominant colour */
  --color-success:      #2F6F4F;
  --color-warning:      #8A5A12;
  --color-danger:       #A4362F;
}
```

Type: serif display for headings (Georgia/Palatino stack, no web-font dependency) and a system sans stack
for body text and UI. Radii: 8 px (inputs), 14 px (cards), 22 px (large panels), pill for chips/buttons.
Spacing scale: 4, 8, 12, 16, 24, 32, 48, 72 px. Shadows are low-contrast navy tints; the layout relies on
whitespace rather than decoration.

**Deliberate constraints:** no green-dominant palette, no rainbow category chips, no gradients beyond the
hero and illustration artwork, no icon font (inline SVG only).

## 5. Wireframe descriptions

| Screen | Structure |
| --- | --- |
| Homepage | Sticky header → three-line hero (headline, supporting copy, search panel) + illustration → category chips with counts → 3-column destination grid → "Plan your trip" split section with an expectations card → navy map band → local experiences row → cultural highlights → 4 stats |
| Explore | Page head with result count → filter card (keyword, category, district, sort, Apply/Clear) → responsive 3/2/1 column card grid → pagination |
| Destination details | Breadcrumb + title block with badges → 2-column body: left = image, gallery, tab bar, tab panels; right = sticky action card (Directions, Add to trip, favourite, quick facts, mini map) → "You may also like" grid |
| Map | Page head → 2-column: filter sidebar with live result list, and the map with attribution + limitations note |
| Trip planner | Page head → 2-column: preferences form (left) and the plan area (right), day columns of numbered stops with images and directions links |
| Saved trip | Breadcrumb + title with share/delete actions → 2-column: editable day columns (drag handle, day selector, remove) and a settings card (title, start, days, budget, date) |
| Local experiences | Page head → demo-data notice → filter card → provider grid → cultural overview by kind → "how inquiries work" and "are you a provider" cards |
| Admin | Page head → 2-column: sidebar nav and content (stat grid, tables, forms) |

## 6. Responsive behaviour

* Mobile-first CSS; breakpoints at 1080 px, 820 px and 520 px.
* At ≤ 820 px the primary navigation becomes a full-width panel toggled by a hamburger button, all grids
  collapse to one column, forms become single-column and the map height reduces to 60 vh.
* Cards switch from horizontal to stacked; tables scroll horizontally inside a wrapper.
* Touch targets are at least 40 px; the favourite button and map result rows are tappable.
* Print styles hide the header, footer and flash messages (useful for a printed itinerary).

## 7. Accessibility decisions

* "Skip to main content" link, semantic landmarks (`header`, `nav`, `main`, `footer`).
* Visible focus rings (`:focus-visible`, 3 px navy outline, 2 px offset).
* Tabs implement the ARIA tab pattern with arrow-key navigation and `aria-selected`.
* Live regions (`role="status"`, `aria-live="polite"`) announce map counts, planner results, saved-trip edits
  and flash messages.
* Every input has a `<label>`; validation errors are text, not colour alone.
* Colour contrast: navy on ivory and ivory on navy both exceed 7:1; muted grey is used only for
  secondary text at 16 px or larger… where it stays above 4.5:1 against ivory.
* `aria-pressed` on favourite buttons, `aria-labelledby` on tab panels, descriptive `alt` text on
  destination artwork, decorative SVG icons marked `aria-hidden`.
* The whole core journey works without JavaScript (planner submission, filters, inquiry form, stop removal
  is the one JavaScript-only convenience — a note explains it and the stop can still be deleted through
  the API/admin).

## 8. States

| State | Treatment |
| --- | --- |
| Loading | Button spinner + disabled state; `aria-busy` on the result region; skeleton class available for future list fetches |
| Empty | Centred card explaining *why* it is empty and the next action (clear filters, open the map, generate a plan) |
| Error | Red-bordered alert with the message returned by the server; validation errors appear under the field |
| Success | Green-tinted alert; flash messages stack bottom-right and auto-dismiss after 7 s |
| Not verified | Amber "Data pending verification" badge; unknown facts print "Not verified" instead of a value |
| Approximate coordinates | Amber marker (brown pin) and an "approximate" badge next to the coordinates |
| Destructive | `window.confirm` before deleting a trip, a stop, a destination or unpublishing (server action still requires a POST + CSRF) |