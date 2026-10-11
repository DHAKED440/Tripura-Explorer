"""User accounts and favourites."""
from __future__ import annotations

from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    favorites = db.relationship(
        "Favorite", back_populates="user", cascade="all, delete-orphan", lazy="dynamic"
    )
    itineraries = db.relationship(
        "Itinerary", back_populates="owner", cascade="all, delete-orphan", lazy="dynamic"
    )

    # -- password handling ---------------------------------------------------
    def set_password(self, password: str) -> None:
        """Store a salted hash - plain text passwords are never kept."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def first_name(self) -> str:
        return (self.name or "").split(" ")[0]

    def favorite_place_ids(self) -> set[int]:
        return {fav.place_id for fav in self.favorites}

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<User {self.email}>"


class Favorite(db.Model):
    __tablename__ = "favorites"
    __table_args__ = (db.UniqueConstraint("user_id", "place_id", name="uq_favorites_user_place"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    place_id = db.Column(db.Integer, db.ForeignKey("places.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    user = db.relationship("User", back_populates="favorites")
    place = db.relationship("Place")

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<Favorite user={self.user_id} place={self.place_id}>"