"""Explore listings, destination details and the public place API."""
from __future__ import annotations

from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.forms import CorrectionForm
from app.models import CorrectionReport, Favorite, Place
from app.services.destination_service import (
    get_place_by_slug,
    list_categories,
    list_districts,
    nearby_places,
    related_by_interest,
)
from app.services.search_service import SORT_OPTIONS, parse_filters, search

bp = Blueprint("places", __name__)


@bp.get("/explore")
def explore():
    """Filterable, paginated destination grid driven by query parameters."""
    filters = parse_filters(request.args, per_page=current_app.config["PLACES_PER_PAGE"])
    items, total, pages = search(filters)
    favorite_ids = current_user.favorite_place_ids() if current_user.is_authenticated else set()
    return render_template(
        "explore.html",
        places=items,
        total=total,
        pages=pages,
        filters=filters,
        categories=list_categories(),
        districts=list_districts(),
        sort_options=SORT_OPTIONS,
        favorite_ids=favorite_ids,
    )


@bp.get("/api/places")
def api_places():
    """Same results as ``/explore`` in JSON form."""
    filters = parse_filters(request.args, per_page=current_app.config["PLACES_PER_PAGE"])
    items, total, pages = search(filters)
    return jsonify(
        {
            "total": total,
            "pages": pages,
            "page": filters.page,
            "filters": filters.as_query_params(),
            "errors": filters.errors,
            "places": [place.to_dict() for place in items],
        }
    )


@bp.get("/places/<slug>")
def detail(slug: str):
    """Destination details. Unpublished or unknown slugs return 404."""
    place = get_place_by_slug(slug)
    if place is None:
        abort(404)

    is_favorite = False
    if current_user.is_authenticated:
        is_favorite = (
            Favorite.query.filter_by(user_id=current_user.id, place_id=place.id).first() is not None
        )

    return render_template(
        "place_detail.html",
        place=place,
        nearby=nearby_places(place, limit=4),
        also_like=related_by_interest(place, limit=3),
        is_favorite=is_favorite,
        correction_form=CorrectionForm(),
        travel_hints=_travel_hints(place),
    )


@bp.get("/api/places/<slug>")
def api_place(slug: str):
    place = get_place_by_slug(slug)
    if place is None:
        return jsonify({"error": "Destination not found"}), 404
    return jsonify({"place": place.to_dict(include_admin_fields=True)})


@bp.post("/places/<slug>/report")
def report_problem(slug: str):
    """Store a user submitted correction so an administrator can review it."""
    place = get_place_by_slug(slug)
    if place is None:
        abort(404)

    form = CorrectionForm()
    if form.validate_on_submit():
        report = CorrectionReport(
            place_id=place.id,
            message=form.message.data.strip(),
            reporter_email=(form.reporter_email.data or "").strip().lower() or None,
        )
        try:
            db.session.add(report)
            db.session.commit()
            flash("Thank you — your report has been sent to the site administrators.", "success")
        except SQLAlchemyError:  # pragma: no cover - defensive
            db.session.rollback()
            flash("Sorry, the report could not be saved. Please try again later.", "error")
    else:
        flash("Please describe the problem in at least 10 characters.", "error")
    return redirect(url_for("places.detail", slug=place.slug) + "#report")


def _travel_hints(place: Place) -> list[dict]:
    """Honest travel information: only show what the record actually contains."""
    hints = []
    if place.best_season:
        hints.append({"label": "Best season", "value": place.best_season})
    if place.opening_info:
        hints.append({"label": "Opening hours", "value": place.opening_info})
    if place.closed_day:
        hints.append({"label": "Closed", "value": place.closed_day})
    if place.entry_fee_indian or place.entry_fee_foreign:
        hints.append(
            {
                "label": "Entry fee",
                "value": " · ".join(filter(None, [place.entry_fee_indian, place.entry_fee_foreign])),
            }
        )
    if place.typical_visit_hours:
        hints.append({"label": "Time needed", "value": f"{place.typical_visit_hours:g} hours"})
    if place.facilities:
        hints.append({"label": "Facilities", "value": place.facilities})
    return hints