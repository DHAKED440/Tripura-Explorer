"""Homepage and other general pages."""
from flask import Blueprint, jsonify, render_template

from app.data.cultural_highlights import CULTURAL_HIGHLIGHTS
from app.models import Business, Place
from app.services.destination_service import (
    category_place_counts,
    featured_places,
    list_categories,
    list_districts,
)

bp = Blueprint("main", __name__)


@bp.get("/")
def home():
    """Landing page: search, categories, featured destinations and trip shortcuts."""
    categories = list_categories()
    districts = list_districts()
    featured = featured_places(limit=6)
    published_count = Place.query.filter(Place.is_published.is_(True)).count()
    experiences = (
        Business.query.filter(Business.approval_status == "approved")
        .order_by(Business.name.asc())
        .limit(3)
        .all()
    )
    return render_template(
        "index.html",
        categories=categories,
        category_counts=category_place_counts(),
        districts=districts,
        featured_places=featured,
        published_count=published_count,
        experiences=experiences,
        highlights=CULTURAL_HIGHLIGHTS[:4],
    )


@bp.get("/api/featured-places")
def api_featured_places():
    """JSON feed used by the homepage cards and by external demos."""
    return jsonify({"places": [place.to_dict() for place in featured_places(limit=6)]})


@bp.get("/about")
def about():
    """Project background, data policy and prototype limitations."""
    return render_template(
        "about.html",
        published_count=Place.query.filter(Place.is_published.is_(True)).count(),
        categories=list_categories(),
        districts=list_districts(),
    )