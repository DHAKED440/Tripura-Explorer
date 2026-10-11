"""Local Experiences directory and inquiry handling.

Only administrators can create or approve providers. Public visitors see
approved listings only, and inquiries are stored for review instead of being
treated as a confirmed booking.
"""
from __future__ import annotations

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from email_validator import EmailNotValidError, validate_email
from flask_login import current_user
from sqlalchemy import or_

from app.data.cultural_highlights import grouped_highlights
from app.extensions import db
from app.forms import InquiryForm
from app.models import Business, District, Inquiry
from app.models.business import BUSINESS_CATEGORIES

bp = Blueprint("experiences", __name__)


def validate_inquiry_payload(payload: dict) -> tuple[dict, list[str]]:
    """Shared validation for the JSON API and the HTML form."""
    errors: list[str] = []
    name = str(payload.get("name") or "").strip()
    email = str(payload.get("email") or "").strip()
    phone = str(payload.get("phone") or "").strip()
    message = str(payload.get("message") or "").strip()

    if len(name) < 2:
        errors.append("Please enter your name (at least 2 characters).")
    if len(name) > 120:
        errors.append("Your name is too long (120 characters maximum).")
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        errors.append("Please enter a valid email address.")
    if len(phone) > 40:
        errors.append("The phone number is too long (40 characters maximum).")
    if len(message) < 10:
        errors.append("Please write at least 10 characters in your message.")
    if len(message) > 1200:
        errors.append("The message is too long (1200 characters maximum).")

    cleaned = {
        "name": name,
        "email": email.lower(),
        "phone": phone or None,
        "message": message,
    }
    return cleaned, errors


@bp.get("/experiences")
def index():
    """Directory of approved providers plus an editorial cultural overview."""
    query = Business.query.filter(Business.approval_status == "approved")

    q = (request.args.get("q") or "").strip()[:120]
    category = (request.args.get("category") or "").strip()
    district_value = (request.args.get("district") or "").strip()
    errors: list[str] = []

    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Business.name.ilike(pattern),
                Business.short_description.ilike(pattern),
                Business.locality.ilike(pattern),
            )
        )
    if category:
        if category not in BUSINESS_CATEGORIES:
            errors.append(f"No provider category matches '{category}'.")
            query = query.filter(Business.id.is_(None))
        else:
            query = query.filter(Business.category == category)
    if district_value:
        lowered = district_value.lower()
        district = District.query.filter(
            or_(District.slug == lowered, District.name.ilike(district_value))
        ).first()
        if district is None:
            errors.append(f"No district matches '{district_value}'.")
            query = query.filter(Business.id.is_(None))
        else:
            query = query.filter(Business.district_id == district.id)

    providers = query.order_by(Business.name.asc()).all()
    return render_template(
        "experiences.html",
        providers=providers,
        categories=BUSINESS_CATEGORIES,
        districts=District.query.order_by(District.name.asc()).all(),
        highlights=grouped_highlights(),
        filters={"q": q, "category": category, "district": district_value},
        errors=errors,
        pending_count=Business.query.filter(Business.approval_status == "pending").count(),
    )


@bp.get("/experiences/<slug>")
def detail(slug: str):
    provider = Business.query.filter(Business.slug == slug).first()
    if provider is None or not provider.is_approved:
        abort(404)
    related = (
        Business.query.filter(
            Business.approval_status == "approved",
            Business.category == provider.category,
            Business.id != provider.id,
        )
        .order_by(Business.name.asc())
        .limit(3)
        .all()
    )
    return render_template(
        "business_detail.html",
        provider=provider,
        related=related,
        form=InquiryForm(),
        inquiry_sent=request.args.get("sent") == "1",
    )


@bp.post("/api/inquiries")
def api_create_inquiry():
    payload = request.get_json(silent=True) or request.form
    business_id = payload.get("business_id") or payload.get("business_slug")
    provider = None
    if str(business_id or "").isdigit():
        provider = db.session.get(Business, int(business_id))
    elif business_id:
        provider = Business.query.filter(Business.slug == str(business_id)).first()

    if provider is None or not provider.is_approved:
        return jsonify({"error": "not_found", "message": "Provider not found."}), 404

    cleaned, errors = validate_inquiry_payload(payload)
    if errors:
        return jsonify({"error": "validation_failed", "errors": errors}), 400

    inquiry = Inquiry(
        business_id=provider.id,
        user_id=current_user.id if current_user.is_authenticated else None,
        name=cleaned["name"],
        email=cleaned["email"],
        phone=cleaned["phone"],
        message=cleaned["message"],
    )
    db.session.add(inquiry)
    db.session.commit()
    return (
        jsonify(
            {
                "status": "received",
                "inquiry_id": inquiry.id,
                "message": (
                    "Thank you. Your inquiry has been recorded and an administrator will review it. "
                    "This prototype does not confirm bookings."
                ),
            }
        ),
        201,
    )


@bp.post("/experiences/<slug>/inquire")
def submit_inquiry_form(slug: str):
    """No-JavaScript fallback for the inquiry form."""
    provider = Business.query.filter(Business.slug == slug).first()
    if provider is None or not provider.is_approved:
        abort(404)
    form = InquiryForm()
    if form.validate_on_submit():
        inquiry = Inquiry(
            business_id=provider.id,
            user_id=current_user.id if current_user.is_authenticated else None,
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            phone=(form.phone.data or "").strip() or None,
            message=form.message.data.strip(),
        )
        db.session.add(inquiry)
        db.session.commit()
        flash("Thank you — your inquiry has been recorded for review.", "success")
        return redirect(url_for("experiences.detail", slug=provider.slug, sent=1))
    for field_errors in form.errors.values():
        for error in field_errors:
            flash(error, "error")
    return redirect(url_for("experiences.detail", slug=provider.slug))