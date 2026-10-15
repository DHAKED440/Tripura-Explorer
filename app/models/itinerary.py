"""Saved trips and their day-wise stops."""
from __future__ import annotations

import secrets
from collections import OrderedDict
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, UniqueConstraint

from app.extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Itinerary(db.Model):
    __tablename__ = "itineraries"
    __table_args__ = (
        CheckConstraint("duration_days >= 1 AND duration_days <= 3", name="ck_itineraries_duration"),
        CheckConstraint("budget IS NULL OR budget >= 0", name="ck_itineraries_budget"),
    )

    id = db.Column(db.Integer, primary_key=True)
    # Guest itineraries are generated in memory only; a persisted trip always
    # belongs to a signed-in user. Ownership is checked on every request.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    title = db.Column(db.String(160), nullable=False)
    duration_days = db.Column(db.Integer, nullable=False, default=1)
    starting_location = db.Column(db.String(160), nullable=False)
    budget = db.Column(db.Integer)
    interests = db.Column(db.String(300), nullable=False, default="")
    travel_date = db.Column(db.Date)
    share_token = db.Column(db.String(64), unique=True, index=True)
    is_shared = db.Column(db.Boolean, nullable=False, default=False)
    generation_notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    owner = db.relationship("User", back_populates="itineraries")
    stops = db.relationship(
        "ItineraryStop",
        back_populates="itinerary",
        cascade="all, delete-orphan",
        order_by="ItineraryStop.day_number, ItineraryStop.stop_order",
    )

    # -- interests -----------------------------------------------------------
    @property
    def interests_list(self) -> list[str]:
        return [part.strip() for part in (self.interests or "").split(",") if part.strip()]

    def set_interests(self, interests) -> None:
        if isinstance(interests, str):
            interests = [part.strip() for part in interests.split(",") if part.strip()]
        cleaned: list[str] = []
        for interest in interests or []:
            text = str(interest).strip()
            if text and text not in cleaned:
                cleaned.append(text)
        self.interests = ",".join(cleaned)

    # -- stops ---------------------------------------------------------------
    def stops_by_day(self) -> "OrderedDict[int, list[ItineraryStop]]":
        """Group stops by day number, keeping the deterministic stop order."""
        grouped: "OrderedDict[int, list[ItineraryStop]]" = OrderedDict()
        for day in range(1, (self.duration_days or 1) + 1):
            grouped[day] = []
        for stop in sorted(self.stops, key=lambda s: (s.day_number, s.stop_order)):
            grouped.setdefault(stop.day_number, []).append(stop)
        return grouped

    def normalise_stops(self) -> None:
        """Re-number ``stop_order`` inside each day so ordering stays valid."""
        grouped = self.stops_by_day()
        for day, stops in grouped.items():
            for index, stop in enumerate(stops, start=1):
                stop.stop_order = index

    def reorder_day(self, day_number: int, ordered_stop_ids: list[int]) -> None:
        """Apply a new order for one day of the itinerary."""
        stops = {stop.id: stop for stop in self.stops if stop.day_number == day_number}
        allowed = set(stops)
        position = 1
        for stop_id in ordered_stop_ids:
            if stop_id in allowed and stops[stop_id].stop_order != position:
                stops[stop_id].stop_order = position
            position += 1

    def ensure_share_token(self) -> str:
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(24)
        return self.share_token

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "duration_days": self.duration_days,
            "starting_location": self.starting_location,
            "budget": self.budget,
            "interests": self.interests_list,
            "travel_date": self.travel_date.isoformat() if self.travel_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "generation_notes": self.generation_notes,
            "days": [
                {
                    "day": day,
                    "stops": [stop.to_dict() for stop in stops],
                }
                for day, stops in self.stops_by_day().items()
            ],
        }

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<Itinerary {self.id} {self.title!r}>"


class ItineraryStop(db.Model):
    __tablename__ = "itinerary_stops"
    __table_args__ = (
        # A stop cannot appear twice in the same trip. The day/order pair is
        # re-numbered by Itinerary.normalise_stops() instead of being locked by a
        # unique index, because re-ordering inside a day would violate it.
        UniqueConstraint("itinerary_id", "place_id", name="uq_stops_itinerary_place"),
        CheckConstraint("day_number >= 1 AND day_number <= 3", name="ck_stops_day"),
        CheckConstraint("stop_order >= 1", name="ck_stops_order"),
    )

    id = db.Column(db.Integer, primary_key=True)
    itinerary_id = db.Column(
        db.Integer, db.ForeignKey("itineraries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    place_id = db.Column(db.Integer, db.ForeignKey("places.id"), nullable=False, index=True)

    day_number = db.Column(db.Integer, nullable=False, default=1)
    stop_order = db.Column(db.Integer, nullable=False, default=1)
    planned_time = db.Column(db.String(40))
    notes = db.Column(db.String(300))

    itinerary = db.relationship("Itinerary", back_populates="stops")
    place = db.relationship("Place", back_populates="stops")

    def to_dict(self) -> dict:
        place = self.place
        return {
            "id": self.id,
            "place_id": self.place_id,
            "day_number": self.day_number,
            "stop_order": self.stop_order,
            "planned_time": self.planned_time,
            "notes": self.notes,
            "place": {
                "name": place.name,
                "slug": place.slug,
                "url": f"/places/{place.slug}",
                "image_url": place.image_url,
                "category": place.category_name,
                "district": place.district_name,
                "locality": place.locality,
                "address": place.address,
                "plus_code": place.plus_code,
                "latitude": place.latitude,
                "longitude": place.longitude,
                "has_coordinates": place.has_coordinates,
                "coordinates_verified": place.coordinates_verified,
                "directions_url": place.directions_url,
            }
            if place
            else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<ItineraryStop day={self.day_number} order={self.stop_order}>"
