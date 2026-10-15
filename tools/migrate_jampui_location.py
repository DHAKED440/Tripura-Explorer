"""Update Jampui Hills canonical location record to Kanchanpur sub-division, North Tripura (23.9667675, 92.2751563).

Run once per database:
    python tools/migrate_jampui_location.py
"""
from __future__ import annotations

from pathlib import Path
import sys

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.extensions import db


JAMPUI = {
    "locality": "Vanghmun, Kanchanpur",
    "address": "Kanchanpur Sub-Division, North Tripura, Tripura 799269, India",
    "plus_code": "X78G+P3",
    "latitude": 23.9667675,
    "longitude": 92.2751563,
    "description": (
        "The Jampui Hills form the highest hill range in Tripura, located in the Kanchanpur sub-division "
        "of North Tripura district right along the border with Mizoram. "
        "Villages such as Vanghmun are known for orange orchards and scenic viewpoints over the valleys, "
        "and the area is a base for short treks and the annual Orange Festival in November and December."
    ),
    "coordinate_source": "GPS Verified along Mizoram border in Kanchanpur sub-division",
    "verification_notes": (
        "Kanchanpur sub-division, North Tripura district along the Mizoram border (23.96677, 92.27516, Plus Code X78G+P3). "
        "Directions route directly to Jampui Hills scenic range."
    ),
    "source_note": "Official Tripura Tourism destination record for Jampui Hills, Kanchanpur sub-division, North Tripura.",
}


def main() -> None:
    app = create_app()
    with app.app_context():
        with db.engine.begin() as connection:
            result = connection.execute(
                text(
                    "UPDATE places SET "
                    "locality=:locality, "
                    "address=:address, "
                    "plus_code=:plus_code, "
                    "latitude=:latitude, "
                    "longitude=:longitude, "
                    "description=:description, "
                    "coordinate_source=:coordinate_source, "
                    "verification_notes=:verification_notes, "
                    "source_note=:source_note "
                    "WHERE slug=:slug"
                ),
                {**JAMPUI, "slug": "jampui-hills"},
            )
            if result.rowcount != 1:
                raise RuntimeError(
                    "Expected exactly one Jampui Hills place record; "
                    f"updated {result.rowcount} rows."
                )

    print("Updated Jampui Hills location:")
    print(f"latitude={JAMPUI['latitude']}, longitude={JAMPUI['longitude']}")
    print(f"locality={JAMPUI['locality']}, address={JAMPUI['address']}")
    print(f"plus_code={JAMPUI['plus_code']}")


if __name__ == "__main__":
    main()
