"""Tripura districts used by the category/district filters.

Tripura has eight districts: West Tripura, Sepahijala, Khowai, Gomati,
South Tripura, Dhalai, Unakoti and North Tripura.
"""
from app.extensions import db


class District(db.Model):
    __tablename__ = "districts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)

    places = db.relationship("Place", back_populates="district", lazy="dynamic")

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<District {self.name}>"

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "slug": self.slug}