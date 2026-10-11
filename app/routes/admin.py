"""Administrator dashboard.

Every route in this blueprint is protected on the server by ``admin_required``.
Hiding a link is never treated as access control.
"""
from __future__ import annotations

from functools import wraps

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.extensions import db
from app.forms import (
    BusinessForm,
    CorrectionStatusForm,
    InquiryStatusForm,
    PlaceForm,
)
from app.models import Business, Category, CorrectionReport, District, Inquiry, Place, User
from app.services.destination_service import dashboard_stats

bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    """Allow only signed in administrators; everybody else gets 403."""

    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapper


def _set_form_choices(form) -> None:
    """Fill the category/district selects from the database."""
    form.category_id.choices = [
        (category.id, category.name) for category in Category.query.order_by(Category.name.asc()).all()
    ]
    form.district_id.choices = [("", "— not recorded —")] + [
        (str(district.id), district.name) for district in District.query.order_by(District.name.asc()).all()
    ]


@bp.get("")
@admin_required
def dashboard():
    return render_template(
        "admin/dashboard.html",
        stats=dashboard_stats(),
        recent_places=Place.query.order_by(Place.updated_at.desc()).limit(6).all(),
        recent_inquiries=Inquiry.query.order_by(Inquiry.created_at.desc()).limit(5).all(),
        new_corrections=CorrectionReport.query.filter(CorrectionReport.status == "new").limit(5).all(),
    )


# --------------------------------------------------------------------------- #
# destinations
# --------------------------------------------------------------------------- #
@bp.get("/places")
@admin_required
def places():
    q = (request.args.get("q") or "").strip()[:120]
    status = (request.args.get("status") or "").strip()
    query = Place.query
    if q:
        pattern = f"%{q}%"
        query = query.filter(or_(Place.name.ilike(pattern), Place.slug.ilike(pattern), Place.locality.ilike(pattern)))
    if status == "published":
        query = query.filter(Place.is_published.is_(True))
    elif status == "draft":
        query = query.filter(Place.is_published.is_(False))
    elif status == "unverified":
        query = query.filter(Place.is_verified.is_(False))
    return render_template(
        "admin/places.html",
        places=query.order_by(Place.updated_at.desc()).all(),
        q=q,
        status=status,
    )


@bp.route("/places/new", methods=["GET", "POST"])
@admin_required
def place_new():
    form = PlaceForm()
    _set_form_choices(form)
    if form.validate_on_submit():
        if Place.query.filter_by(slug=form.slug.data.strip()).first():
            form.slug.errors.append("That slug is already used by another destination.")
        else:
            place = Place()
            _apply_place_form(place, form)
            db.session.add(place)
            db.session.commit()
            flash(f"Created destination “{place.name}”.", "success")
            return redirect(url_for("admin.places"))
    return render_template("admin/place_form.html", form=form, place=None)


@bp.route("/places/<int:place_id>/edit", methods=["GET", "POST"])
@admin_required
def place_edit(place_id: int):
    place = db.session.get(Place, place_id)
    if place is None:
        abort(404)
    form = PlaceForm(obj=place)
    _set_form_choices(form)
    if request.method == "GET":
        form.category_id.data = place.category_id
        form.district_id.data = str(place.district_id) if place.district_id else ""
    if form.validate_on_submit():
        clash = Place.query.filter(Place.slug == form.slug.data.strip(), Place.id != place.id).first()
        if clash:
            form.slug.errors.append("That slug is already used by another destination.")
        else:
            _apply_place_form(place, form)
            db.session.commit()
            flash(f"Saved “{place.name}”.", "success")
            return redirect(url_for("admin.places"))
    return render_template("admin/place_form.html", form=form, place=place)


