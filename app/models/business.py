"""Local tourism providers (homestays, guides, restaurants, ...) and inquiries.

The MVP treats this as an *inquiry directory*: it deliberately does not show
live availability or accept bookings.  Personal data collected by an inquiry is
only visible to administrators.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.extensions import db

BUSINESS_CATEGORIES = [
    "Homestay",
    "Local Guide",
    "Restaurant",
    "Transport",
    "Handicrafts",
    "Cultural Experience",
]

BUSINESS_STATUSES = ["pending", "approved", "rejected"]
INQUIRY_STATUSES = ["new", "in_progress", "closed"]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Business(db.Model):
    __tablename__ = "businesses"

    id = db.Column(db.Integer, primary_key=True)
    district_id = db.Column(db.Integer, db.ForeignKey("districts.id"), nullable=True, index=True)

    name = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(160), unique=True, nullable=False, index=True)
    category = db.Column(db.String(60), nullable=False, index=True)
    short_description = db.Column(db.String(300))
    description = db.Column(db.Text)

    locality = db.Column(db.String(160))
    address = db.Column(db.String(300))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    contact_name = db.Column(db.String(160))
    contact_phone = db.Column(db.String(40))
    contact_email = db.Column(db.String(180))
    languages = db.Column(db.String(160))
    price_note = db.Column(db.String(200))
    image_url = db.Column(db.String(400))
    image_alt = db.Column(db.String(300))

    approval_status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    status_note = db.Column(db.String(300))
    verified_on = db.Column(db.Date)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    district = db.relationship("District")
    inquiries = db.relationship("Inquiry", back_populates="business", cascade="all, delete-orphan", lazy="dynamic")

    @property
    def is_approved(self) -> bool:
        return self.approval_status == "approved"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "category": self.category,
            "short_description": self.short_description,
            "district": self.district.name if self.district else None,
            "locality": self.locality,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "languages": self.languages,
            "price_note": self.price_note,
            "image_url": self.image_url,
            "url": f"/experiences/{self.slug}",
        }

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<Business {self.slug} {self.approval_status}>"


class Inquiry(db.Model):
    __tablename__ = "inquiries"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), nullable=False)
    phone = db.Column(db.String(40))
    message = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(20), nullable=False, default="new", index=True)
    admin_note = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    business = db.relationship("Business", back_populates="inquiries")

    def to_admin_dict(self) -> dict:
        return {
            "id": self.id,
            "business": self.business.name if self.business else None,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "message": self.message,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<Inquiry {self.id} {self.status}>"