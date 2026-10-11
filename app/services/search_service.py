"""Search, filtering, sorting and pagination for the Explore page."""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import or_

from app.models import Category, District, Place
from app.services.destination_service import base_query

SORT_OPTIONS = {
    "popular": ("Most popular", None),
    "name": ("Name (A-Z)", "name"),
    "name_desc": ("Name (Z-A)", "name_desc"),
    "newest": ("Recently added", "newest"),
}


@dataclass
class ExploreFilters:
    """Validated query parameters for the Explore page."""

    q: str = ""
    category: str = ""          # category slug
    district: str = ""          # district slug or display name
    sort: str = "popular"
    page: int = 1
    per_page: int = 9
    errors: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.q or self.category or self.district)

    def as_query_params(self) -> dict:
        params = {}
        if self.q:
            params["q"] = self.q
        if self.category:
            params["category"] = self.category
        if self.district:
            params["district"] = self.district
        if self.sort != "popular":
            params["sort"] = self.sort
        return params


def parse_filters(args, per_page: int = 9) -> ExploreFilters:
    """Read and validate filters from a request query string.

    Invalid values never raise: unknown categories/districts simply produce an
    empty result set and a human readable message.
    """
    raw_q = (args.get("q") or "").strip()[:120]
    raw_category = (args.get("category") or "").strip().lower()[:60]
    raw_district = (args.get("district") or "").strip()[:60]
    raw_sort = (args.get("sort") or "popular").strip().lower()

    filters = ExploreFilters(
        q=raw_q,
        category=raw_category,
        district=raw_district,
        sort=raw_sort if raw_sort in SORT_OPTIONS else "popular",
        per_page=max(1, min(int(per_page or 9), 24)),
    )

    if raw_sort and raw_sort not in SORT_OPTIONS:
        filters.errors.append(f"Unknown sort option '{raw_sort}' — showing the default order.")

    try:
        page = int(args.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    filters.page = max(1, page)

    if raw_category and not Category.query.filter(Category.slug == raw_category).first():
        filters.errors.append(f"No category matches '{raw_category}'.")

    if raw_district and not _district_exists(raw_district):
        filters.errors.append(f"No district matches '{raw_district}'.")

    return filters


def _district_exists(value: str) -> bool:
    lowered = value.strip().lower()
    return (
        District.query.filter(
            or_(District.slug == lowered, District.name.ilike(value.strip()))
        ).first()
        is not None
    )


def _resolve_district(value: str) -> District | None:
    lowered = value.strip().lower()
    return District.query.filter(
        or_(District.slug == lowered, District.name.ilike(value.strip()))
    ).first()


def build_query(filters: ExploreFilters):
    """Turn validated filters into a SQLAlchemy query."""
    query = base_query()

    if filters.q:
        pattern = f"%{filters.q}%"
        query = query.filter(
            or_(
                Place.name.ilike(pattern),
                Place.locality.ilike(pattern),
                Place.short_description.ilike(pattern),
                Place.description.ilike(pattern),
                Place.extra_tags.ilike(pattern),
            )
        )

    if filters.category:
        category = Category.query.filter(Category.slug == filters.category).first()
        if category is None:
            query = query.filter(Place.id.is_(None))  # deliberate empty result
        else:
            query = query.filter(Place.category_id == category.id)

    if filters.district:
        district = _resolve_district(filters.district)
        if district is None:
            query = query.filter(Place.id.is_(None))
        else:
            query = query.filter(Place.district_id == district.id)

    return query


def sort_query(query, sort: str):
    if sort == "name":
        return query.order_by(Place.name.asc())
    if sort == "name_desc":
        return query.order_by(Place.name.desc())
    if sort == "newest":
        return query.order_by(Place.created_at.desc(), Place.name.asc())
    return query.order_by(Place.popularity.desc(), Place.name.asc())


def search(filters: ExploreFilters):
    """Return ``(items, total, pages)`` for the given filters."""
    query = sort_query(build_query(filters), filters.sort)
    pagination = query.paginate(page=filters.page, per_page=filters.per_page, error_out=False)
    return pagination.items, pagination.total, pagination.pages


def search_places_for_interests(interests: list[str], limit: int = 30) -> list[Place]:
    """Destinations matching any of the requested interests (planner input)."""
    wanted = {interest.strip().lower() for interest in interests if interest.strip()}
    if not wanted:
        return []

    categories = Category.query.all()
    category_by_slug = {category.slug: category for category in categories}
    wanted_ids = {
        category_by_slug[slug].id
        for slug in wanted
        if slug in category_by_slug
    }

    query = base_query().order_by(Place.popularity.desc(), Place.name.asc()).limit(limit)
    results = []
    for place in query.all():
        tags = {tag.lower() for tag in place.tag_list}
        if tags & wanted or (place.category_id in wanted_ids):
            results.append(place)
    return results