def _apply_place_form(place: Place, form: PlaceForm) -> None:
    """Copy validated form data onto a Place record."""
    place.name = form.name.data.strip()
    place.slug = form.slug.data.strip()
    place.tagline = (form.tagline.data or "").strip() or None
    place.short_description = (form.short_description.data or "").strip() or None
    place.description = (form.description.data or "").strip() or None
    place.category_id = form.category_id.data
    place.district_id = form.district_id.data
    place.locality = (form.locality.data or "").strip() or None
    place.address = (form.address.data or "").strip() or None
    place.latitude = float(form.latitude.data) if form.latitude.data is not None else None
    place.longitude = float(form.longitude.data) if form.longitude.data is not None else None
    place.coordinates_verified = bool(form.coordinates_verified.data)
    place.coordinate_source = (form.coordinate_source.data or "").strip() or None
    place.image_url = (form.image_url.data or "").strip() or None
    place.image_alt = (form.image_alt.data or "").strip() or None
    place.entry_fee_indian = (form.entry_fee_indian.data or "").strip() or None
    place.entry_fee_foreign = (form.entry_fee_foreign.data or "").strip() or None
    place.opening_info = (form.opening_info.data or "").strip() or None
    place.closed_day = (form.closed_day.data or "").strip() or None
    place.best_season = (form.best_season.data or "").strip() or None
    place.typical_visit_hours = float(form.typical_visit_hours.data) if form.typical_visit_hours.data is not None else None
    place.facilities = (form.facilities.data or "").strip() or None
    place.accessibility_info = (form.accessibility_info.data or "").strip() or None
    place.safety_notes = (form.safety_notes.data or "").strip() or None
    place.contact_info = (form.contact_info.data or "").strip() or None
    place.extra_tags = (form.extra_tags.data or "").strip() or None
    place.popularity = form.popularity.data or 0
    place.is_published = bool(form.is_published.data)
    place.is_verified = bool(form.is_verified.data)
    place.verified_by = (form.verified_by.data or "").strip() or None
    place.last_verified_at = form.last_verified_at.data
    place.verification_notes = (form.verification_notes.data or "").strip() or None
    place.source_note = (form.source_note.data or "").strip() or None


@bp.post("/places/<int:place_id>/publish")
@admin_required
def publish_place(place_id: int):
    place = db.session.get(Place, place_id)
    if place is None:
        abort(404)
    place.is_published = True
    db.session.commit()
    flash(f"“{place.name}” is now published.", "success")
    return redirect(request.referrer or url_for("admin.places"))


@bp.post("/places/<int:place_id>/unpublish")
@admin_required
def unpublish_place(place_id: int):
    place = db.session.get(Place, place_id)
    if place is None:
        abort(404)
    place.is_published = False
    db.session.commit()
    flash(f"“{place.name}” is now hidden from the public site.", "info")
    return redirect(request.referrer or url_for("admin.places"))


@bp.post("/places/<int:place_id>/delete")
@admin_required
def delete_place(place_id: int):
    place = db.session.get(Place, place_id)
    if place is None:
        abort(404)
    name = place.name
    db.session.delete(place)
    db.session.commit()
    flash(f"Deleted “{name}”.", "success")
    return redirect(url_for("admin.places"))


# --------------------------------------------------------------------------- #
# categories
# --------------------------------------------------------------------------- #
@bp.route("/categories", methods=["GET", "POST"])
@admin_required
def categories():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        slug = (request.form.get("slug") or "").strip().lower()
        if len(name) < 2 or len(slug) < 2:
            flash("Provide both a category name and a slug.", "error")
        elif Category.query.filter(or_(Category.name == name, Category.slug == slug)).first():
            flash("That category already exists.", "error")
        else:
            db.session.add(
                Category(name=name, slug=slug, description=(request.form.get("description") or "").strip() or None)
            )
            db.session.commit()
            flash(f"Added category “{name}”.", "success")
        return redirect(url_for("admin.categories"))
    return render_template(
        "admin/categories.html",
        categories=Category.query.order_by(Category.name.asc()).all(),
        districts=District.query.order_by(District.name.asc()).all(),
    )


# --------------------------------------------------------------------------- #
# providers
# --------------------------------------------------------------------------- #
@bp.get("/providers")
@admin_required
def providers():
    status = (request.args.get("status") or "").strip()
    query = Business.query
    if status in {"pending", "approved", "rejected"}:
        query = query.filter(Business.approval_status == status)
    return render_template(
        "admin/providers.html",
        providers=query.order_by(Business.name.asc()).all(),
        status=status,
    )


@bp.route("/providers/new", methods=["GET", "POST"])
@admin_required
def provider_new():
    form = BusinessForm()
    _set_business_choices(form)
    if form.validate_on_submit():
        if Business.query.filter_by(slug=form.slug.data.strip()).first():
            form.slug.errors.append("That slug is already used by another provider.")
        else:
            provider = Business()
            _apply_business_form(provider, form)
            db.session.add(provider)
            db.session.commit()
            flash(f"Created provider “{provider.name}”.", "success")
            return redirect(url_for("admin.providers"))
    return render_template("admin/provider_form.html", form=form, provider=None)


@bp.route("/providers/<int:provider_id>/edit", methods=["GET", "POST"])
@admin_required
def provider_edit(provider_id: int):
    provider = db.session.get(Business, provider_id)
    if provider is None:
        abort(404)
    form = BusinessForm(obj=provider)
    _set_business_choices(form)
    if request.method == "GET":
        form.district_id.data = str(provider.district_id) if provider.district_id else ""
    if form.validate_on_submit():
        _apply_business_form(provider, form)
        db.session.commit()
        flash(f"Saved “{provider.name}”.", "success")
        return redirect(url_for("admin.providers"))
    return render_template("admin/provider_form.html", form=form, provider=provider)


