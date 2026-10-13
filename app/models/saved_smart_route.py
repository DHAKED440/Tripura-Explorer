"""Saved smart route model for persisting and reopening mathematical routes."""
from __future__ import annotations

import secrets
from datetime import datetime, timezone

from app.extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SavedSmartRoute(db.Model):
    __tablename__ = "saved_smart_routes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    title = db.Column(db.String(180), nullable=False)
    start_place_id = db.Column(db.Integer, db.ForeignKey("places.id", ondelete="SET NULL"), nullable=True)
    end_place_id = db.Column(db.Integer, db.ForeignKey("places.id", ondelete="SET NULL"), nullable=True)
    is_round_trip = db.Column(db.Boolean, nullable=False, default=False)

    selected_destination_ids = db.Column(db.JSON, nullable=False, default=list)
    optimization_objective = db.Column(db.String(32), nullable=False, default="time")  # time, distance, cost, balanced
    algorithm_used = db.Column(db.String(64), nullable=False, default="dijkstra")
    algorithm_guarantee = db.Column(db.String(64), nullable=False, default="exact_shortest_path")

    total_distance_km = db.Column(db.Float, nullable=False, default=0.0)
    total_time_minutes = db.Column(db.Float, nullable=False, default=0.0)
    total_estimated_cost = db.Column(db.Float, nullable=True)

    ordered_stops_json = db.Column(db.JSON, nullable=False, default=list)
    legs_json = db.Column(db.JSON, nullable=False, default=list)
    preferences_json = db.Column(db.JSON, nullable=False, default=dict)
    summary_notes = db.Column(db.Text, nullable=True)
    share_token = db.Column(db.String(64), unique=True, index=True, nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    # Relationships
    user = db.relationship("User", backref=db.backref("saved_smart_routes", lazy="dynamic"))
    start_place = db.relationship("Place", foreign_keys=[start_place_id])
    end_place = db.relationship("Place", foreign_keys=[end_place_id])

    def __init__(self, **kwargs):
        if "share_token" not in kwargs or not kwargs["share_token"]:
            kwargs["share_token"] = secrets.token_urlsafe(20)
        super().__init__(**kwargs)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "user_id": self.user_id,
            "start_place_id": self.start_place_id,
            "end_place_id": self.end_place_id,
            "is_round_trip": self.is_round_trip,
            "selected_destination_ids": self.selected_destination_ids,
            "optimization_objective": self.optimization_objective,
            "algorithm_used": self.algorithm_used,
            "algorithm_guarantee": self.algorithm_guarantee,
            "total_distance_km": round(self.total_distance_km, 2),
            "total_time_minutes": round(self.total_time_minutes, 1),
            "total_estimated_cost": round(self.total_estimated_cost, 2) if self.total_estimated_cost is not None else None,
            "ordered_stops": self.ordered_stops_json,
            "ordered_stop_ids": [
                s.get("id") if isinstance(s, dict) else s
                for s in (self.ordered_stops_json or [])
            ],
            "legs": self.legs_json,
            "preferences": self.preferences_json,
            "summary_notes": self.summary_notes,
            "share_token": self.share_token,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<SavedSmartRoute {self.id} {self.title!r} ({self.algorithm_used})>"
