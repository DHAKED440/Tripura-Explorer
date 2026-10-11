"""Generate the placeholder illustrations used by the prototype.

The prototype ships with generated SVG artwork instead of photographs so that
no unlicensed image is ever used. Run this script again after adding a
destination to the seed data:

    python tools/generate_place_images.py

Every file it writes lives in app/static/images/ and is referenced by
Place.image_url. Replace them with licensed photographs (keeping the alt text
and credit fields) before launch.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.seed_data import BUSINESSES, PLACES  # noqa: E402  (path set above)

IMAGES_DIR = BASE_DIR / "app" / "static" / "images"
PLACES_DIR = IMAGES_DIR / "places"
BUSINESS_DIR = PLACES_DIR / "businesses"

PALETTES = {
    "heritage": ("#17365D", "#2E5F92", "#F7F5F0", "#B08D57"),
    "temples": ("#1E4A7B", "#17365D", "#F7F5F0", "#C39A5F"),
    "hills": ("#17365D", "#3C6E9B", "#EFEDE6", "#8FB0C9"),
    "lakes": ("#12304F", "#2C6690", "#F3F1EA", "#9CC3D8"),
    "wildlife": ("#1B3B31", "#2F6152", "#F2F1EA", "#B08D57"),
    "nature": ("#1B3B31", "#2F6152", "#F2F1EA", "#C0A16B"),
    "culture": ("#17365D", "#4A6C9B", "#F7F5F0", "#B08D57"),
}

WIDTH, HEIGHT = 900, 675


def _seed(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)


def _hill(path_id: str, y: int, height: int, fill: str, skew: int) -> str:
    return (
        f'<path d="M0 {y + 60} Q {WIDTH // 4 + skew} {y - height} {WIDTH // 2} {y} '
        f'T {WIDTH} {y + 40} L {WIDTH} {HEIGHT} L 0 {HEIGHT} Z" fill="{fill}" opacity="0.95"/>'
    )


def _sky(primary: str, secondary: str) -> str:
    return (
        f'<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{primary}"/><stop offset="100%" stop-color="{secondary}"/>'
        f"</linearGradient></defs>"
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#sky)"/>'
    )


def _palace(accent: str, ivory: str) -> str:
    return (
        f'<g transform="translate({WIDTH // 2 - 170}, {HEIGHT - 300})">'
        f'<rect x="0" y="120" width="340" height="180" fill="{ivory}" opacity="0.94"/>'
        f'<rect x="120" y="40" width="100" height="90" fill="{ivory}" opacity="0.9"/>'
        f'<path d="M110 40 Q170 -30 230 40 Z" fill="{accent}"/>'
        f'<rect x="30" y="40" width="60" height="90" fill="{ivory}" opacity="0.85"/>'
        f'<rect x="250" y="40" width="60" height="90" fill="{ivory}" opacity="0.85"/>'
        f'<rect x="155" y="160" width="30" height="140" fill="{accent}" opacity="0.85"/>'
        f'<rect x="60" y="170" width="34" height="60" fill="{accent}" opacity="0.55"/>'
        f'<rect x="246" y="170" width="34" height="60" fill="{accent}" opacity="0.55"/>'
        f"</g>"
    )


def _temple(accent: str, ivory: str) -> str:
    return (
        f'<g transform="translate({WIDTH // 2 - 120}, {HEIGHT - 300})">'
        f'<rect x="0" y="150" width="240" height="150" fill="{ivory}" opacity="0.94"/>'
        f'<path d="M40 150 L120 20 L200 150 Z" fill="{ivory}" opacity="0.9"/>'
        f'<rect x="104" y="185" width="32" height="115" fill="{accent}" opacity="0.8"/>'
        f'<circle cx="120" cy="4" r="12" fill="{accent}"/>'
        f'<rect x="-20" y="260" width="280" height="18" fill="{accent}" opacity="0.5"/>'
        f"</g>"
    )


def _water(accent: str) -> str:
    return (
        f'<rect y="{HEIGHT - 200}" width="{WIDTH}" height="200" fill="{accent}" opacity="0.55"/>'
        f'<path d="M60 {HEIGHT - 120} q 60 -18 120 0 t 120 0 t 120 0 t 120 0 t 120 0" '
        f'stroke="#FFFFFF" stroke-opacity="0.35" stroke-width="4" fill="none"/>'
    )


def _trees(accent: str, count: int = 6) -> str:
    shapes = []
    for index in range(count):
        x = 70 + index * (WIDTH - 140) / max(1, count - 1)
        scale = 0.7 + (index % 3) * 0.15
        shapes.append(
            f'<g transform="translate({x:.0f}, {HEIGHT - 190}) scale({scale:.2f})">'
            f'<rect x="-6" y="0" width="12" height="70" fill="#0F2733" opacity="0.5"/>'
            f'<circle cx="0" cy="-10" r="44" fill="{accent}" opacity="0.75"/>'
            f"</g>"
        )
    return "".join(shapes)


def _birds() -> str:
    return (
        f'<g stroke="#FFFFFF" stroke-opacity="0.5" stroke-width="3" fill="none">'
        f'<path d="M120 120 q 14 -12 28 0 q 14 -12 28 0"/>'
        f'<path d="M640 90 q 12 -10 24 0 q 12 -10 24 0"/>'
        f"</g>"
    )


def scene(category: str, label: str, variant: int = 0) -> str:
    primary, secondary, ivory, accent = PALETTES.get(category, PALETTES["heritage"])
    token = _seed(label + str(variant))
    skew = (token % 120) - 60

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img">']
    parts.append(_sky(primary, secondary))

    if category == "hills":
        parts.append(_hill("a", HEIGHT - 300, 150, secondary, skew))
        parts.append(_hill("b", HEIGHT - 210, 110, primary, -skew))
    elif category in {"lakes"}:
        parts.append(_hill("a", HEIGHT - 330, 90, secondary, skew))
        parts.append(_water(accent))
        parts.append(_palace(accent, ivory))
        parts.append(
            f'<path d="M120 {HEIGHT - 130} q 70 34 140 0 l 18 26 h -176 Z" fill="{ivory}" opacity="0.85"/>'
        )
    elif category in {"wildlife", "nature"}:
        parts.append(_hill("a", HEIGHT - 280, 120, secondary, skew))
        parts.append(_trees(accent))
    elif category == "temples":
        parts.append(_hill("a", HEIGHT - 300, 100, secondary, skew))
        parts.append(_temple(accent, ivory))
    elif category == "culture":
        parts.append(_hill("a", HEIGHT - 300, 110, secondary, skew))
        parts.append(
            f'<g transform="translate({WIDTH // 2 - 90}, {HEIGHT - 320})">'
            f'<rect x="0" y="60" width="180" height="220" fill="{ivory}" opacity="0.92"/>'
            f'<path d="M-30 60 L90 -30 L210 60 Z" fill="{accent}" opacity="0.85"/>'
            f'<rect x="30" y="120" width="40" height="70" fill="{primary}" opacity="0.35"/>'
            f'<rect x="110" y="120" width="40" height="70" fill="{primary}" opacity="0.35"/>'
            f"</g>"
        )
    else:  # heritage
        parts.append(_hill("a", HEIGHT - 310, 110, secondary, skew))
        parts.append(_palace(accent, ivory))

    if variant:
        parts.append(
            f'<circle cx="{180 + (token % 500)}" cy="{140 + (token % 90)}" r="46" fill="#FFFFFF" opacity="0.12"/>'
        )
    parts.append(_birds())
    parts.append(
        f'<rect x="0" y="{HEIGHT - 46}" width="{WIDTH}" height="46" fill="#0C2138" opacity="0.55"/>'
        f'<text x="34" y="{HEIGHT - 16}" font-family="Georgia, serif" font-size="26" fill="#F7F5F0">'
        f"{label}</text>"
    )
    parts.append("</svg>")
    return "".join(parts)


def hero() -> str:
    primary, secondary, ivory, accent = PALETTES["heritage"]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 900" role="img">']
    parts.append(
        '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#102943"/><stop offset="55%" stop-color="#22466F"/>'
        '<stop offset="100%" stop-color="#3A6B95"/></linearGradient></defs>'
    )
    parts.append('<rect width="1200" height="900" fill="url(#sky)"/>')
    parts.append('<circle cx="930" cy="170" r="70" fill="#F7F5F0" opacity="0.85"/>')
    parts.append('<path d="M0 560 Q 250 430 520 560 T 1200 520 L 1200 900 L 0 900 Z" fill="#1B3B31" opacity="0.85"/>')
    parts.append('<path d="M0 620 Q 320 520 640 620 T 1200 600 L 1200 900 L 0 900 Z" fill="#17365D"/>')
    parts.append('<rect y="700" width="1200" height="200" fill="#12304F" opacity="0.75"/>')
    parts.append(
        '<g transform="translate(360, 430)">'
        f'<rect x="0" y="90" width="470" height="180" fill="{ivory}" opacity="0.95"/>'
        f'<rect x="170" y="10" width="130" height="80" fill="{ivory}" opacity="0.92"/>'
        f'<path d="M155 10 Q235 -70 315 10 Z" fill="{accent}"/>'
        f'<rect x="40" y="30" width="70" height="60" fill="{ivory}" opacity="0.86"/>'
        f'<rect x="360" y="30" width="70" height="60" fill="{ivory}" opacity="0.86"/>'
        f'<rect x="215" y="150" width="40" height="120" fill="{accent}" opacity="0.8"/>'
        "</g>"
    )
    parts.append('<path d="M250 760 q 90 40 180 0 l 22 30 h -224 Z" fill="#F7F5F0" opacity="0.9"/>')
    parts.append('<path d="M760 790 q 70 30 140 0 l 18 26 h -176 Z" fill="#F7F5F0" opacity="0.75"/>')
    parts.append(_birds().replace("#FFFFFF", "#F7F5F0"))
    parts.append("</svg>")
    return "".join(parts)


def map_preview() -> str:
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 700" role="img">']
    parts.append('<rect width="1000" height="700" fill="#EFEDE6"/>')
    parts.append('<path d="M120 60 L880 120 L930 600 L80 660 Z" fill="#E4E7E2" stroke="#C9CFC7" stroke-width="3"/>')
    parts.append('<g fill="#DFE7EE" stroke="#B9CBD9" stroke-width="2">')
    parts.append('<ellipse cx="330" cy="300" rx="110" ry="70"/>')
    parts.append('<ellipse cx="660" cy="470" rx="90" ry="55"/>')
    parts.append("</g>")
    parts.append('<g stroke="#D8D3C4" stroke-width="6" fill="none">')
    parts.append('<path d="M150 520 Q 400 380 830 180"/>')
    parts.append('<path d="M220 160 Q 480 330 700 640"/>')
    parts.append("</g>")
    pins = [(250, 230), (420, 330), (600, 250), (720, 420), (330, 520), (540, 560)]
    for index, (x, y) in enumerate(pins, start=1):
        fill = "#17365D" if index % 3 else "#8A6A48"
        parts.append(f'<circle cx="{x}" cy="{y}" r="14" fill="{fill}"/>')
        parts.append(
            f'<text x="{x}" y="{y + 5}" text-anchor="middle" font-family="Segoe UI, sans-serif" '
            f'font-size="13" fill="#FFFFFF">{index}</text>'
        )
    parts.append(
        '<text x="40" y="660" font-family="Georgia, serif" font-size="26" fill="#17365D">'
        "Tripura — destination map preview</text>"
    )
    parts.append("</svg>")
    return "".join(parts)


def placeholder() -> str:
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 675" role="img">']
    parts.append('<rect width="900" height="675" fill="#EFEDE6"/>')
    parts.append('<circle cx="450" cy="300" r="150" fill="#DDE3E8"/>')
    parts.append(_temple("#B08D57", "#F7F5F0").replace(str(WIDTH), "900"))
    parts.append(
        '<text x="450" y="600" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="24" fill="#6B7280">'
        "Placeholder illustration — photograph pending</text>"
    )
    parts.append("</svg>")
    return "".join(parts)


def favicon() -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<rect width="64" height="64" rx="16" fill="#17365D"/>'
        '<path d="M12 44 L26 24 L38 40 L46 28 L54 44 Z" fill="#F7F5F0"/>'
        '<circle cx="44" cy="18" r="6" fill="#B08D57"/>'
        "</svg>"
    )


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    write(IMAGES_DIR / "hero-tripura.svg", hero())
    write(IMAGES_DIR / "map-preview.svg", map_preview())
    write(IMAGES_DIR / "place-placeholder.svg", placeholder())
    write(IMAGES_DIR / "favicon.svg", favicon())

    for place in PLACES:
        slug = place["slug"]
        category = place["category"]
        write(PLACES_DIR / f"{slug}.svg", scene(category, place["name"]))
        write(PLACES_DIR / f"{slug}-view.svg", scene(category, place["name"], variant=1))

    for business in BUSINESSES:
        label = business["name"]
        write(BUSINESS_DIR / f"{business['slug']}.svg", scene("culture", label))

    print(f"Wrote {4 + len(PLACES) * 2 + len(BUSINESSES)} SVG files into {IMAGES_DIR}")


if __name__ == "__main__":
    main()