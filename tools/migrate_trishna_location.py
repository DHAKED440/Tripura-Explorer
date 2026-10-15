"""Add the Plus Code field and repair Trishna's canonical location record.

Run once per database after deploying the Place.plus_code model change:
    python tools/migrate_trishna_location.py
"""
from __future__ import annotations

from pathlib import Path
import sys

from sqlalchemy import inspect, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.extensions import db


TRISHNA = {
    "plus_code": "7CH2+PFW",
    "address": "7CH2+PFW, Belonia - Bhabanipur Rd, Rajnagar, Joychandrapur, Tripura 799150",
    "latitude": 23.2793625,
    "longitude": 91.401203125,
    "coordinate_source": "User-provided Plus Code 7CH2+PFW, decoded with openlocationcode 1.0.1; verify on Google Maps",
    "verification_notes": (
        "Short Plus Code recovered using the OpenStreetMap Belonia town point "
        "(23.2497879, 91.4550309) and decoded to its cell center. Confirm the destination pin "
        "on Google Maps before marking verified."
    ),
    "source_note": "Sanctuary location supplied by the project owner as Plus Code and full address.",
}


def main() -> None:
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        if "plus_code" not in {column["name"] for column in inspector.get_columns("places")}:
            with db.engine.begin() as connection:
                connection.execute(text("ALTER TABLE places ADD COLUMN plus_code VARCHAR(32)"))

        with db.engine.begin() as connection:
            result = connection.execute(
                text(
                    "UPDATE places SET plus_code=:plus_code, address=:address, "
                    "latitude=:latitude, longitude=:longitude, coordinates_verified=:verified, "
                    "coordinate_source=:coordinate_source, verification_notes=:verification_notes, "
                    "source_note=:source_note WHERE slug=:slug"
                ),
                {**TRISHNA, "verified": False, "slug": "trishna-wildlife-sanctuary"},
            )
            if result.rowcount != 1:
                raise RuntimeError(
                    "Expected exactly one Trishna Wildlife Sanctuary place record; "
                    f"updated {result.rowcount} rows."
                )

    print("Updated Trishna Wildlife Sanctuary coordinates (verify on Google Maps):")
    print(f"latitude={TRISHNA['latitude']}, longitude={TRISHNA['longitude']}")


if __name__ == "__main__":
    main()
