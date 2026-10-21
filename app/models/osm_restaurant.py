"""Restaurant listings discovered from OpenStreetMap.

This provider-owned inventory is separate from the curated ``Place`` records
and user-submitted ``Business`` directory. Values remain nullable because OSM
contributors do not record every field for every restaurant.
"""
from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlencode

from sqlalchemy import CheckConstraint, UniqueConstraint

from app.extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OSMRestaurant(db.Model):
    __tablename__ = "osm_restaurants"
    __table_args__ = (
        UniqueConstraint("osm_type", "osm_id", name="uq_osm_restaurants_element"),
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_osm_restaurants_latitude"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_osm_restaurants_longitude"),
    )

    id = db.Column(db.Integer, primary_key=True)
    osm_type = db.Column(db.String(12), nullable=False)
    osm_id = db.Column(db.String(32), nullable=False)
    name = db.Column(db.String(180), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(500))
    description = db.Column(db.Text)
    cuisine = db.Column(db.String(300))
    opening_hours = db.Column(db.String(500))
    phone = db.Column(db.String(100))
    email = db.Column(db.String(200))
    website = db.Column(db.String(500))
    operator = db.Column(db.String(240))
    brand = db.Column(db.String(240))
    takeaway = db.Column(db.String(80))
    delivery = db.Column(db.String(80))
    dine_in = db.Column(db.String(80))
    wheelchair = db.Column(db.String(80))
    image_url = db.Column(db.String(1000))
    raw_tags = db.Column(db.JSON, nullable=False, default=dict)
    source_url = db.Column(db.String(500), nullable=False)
    source_attribution = db.Column(db.String(160), nullable=False, default="© OpenStreetMap contributors")
    first_seen_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    last_synced_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)

    def to_dict(self, origin_lat: float | None = None, origin_lon: float | None = None) -> dict:
        from app.services.local_experience_search import haversine_km

        distance = None
        if origin_lat is not None and origin_lon is not None:
            distance = round(haversine_km(origin_lat, origin_lon, self.latitude, self.longitude), 1)
        direction_query = urlencode({
            "lat": f"{self.latitude:.7f}", "lng": f"{self.longitude:.7f}",
            "name": self.name, "osm_type": self.osm_type,
            "osm_id": self.osm_id, "directions": "1",
        })
        return {
            "id": f"{self.osm_type}/{self.osm_id}",
            "osm_type": self.osm_type,
            "osm_id": int(self.osm_id),
            "name": self.name,
            "category": "Food & Restaurants",
            "latitude": self.latitude,
            "longitude": self.longitude,
            "distance_km": distance,
            "distance_type": "straight-line",
            "address": self.address,
            "description": self.description,
            "cuisine": self.cuisine,
            "opening_hours": self.opening_hours,
            "opening_status": None,
            "phone": self.phone,
            "email": self.email,
            "website": self.website,
            "operator": self.operator,
            "brand": self.brand,
            "takeaway": self.takeaway,
            "delivery": self.delivery,
            "dine_in": self.dine_in,
            "wheelchair": self.wheelchair,
            "photo": self.image_url,
            "rating": None,
            "review_count": None,
            "price": None,
            "raw_tags": self.raw_tags or {},
            "osm_url": self.source_url,
            "directions": f"/map?{direction_query}",
            "external_directions": f"https://www.google.com/maps/dir/?api=1&destination={self.latitude:.7f}%2C{self.longitude:.7f}",
            "icon_category": "food",
            "attribution": self.source_attribution,
        }
