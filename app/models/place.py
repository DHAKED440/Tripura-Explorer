"""The destination record - the heart of the application.

Every public screen (home, explore, details, map, trip planner) is driven by
this single table so destination facts are never duplicated in templates.
"""
from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote_plus

from sqlalchemy import CheckConstraint, Index

from app.extensions import db


def utcnow() -> datetime:
    """Timezone aware ``now`` used by default columns."""
    return datetime.now(timezone.utc)


class Place(db.Model):
    __tablename__ = "places"
    __table_args__ = (
        CheckConstraint("latitude IS NULL OR (latitude >= -90 AND latitude <= 90)", name="ck_places_latitude"),
        CheckConstraint("longitude IS NULL OR (longitude >= -180 AND longitude <= 180)", name="ck_places_longitude"),
        CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL) OR (latitude IS NOT NULL AND longitude IS NOT NULL)",
            name="ck_places_lat_lng_together",
        ),
        Index("ix_places_published_popularity", "is_published", "popularity"),
    )

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True)
    district_id = db.Column(db.Integer, db.ForeignKey("districts.id"), nullable=True, index=True)

    name = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(160), unique=True, nullable=False, index=True)
    tagline = db.Column(db.String(200))
    short_description = db.Column(db.String(300))
    description = db.Column(db.Text)

    locality = db.Column(db.String(160))
    address = db.Column(db.String(300))
    plus_code = db.Column(db.String(32))

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    # Coordinates are only treated as trustworthy when a human verified them.
    coordinates_verified = db.Column(db.Boolean, nullable=False, default=False)
    coordinate_source = db.Column(db.String(300))

    image_url = db.Column(db.String(400))
    image_alt = db.Column(db.String(300))
    gallery = db.Column(db.JSON, default=list)

    # Visitor information. Unknown values stay NULL / blank on purpose:
    # the product must never invent fees, hours or seasons.
    entry_fee_indian = db.Column(db.String(120))
    entry_fee_foreign = db.Column(db.String(120))
    opening_info = db.Column(db.String(200))
    closed_day = db.Column(db.String(120))
    best_season = db.Column(db.String(160))
    typical_visit_hours = db.Column(db.Float)
    facilities = db.Column(db.String(300))
    accessibility_info = db.Column(db.String(300))
    safety_notes = db.Column(db.String(300))
    contact_info = db.Column(db.String(200))

    extra_tags = db.Column(db.String(200))  # comma separated secondary interests
    popularity = db.Column(db.Integer, nullable=False, default=0)

    is_published = db.Column(db.Boolean, nullable=False, default=False)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    verified_by = db.Column(db.String(160))
    last_verified_at = db.Column(db.Date)
    verification_notes = db.Column(db.Text)
    source_note = db.Column(db.Text)

    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    category = db.relationship("Category", back_populates="places")
    district = db.relationship("District", back_populates="places")
    stops = db.relationship("ItineraryStop", back_populates="place", lazy="dynamic")

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<Place {self.slug}>"

    # -- convenience helpers -------------------------------------------------
    @property
    def district_name(self) -> str | None:
        return self.district.name if self.district else None

    @property
    def category_name(self) -> str | None:
        return self.category.name if self.category else None

    @property
    def has_coordinates(self) -> bool:
        """True when the record has coordinates inside the valid range."""
        if self.latitude is None or self.longitude is None:
            return False
        return -90 <= self.latitude <= 90 and -180 <= self.longitude <= 180

    @property
    def has_tripura_coordinates(self) -> bool:
        """True only when both coordinates fall inside the Tripura navigation bounds."""
        return bool(
            self.has_coordinates
            and 22.9 <= self.latitude <= 24.6
            and 91.0 <= self.longitude <= 92.4
        )

    @property
    def map_ready(self) -> bool:
        return bool(self.is_published and self.has_coordinates)

    @property
    def tag_list(self) -> list[str]:
        tags = [self.category_name] if self.category_name else []
        if self.extra_tags:
            tags.extend(part.strip() for part in self.extra_tags.split(",") if part.strip())
        seen: list[str] = []
        for tag in tags:
            if tag and tag not in seen:
                seen.append(tag)
        return seen

    def get_google_maps_url(self, origin_lat: float | None = None, origin_lng: float | None = None) -> str | None:
        """Build a directions URL to the verified destination coordinates."""
        if not self.has_tripura_coordinates:
            return None

        url = f"https://www.google.com/maps/dir/?api=1&destination={self.latitude:.5f},{self.longitude:.5f}"
        if (
            origin_lat is not None
            and origin_lng is not None
            and -90 <= origin_lat <= 90
            and -180 <= origin_lng <= 180
        ):
            url += f"&origin={origin_lat:.5f},{origin_lng:.5f}"
        url += "&travelmode=driving"
        return url

    @property
    def directions_url(self) -> str | None:
        """External navigation link to this place's stored GIS destination."""
        return self.get_google_maps_url()

    def to_dict(self, include_admin_fields: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "tagline": self.tagline,
            "short_description": self.short_description,
            "category": self.category_name,
            "category_slug": self.category.slug if self.category else None,
            "district": self.district_name,
            "locality": self.locality,
            "address": self.address,
            "plus_code": self.plus_code,
            "image_url": self.image_url,
            "image_alt": self.image_alt,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "coordinates_verified": self.coordinates_verified,
            "is_verified": self.is_verified,
            "opening_info": self.opening_info,
            "closed_day": self.closed_day,
            "typical_visit_hours": self.typical_visit_hours,
            "entry_fee_indian": self.entry_fee_indian,
            "entry_fee_foreign": self.entry_fee_foreign,
            "directions_url": self.directions_url,
            "url": f"/places/{self.slug}",
        }
        if include_admin_fields:
            data.update(
                {
                    "is_published": self.is_published,
                    "popularity": self.popularity,
                    "last_verified_at": self.last_verified_at.isoformat() if self.last_verified_at else None,
                    "verification_notes": self.verification_notes,
                    "source_note": self.source_note,
                }
            )
        return data

    def to_map_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "category": self.category_name,
            "district": self.district_name,
            "lat": self.latitude,
            "lng": self.longitude,
            "plus_code": self.plus_code,
            "address": self.address,
            "coordinates_verified": self.coordinates_verified,
            "directions_url": self.directions_url,
            "image_url": self.image_url,
            "url": f"/places/{self.slug}",
        }
