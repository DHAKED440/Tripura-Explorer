"""Audit published and draft destination coordinates in the app's database."""
from __future__ import annotations

import math
from itertools import combinations
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.extensions import db
from app.models import Place

LAT_MIN, LAT_MAX = 22.9, 24.6
LNG_MIN, LNG_MAX = 91.0, 92.4
NEAR_KM = 0.1


def distance_km(first: Place, second: Place) -> float:
    radius = 6371.0088
    lat1, lat2 = math.radians(first.latitude), math.radians(second.latitude)
    dlat = lat2 - lat1
    dlng = math.radians(second.longitude - first.longitude)
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(value))


def main() -> None:
    app = create_app()
    with app.app_context():
        places = Place.query.order_by(Place.name.asc(), Place.slug.asc()).all()
        pairs = []
        for first, second in combinations(places, 2):
            if None in (first.latitude, first.longitude, second.latitude, second.longitude):
                continue
            distance = distance_km(first, second)
            if distance <= NEAR_KM:
                pairs.append((first, second, distance))

        near_ids = {place.id for first, second, _ in pairs for place in (first, second)}
        print("name | latitude | longitude | outside_tripura | near_duplicate_within_100m")
        for place in places:
            lat, lng = place.latitude, place.longitude
            outside = lat is not None and lng is not None and not (
                LAT_MIN <= lat <= LAT_MAX and LNG_MIN <= lng <= LNG_MAX
            )
            near = place.id in near_ids
            lat_text = f"{lat:.7f}" if lat is not None else "MISSING"
            lng_text = f"{lng:.7f}" if lng is not None else "MISSING"
            print(f"{place.name} | {lat_text} | {lng_text} | {outside} | {near}")

        print("\nNEAR-DUPLICATE PAIRS (different destination records, <= 100 m):")
        if pairs:
            for first, second, distance in pairs:
                print(f"{first.name} [{first.slug}] <-> {second.name} [{second.slug}]: {distance * 1000:.1f} m")
        else:
            print("None")


if __name__ == "__main__":
    main()
