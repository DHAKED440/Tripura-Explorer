"""Destination categories (Nature, Heritage, Temples, ...)."""
from app.extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    icon = db.Column(db.String(40))  # name of an inline SVG icon used by the UI

    places = db.relationship("Place", back_populates="category", lazy="dynamic")

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<Category {self.name}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "icon": self.icon,
        }