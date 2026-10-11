"""User submitted correction reports reviewed by administrators."""
from __future__ import annotations

from datetime import datetime, timezone

from app.extensions import db

CORRECTION_STATUSES = ["new", "reviewing", "resolved", "rejected"]


def utcnow() -> datetime:
    """Timezone aware ``now`` used by the default timestamp columns."""
    return datetime.now(timezone.utc)


class CorrectionReport(db.Model):
    __tablename__ = "correction_reports"

    id = db.Column(db.Integer, primary_key=True)
    place_id = db.Column(db.Integer, db.ForeignKey("places.id"), nullable=False, index=True)

    message = db.Column(db.Text, nullable=False)
    reporter_email = db.Column(db.String(180))
    status = db.Column(db.String(20), nullable=False, default="new", index=True)
    admin_note = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    place = db.relationship("Place")

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<CorrectionReport {self.id} place={self.place_id}>"