def _set_business_choices(form) -> None:
    form.district_id.choices = [("", "— not recorded —")] + [
        (str(district.id), district.name) for district in District.query.order_by(District.name.asc()).all()
    ]


def _apply_business_form(provider: Business, form: BusinessForm) -> None:
    provider.name = form.name.data.strip()
    provider.slug = form.slug.data.strip()
    provider.category = form.category.data
    provider.district_id = form.district_id.data
    provider.short_description = (form.short_description.data or "").strip() or None
    provider.description = (form.description.data or "").strip() or None
    provider.locality = (form.locality.data or "").strip() or None
    provider.address = (form.address.data or "").strip() or None
    provider.contact_name = (form.contact_name.data or "").strip() or None
    provider.contact_phone = (form.contact_phone.data or "").strip() or None
    provider.contact_email = (form.contact_email.data or "").strip().lower() or None
    provider.languages = (form.languages.data or "").strip() or None
    provider.price_note = (form.price_note.data or "").strip() or None
    provider.image_url = (form.image_url.data or "").strip() or None
    provider.image_alt = (form.image_alt.data or "").strip() or None
    provider.approval_status = form.approval_status.data
    provider.status_note = (form.status_note.data or "").strip() or None


@bp.post("/providers/<int:provider_id>/approve")
@admin_required
def approve_provider(provider_id: int):
    provider = db.session.get(Business, provider_id)
    if provider is None:
        abort(404)
    provider.approval_status = "approved"
    db.session.commit()
    flash(f"Approved “{provider.name}”.", "success")
    return redirect(request.referrer or url_for("admin.providers"))


@bp.post("/providers/<int:provider_id>/reject")
@admin_required
def reject_provider(provider_id: int):
    provider = db.session.get(Business, provider_id)
    if provider is None:
        abort(404)
    provider.approval_status = "rejected"
    db.session.commit()
    flash(f"Rejected “{provider.name}”.", "info")
    return redirect(request.referrer or url_for("admin.providers"))


# --------------------------------------------------------------------------- #
# inquiries and corrections
# --------------------------------------------------------------------------- #
@bp.get("/inquiries")
@admin_required
def inquiries():
    status = (request.args.get("status") or "").strip()
    query = Inquiry.query
    if status in {"new", "in_progress", "closed"}:
        query = query.filter(Inquiry.status == status)
    form = InquiryStatusForm()
    return render_template(
        "admin/inquiries.html",
        inquiries=query.order_by(Inquiry.created_at.desc()).all(),
        status=status,
        form=form,
    )


@bp.post("/inquiries/<int:inquiry_id>/status")
@admin_required
def update_inquiry(inquiry_id: int):
    inquiry = db.session.get(Inquiry, inquiry_id)
    if inquiry is None:
        abort(404)
    form = InquiryStatusForm()
    if form.validate_on_submit():
        inquiry.status = form.status.data
        inquiry.admin_note = (form.admin_note.data or "").strip() or None
        db.session.commit()
        flash("Inquiry updated.", "success")
    else:
        flash("Could not update that inquiry.", "error")
    return redirect(url_for("admin.inquiries"))


@bp.get("/corrections")
@admin_required
def corrections():
    status = (request.args.get("status") or "").strip()
    query = CorrectionReport.query
    if status in {"new", "reviewing", "resolved", "rejected"}:
        query = query.filter(CorrectionReport.status == status)
    return render_template(
        "admin/corrections.html",
        corrections=query.order_by(CorrectionReport.created_at.desc()).all(),
        status=status,
        form=CorrectionStatusForm(),
    )


@bp.post("/corrections/<int:report_id>/status")
@admin_required
def update_correction(report_id: int):
    report = db.session.get(CorrectionReport, report_id)
    if report is None:
        abort(404)
    form = CorrectionStatusForm()
    if form.validate_on_submit():
        report.status = form.status.data
        report.admin_note = (form.admin_note.data or "").strip() or None
        db.session.commit()
        flash("Correction report updated.", "success")
    else:
        flash("Could not update that report.", "error")
    return redirect(url_for("admin.corrections"))


@bp.get("/users")
@admin_required
def users():
    return render_template("admin/users.html", users=User.query.order_by(User.created_at.desc()).all())


@bp.post("/users/<int:user_id>/role")
@admin_required
def update_user_role(user_id: int):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    if user.id == current_user.id:
        flash("You cannot change your own role.", "error")
        return redirect(url_for("admin.users"))
    role = (request.form.get("role") or "user").strip().lower()
    if role not in {"user", "admin"}:
        flash("Unknown role.", "error")
    else:
        user.role = role
        db.session.commit()
        flash(f"{user.email} is now {role}.", "success")
    return redirect(url_for("admin.users"))