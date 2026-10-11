"""Registration, sign in, profile and favourites."""
from __future__ import annotations

from urllib.parse import urlparse

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.forms import LoginForm, RegistrationForm
from app.models import Favorite, Place, User

bp = Blueprint("auth", __name__)


def _safe_next(target: str | None) -> str | None:
    """Only allow relative redirects so ``?next=`` cannot be abused."""
    if not target:
        return None
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc or not target.startswith("/") or target.startswith("//"):
        return None
    return target


@bp.route("/auth/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("auth.profile"))
    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            form.email.errors.append("An account with this email already exists.")
        else:
            user = User(name=form.name.data.strip(), email=email, role="user")
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Welcome to Tripura Explore! Your account is ready.", "success")
            return redirect(_safe_next(request.args.get("next")) or url_for("auth.profile"))
    return render_template("auth/register.html", form=form)


@bp.route("/auth/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.profile"))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(form.password.data):
            flash("Email or password is incorrect.", "error")
        else:
            login_user(user, remember=form.remember.data)
            flash(f"Signed in as {user.name}.", "success")
            return redirect(_safe_next(request.args.get("next")) or url_for("auth.profile"))
    return render_template("auth/login.html", form=form)


@bp.post("/auth/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("main.home"))


@bp.get("/profile")
@login_required
def profile():
    favorites = (
        Favorite.query.filter_by(user_id=current_user.id)
        .join(Place, Favorite.place_id == Place.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
    from app.models import Itinerary

    trips = (
        Itinerary.query.filter_by(user_id=current_user.id)
        .order_by(Itinerary.updated_at.desc())
        .all()
    )
    return render_template("auth/profile.html", favorites=favorites, trips=trips)


@bp.post("/api/favorites")
@login_required
def api_add_favorite():
    payload = request.get_json(silent=True) or request.form
    place_id = payload.get("place_id")
    place = db.session.get(Place, int(place_id)) if str(place_id or "").isdigit() else None
    if place is None or not place.is_published:
        return jsonify({"error": "not_found", "message": "Destination not found."}), 404

    existing = Favorite.query.filter_by(user_id=current_user.id, place_id=place.id).first()
    if existing is None:
        db.session.add(Favorite(user_id=current_user.id, place_id=place.id))
        db.session.commit()
    return jsonify({"place_id": place.id, "is_favorite": True}), 201


@bp.delete("/api/favorites/<int:place_id>")
@login_required
def api_remove_favorite(place_id: int):
    favorite = Favorite.query.filter_by(user_id=current_user.id, place_id=place_id).first()
    if favorite is not None:
        db.session.delete(favorite)
        db.session.commit()
    return jsonify({"place_id": place_id, "is_favorite": False}), 200


@bp.post("/places/<slug>/favorite")
@login_required
def toggle_favorite_form(slug: str):
    """Progressive-enhancement fallback for the favourite button."""
    place = Place.query.filter(Place.slug == slug, Place.is_published.is_(True)).first()
    if place is None:
        from flask import abort

        abort(404)
    favorite = Favorite.query.filter_by(user_id=current_user.id, place_id=place.id).first()
    if favorite is None:
        db.session.add(Favorite(user_id=current_user.id, place_id=place.id))
        db.session.commit()
        flash(f"Added {place.name} to your favourites.", "success")
    else:
        db.session.delete(favorite)
        db.session.commit()
        flash(f"Removed {place.name} from your favourites.", "info")
    return redirect(url_for("places.detail", slug=place.slug))