"""Route connection model representing weighted graph edges between destinations.

An edge represents an actual or explicitly estimated travel corridor between
two tourist places. Connections can be bidirectional or directed, and store
measurable weights (distance, travel duration, estimated cost) along with
data source attribution and verification status.
"""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, Index, UniqueConstraint

from app.extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RouteConnection(db.Model):
    __tablename__ = "route_connections"
    __table_args__ = (
        CheckConstraint("distance_km >= 0", name="ck_route_conn_distance"),
        CheckConstraint("travel_time_minutes >= 0", name="ck_route_conn_time"),
        CheckConstraint("estimated_cost IS NULL OR estimated_cost >= 0", name="ck_route_conn_cost"),
        UniqueConstraint(
            "source_destination_id",
            "target_destination_id",
            "transport_mode",
            name="uq_route_conn_src_tgt_mode",
        ),
        Index("ix_route_conn_source", "source_destination_id"),
        Index("ix_route_conn_target", "target_destination_id"),
        Index("ix_route_conn_verification", "verification_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    source_destination_id = db.Column(
        db.Integer, db.ForeignKey("places.id", ondelete="CASCADE"), nullable=False
    )
    target_destination_id = db.Column(
        db.Integer, db.ForeignKey("places.id", ondelete="CASCADE"), nullable=False
    )

    is_directed = db.Column(db.Boolean, nullable=False, default=False)
    distance_km = db.Column(db.Float, nullable=False)
    travel_time_minutes = db.Column(db.Float, nullable=False)
    estimated_cost = db.Column(db.Float, nullable=True)

    transport_mode = db.Column(db.String(32), nullable=False, default="road")  # road, transit, walk, boat
    connection_type = db.Column(db.String(64), nullable=False, default="highway")  # highway, major_road, rural_road, scenic_route, ferry
    geometry_json = db.Column(db.JSON, nullable=True)

    data_source = db.Column(db.String(255), nullable=False, default="Tripura PWD & Highway Distance Tables")
    verification_status = db.Column(db.String(32), nullable=False, default="estimated")  # verified, estimated, illustrative
    accessibility_notes = db.Column(db.String(255), nullable=True)
    seasonal_notes = db.Column(db.String(255), nullable=True)

    valid_from = db.Column(db.Date, nullable=True)
    last_verified_at = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    # Relationships
    source_place = db.relationship("Place", foreign_keys=[source_destination_id], backref=db.backref("outgoing_connections", lazy="dynamic", cascade="all, delete-orphan"))
    target_place = db.relationship("Place", foreign_keys=[target_destination_id], backref=db.backref("incoming_connections", lazy="dynamic", cascade="all, delete-orphan"))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_destination_id": self.source_destination_id,
            "target_destination_id": self.target_destination_id,
            "source_name": self.source_place.name if self.source_place else None,
            "target_name": self.target_place.name if self.target_place else None,
            "is_directed": self.is_directed,
            "distance_km": round(self.distance_km, 2),
            "travel_time_minutes": round(self.travel_time_minutes, 1),
            "estimated_cost": round(self.estimated_cost, 2) if self.estimated_cost is not None else None,
            "transport_mode": self.transport_mode,
            "connection_type": self.connection_type,
            "data_source": self.data_source,
            "verification_status": self.verification_status,
            "accessibility_notes": self.accessibility_notes,
            "seasonal_notes": self.seasonal_notes,
            "last_verified_at": self.last_verified_at.isoformat() if self.last_verified_at else None,
        }

    def __repr__(self) -> str:
        arrow = "->" if self.is_directed else "<->"
        return f"<RouteConnection {self.source_destination_id} {arrow} {self.target_destination_id} ({self.distance_km}km)>"
