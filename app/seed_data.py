"""Repeatable development seed data.

Everything in this module is *prototype* data:

* destination names, districts and short descriptions are compiled from public
  reference material,
* coordinates are approximate and flagged as unverified,
* entry fees, opening hours and contact details are intentionally left blank
  until the managing authority confirms them (see docs/DATA-VERIFICATION.md),
* the local provider listings are clearly labelled demo records.

Running the seed command twice must not create duplicates - every record is
looked up by its slug first.
"""
from __future__ import annotations

from datetime import date

from app.extensions import db
from app.models import Business, Category, District, Place, User

IMAGE_BASE = "/static/images/places"

SOURCE_NOTE = (
    "Prototype seed record. Name, district and general description are compiled from public "
    "reference material. Coordinates are approximate and not yet field-verified. Entry fees, "
    "opening hours and the verifying officer still have to be confirmed with the managing authority."
)

CATEGORIES = [
    {
        "name": "Nature",
        "slug": "nature",
        "icon": "leaf",
        "description": "Forests, rivers, waterfalls and open landscapes.",
    },
    {
        "name": "Heritage",
        "slug": "heritage",
        "icon": "landmark",
        "description": "Palaces, rock carvings and archaeological sites.",
    },
    {
        "name": "Lakes",
        "slug": "lakes",
        "icon": "waves",
        "description": "Lakes and reservoirs, including Rudrasagar and Dumboor.",
    },
    {
        "name": "Hills",
        "slug": "hills",
        "icon": "mountain",
        "description": "Hill ranges and viewpoints, including Jampui Hills.",
    },
    {
        "name": "Temples",
        "slug": "temples",
        "icon": "temple",
        "description": "Temples and pilgrimage sites across the state.",
    },
    {
        "name": "Wildlife",
        "slug": "wildlife",
        "icon": "paw",
        "description": "Sanctuaries, zoological parks and protected forests.",
    },
    {
        "name": "Culture",
        "slug": "culture",
        "icon": "mask",
        "description": "Museums, parks and living cultural experiences.",
    },
]

DISTRICTS = [
    {"name": "West Tripura", "slug": "west-tripura", "description": "District that contains Agartala, the state capital."},
    {"name": "Sepahijala", "slug": "sepahijala", "description": "District in the west of Tripura, home to Neermahal and Sepahijala sanctuary."},
    {"name": "Khowai", "slug": "khowai", "description": "District in central Tripura. No destination has been verified here yet."},
    {"name": "Gomati", "slug": "gomati", "description": "District around Udaipur, Amarpur and the Gomti river."},
    {"name": "South Tripura", "slug": "south-tripura", "description": "Southern district with archaeological and wildlife sites."},
    {"name": "Dhalai", "slug": "dhalai", "description": "Largest district by area, contains Dumboor Lake."},
    {"name": "Unakoti", "slug": "unakoti", "description": "Northern district, home to the Unakoti rock-cut sculptures."},
    {"name": "North Tripura", "slug": "north-tripura", "description": "Northernmost district, contains the Jampui hill range."},
]

PLACES = [
    {
        "name": "Neermahal",
        "slug": "neermahal",
        "tagline": "A royal lake palace in the middle of Rudrasagar Lake",
        "short_description": "A water palace built in the middle of Rudrasagar Lake near Melaghar.",
        "description": (
            "Neermahal is a palace built in the middle of Rudrasagar Lake in the early 20th century "
            "as a summer residence of the Tripura royal family. Visitors reach it by boat from the "
            "Melaghar side; the building mixes Hindu and Islamic architectural styles and is best "
            "known for the annual boat race held on the lake."
        ),
        "category": "heritage",
        "district": "sepahijala",
        "locality": "Melaghar",
        "latitude": 23.4929,
        "longitude": 91.3145,
        "extra_tags": "Lakes,Culture",
        "popularity": 96,
        "facilities": "Boat jetty, ticket counter, parking and small eateries near the jetty.",
        "accessibility_info": "Boat access with steps; confirm current arrangements at the jetty.",
        "safety_notes": "Lake crossings depend on weather and water level - follow the boat operator's instructions.",
        "image_alt": "Illustration of a pale palace standing in the middle of a wide lake.",
    },
    {
        "name": "Unakoti",
        "slug": "unakoti",
        "tagline": "Ancient rock-cut reliefs among forested hills",
        "short_description": "A Shaiva pilgrimage site famous for its rock-cut sculptures and waterfalls.",
        "description": (
            "Unakoti is an ancient pilgrimage site in Unakoti district where large rock-cut reliefs "
            "of Hindu deities are carved into the hillside. The name is usually explained as 'one "
            "less than a crore'. A waterfall and forested slopes surround the carvings, and the site "
            "is busiest during the Ashokastami fair."
        ),
        "category": "heritage",
        "district": "unakoti",
        "locality": "Kailashahar",
        "latitude": 24.3222,
        "longitude": 91.7533,
        "extra_tags": "Temples,Nature",
        "popularity": 94,
        "facilities": "Ticket counter, pathways, drinking water points and parking.",
        "accessibility_info": "Sloping paths and steps across the site; limited access for wheelchairs.",
        "safety_notes": "Paths can be slippery during the monsoon - wear shoes with grip.",
        "image_alt": "Illustration of a large rock-cut deity carving on a wooded hillside.",
    },
    {
        "name": "Tripura Sundari Temple",
        "slug": "tripura-sundari-temple",
        "tagline": "One of the Shakti Peethas at Matabari",
        "short_description": "A 16th-century temple at Matabari near Udaipur, one of the Shakti Peethas.",
        "description": (
            "The Tripura Sundari temple at Matabari, near Udaipur, is one of the 51 Shakti Peethas "
            "and one of the most visited temples in the state. The present structure is associated "
            "with Maharaja Dhanya Manikya and stands beside Kalyan Sagar, a large tank where fish "
            "and tortoises are protected."
        ),
        "category": "temples",
        "district": "gomati",
        "locality": "Matabari, Udaipur",
        "latitude": 23.5047,
        "longitude": 91.4794,
        "extra_tags": "Heritage,Culture",
        "popularity": 93,
        "facilities": "Parking, shoe stand, prasad counters and drinking water.",
        "accessibility_info": "Level approach to the temple courtyard; the inner shrine area is crowded at peak times.",
        "safety_notes": "Dress respectfully and expect queues during festivals.",
        "image_alt": "Illustration of a temple with a stepped tank in front of it.",
    },
    {
        "name": "Ujjayanta Palace",
        "slug": "ujjayanta-palace",
        "tagline": "The former royal palace in Agartala",
        "short_description": "The royal palace of the Tripura kings in Agartala, now home to the State Museum.",
        "description": (
            "Ujjayanta Palace is the former residence of the Tripura royal family in the centre of "
            "Agartala, completed in the early 20th century. The palace now houses the Tripura State "
            "Museum, with galleries on archaeology, art and the history of the state, and is surrounded "
            "by gardens and fountains."
        ),
        "category": "heritage",
        "district": "west-tripura",
        "locality": "Agartala",
        "latitude": 23.8364,
        "longitude": 91.2775,
        "extra_tags": "Culture",
        "popularity": 92,
        "facilities": "Museum ticket counter, gardens, parking nearby.",
        "accessibility_info": "Ramped entrance to the museum; confirm lift access at the counter.",
        "safety_notes": "Photography rules inside the museum galleries vary - check at the entrance.",
        "image_alt": "Illustration of a domed white palace with gardens in front.",
    },
    {
        "name": "Jampui Hills",
        "slug": "jampui-hills",
        "tagline": "The highest hill range in Tripura",
        "short_description": "A hill range in North Tripura known for viewpoints, orange orchards and Mizo villages.",
        "description": (
            "The Jampui Hills form the highest hill range in Tripura, close to the Mizoram border. "
            "Villages such as Vanghmun are known for orange orchards and viewpoints over the valleys, "
            "and the area is a base for short treks and for the harvest season in November and December."
        ),
        "category": "hills",
        "district": "north-tripura",
        "locality": "Vanghmun",
        "latitude": 23.9950,
        "longitude": 92.2760,
        "extra_tags": "Nature,Culture",
        "popularity": 90,
        "facilities": "Guest houses and homestays in the villages; limited fuel and ATM access.",
        "accessibility_info": "Hill roads with bends; travelling with your own vehicle is recommended.",
        "safety_notes": "Roads can be affected by landslides in the monsoon - check conditions before travelling.",
        "image_alt": "Illustration of layered green hills with low clouds.",
    },
    {
        "name": "Dumboor Lake",
        "slug": "dumboor-lake",
        "tagline": "A lake shaped like a small drum",
        "short_description": "A large reservoir in Dhalai district with scattered islands and birdlife.",
        "description": (
            "Dumboor Lake is a reservoir in Dhalai district named after the 'dumboor', a small drum, "
            "because of its shape. It is fed by hill streams and is known for its islands and for "
            "migratory birds in winter. The lake is reached from Gandacherra."
        ),
        "category": "lakes",
        "district": "dhalai",
        "locality": "Gandacherra",
        "latitude": 23.8450,
        "longitude": 91.8250,
        "extra_tags": "Nature",
        "popularity": 87,
        "facilities": "Basic jetty and boat arrangements; very limited facilities nearby.",
        "accessibility_info": "Boat based access; not suitable for visitors with limited mobility.",
        "safety_notes": "Use licensed boats only and carry drinking water; mobile coverage is patchy.",
        "image_alt": "Illustration of a wide lake with small green islands.",
    },
    {
        "name": "Sepahijala Wildlife Sanctuary",
        "slug": "sepahijala-wildlife-sanctuary",
        "tagline": "Sanctuary, zoo and botanical garden",
        "short_description": "A wildlife sanctuary and zoological park about 25 km from Agartala.",
        "description": (
            "Sepahijala Wildlife Sanctuary near Bishalgarh protects a mix of forest, wetland and "
            "plantation, and includes a zoological park and a botanical garden. It is known for "
            "primate species, including a clouded leopard enclosure, and for birdwatching around "
            "the lake inside the sanctuary."
        ),
        "category": "wildlife",
        "district": "sepahijala",
        "locality": "Bishalgarh",
        "latitude": 23.6770,
        "longitude": 91.3220,
        "extra_tags": "Nature",
        "popularity": 85,
        "facilities": "Ticket counter, parking, drinking water and a canteen near the entrance.",
        "accessibility_info": "Main paths are level; some trails are earth tracks.",
        "safety_notes": "Do not feed animals and stay on marked paths.",
        "image_alt": "Illustration of a forest path with tall trees and a lake.",
    },
    {
        "name": "Chabimura (Debtamura)",
        "slug": "chabimura-debtamura",
        "tagline": "Rock carvings on a cliff above the Gomti river",
        "short_description": "Large rock-cut reliefs of Hindu deities on a cliff beside the Gomti river.",
        "description": (
            "Chabimura, also called Debtamura, is a cliff face beside the Gomti river in Gomati "
            "district covered with rock-cut reliefs of Hindu deities, generally dated to the "
            "medieval period. The carvings are reached by boat or by a road and short walk, and the "
            "river setting makes the site popular with photographers."
        ),
        "category": "heritage",
        "district": "gomati",
        "locality": "Amarpur",
        "latitude": 23.4083,
        "longitude": 91.6792,
        "extra_tags": "Nature",
        "popularity": 84,
        "facilities": "Boat point; very limited visitor facilities.",
        "accessibility_info": "Boat access and uneven ground at the carvings.",
        "safety_notes": "Take a local boat and guide; the water level changes with the season.",
        "image_alt": "Illustration of carved figures on a steep rock face beside a river.",
    },
    {
        "name": "Pilak",
        "slug": "pilak",
        "tagline": "Buddhist and Hindu sculptures in South Tripura",
        "short_description": "An archaeological site at Jolaibari with Buddhist and Hindu stone sculptures.",
        "description": (
            "Pilak, near Jolaibari in South Tripura, is an archaeological site where sculptures and "
            "structural remains connected with Buddhist and Hindu traditions have been found. Many "
            "of the finds are displayed in the site museum and in the State Museum in Agartala."
        ),
        "category": "heritage",
        "district": "south-tripura",
        "locality": "Jolaibari",
        "latitude": 23.1547,
        "longitude": 91.4225,
        "extra_tags": "Culture",
        "popularity": 80,
        "facilities": "Site museum and basic pathways.",
        "accessibility_info": "Level ground with some uneven excavated areas.",
        "safety_notes": "Do not touch or climb on the sculptures and structural remains.",
        "image_alt": "Illustration of stone sculptures displayed at an open archaeological site.",
    },
    {
        "name": "Trishna Wildlife Sanctuary",
        "slug": "trishna-wildlife-sanctuary",
        "tagline": "Forest sanctuary known for the Indian bison",
        "short_description": "A sanctuary in South Tripura known for the Indian bison (gayal) and forest habitat.",
        "description": (
            "Trishna Wildlife Sanctuary in South Tripura protects moist deciduous forest that is "
            "known for the Indian bison (gayal) along with other mammals and birds. Visits usually "
            "begin from the range office, and early mornings are the best time for wildlife sightings."
        ),
        "category": "wildlife",
        "district": "south-tripura",
        "locality": "Belonia",
        "latitude": 23.1667,
        "longitude": 91.3833,
        "extra_tags": "Nature",
        "popularity": 79,
        "facilities": "Forest range office; carry your own water and food.",
        "accessibility_info": "Forest tracks, not suitable for wheelchairs.",
        "safety_notes": "Enter with forest department permission and a guide; avoid travelling after dark.",
        "image_alt": "Illustration of a dense forest clearing with tall grass.",
    },
    {
        "name": "Kamalasagar",
        "slug": "kamalasagar",
        "tagline": "A temple and lake near the Bangladesh border",
        "short_description": "A temple beside Kamalasagar lake at Kashba, close to the Bangladesh border.",
        "description": (
            "Kamalasagar, at Kashba in Sepahijala district, combines a lake with a temple associated "
            "with Maharaja Dhanya Manikya. The lake lies beside the border and the site is a popular "
            "picnic and pilgrimage stop on the way to Neermahal."
        ),
        "category": "temples",
        "district": "sepahijala",
        "locality": "Kashba",
        "latitude": 23.5383,
        "longitude": 91.2703,
        "extra_tags": "Heritage,Lakes",
        "popularity": 78,
        "facilities": "Parking, small shops and a lakeside walkway.",
        "accessibility_info": "Level lakeside path; the temple itself has steps.",
        "safety_notes": "The site is close to the international border - carry identification.",
        "image_alt": "Illustration of a small temple beside a calm lake.",
    },
    {
        "name": "Bhuvaneswari Temple",
        "slug": "bhuvaneswari-temple",
        "tagline": "A riverside temple at Udaipur",
        "short_description": "A 17th-century temple on the bank of the Gomti river at Udaipur.",
        "description": (
            "The Bhuvaneswari temple stands on the bank of the Gomti river at Udaipur and is "
            "associated with Maharaja Govinda Manikya. The temple and its river setting appear in "
            "Rabindranath Tagore's writing, and the ghat beside it is used during festivals."
        ),
        "category": "temples",
        "district": "gomati",
        "locality": "Udaipur",
        "latitude": 23.5016,
        "longitude": 91.4750,
        "extra_tags": "Heritage,Culture",
        "popularity": 77,
        "facilities": "Steps down to the river ghat; shops nearby in Udaipur town.",
        "accessibility_info": "Steps between the road and the temple; assistance may be needed.",
        "safety_notes": "Take care on the river steps, especially during the monsoon.",
        "image_alt": "Illustration of a temple with steps leading down to a river.",
    },
    {
        "name": "Boxanagar",
        "slug": "boxanagar",
        "tagline": "Remains of a Buddhist stupa complex",
        "short_description": "An archaeological site near Sonamura with the remains of a Buddhist stupa.",
        "description": (
            "Boxanagar, near Sonamura in Sepahijala district, is an archaeological site where the "
            "remains of a stupa and an associated temple complex have been excavated. Sculptures "
            "from the site are displayed in the State Museum in Agartala."
        ),
        "category": "heritage",
        "district": "sepahijala",
        "locality": "Sonamura",
        "latitude": 23.4486,
        "longitude": 91.3125,
        "extra_tags": "Culture",
        "popularity": 76,
        "facilities": "Excavated area with basic pathways; no visitor centre.",
        "accessibility_info": "Level ground with exposed brick foundations.",
        "safety_notes": "Do not walk on the exposed structures.",
        "image_alt": "Illustration of brick foundations of an ancient stupa.",
    },
    {
        "name": "Heritage Park",
        "slug": "heritage-park",
        "tagline": "Miniature Tripura in the heart of Agartala",
        "short_description": "A park in Agartala with replicas of the state's heritage structures.",
        "description": (
            "Heritage Park in Agartala displays scale replicas of important buildings and monuments "
            "from across Tripura, with landscaped gardens and a toy train for children. It is an easy "
            "half-day visit inside the city and pairs well with the Ujjayanta Palace museum."
        ),
        "category": "culture",
        "district": "west-tripura",
        "locality": "Agartala",
        "latitude": 23.8306,
        "longitude": 91.2806,
        "extra_tags": "Heritage",
        "popularity": 74,
        "facilities": "Gardens, toy train, seating and food stalls.",
        "accessibility_info": "Paved, level paths suitable for wheelchairs and prams.",
        "safety_notes": "Supervise children around the toy train and water features.",
        "image_alt": "Illustration of a landscaped park with miniature heritage buildings.",
    },
    {
        "name": "Gumti Wildlife Sanctuary",
        "slug": "gumti-wildlife-sanctuary",
        "tagline": "Riverine forest along the Gumti",
        "short_description": "A sanctuary in Gomati district around the Gumti river and its forests.",
        "description": (
            "Gumti Wildlife Sanctuary follows the Gumti river and protects forest and wetland habitat "
            "used by elephants, primates and water birds. The sanctuary is usually visited from the "
            "Amarpur side and requires prior permission from the forest department."
        ),
        "category": "wildlife",
        "district": "gomati",
        "locality": "Amarpur",
        "latitude": 23.4167,
        "longitude": 91.6000,
        "extra_tags": "Nature,Lakes",
        "popularity": 72,
        "facilities": "Very limited; arrange transport, water and food in advance.",
        "accessibility_info": "Forest roads and boat sections.",
        "safety_notes": "Travel with forest department permission and a local guide.",
        "image_alt": "Illustration of a river winding through dense forest.",
    },
    {
        "name": "Neermahal Boat Ghat (draft record)",
        "slug": "neermahal-boat-ghat-draft",
        "tagline": "Draft record used to test the publishing workflow",
        "short_description": "A draft destination that is hidden from the public site until an admin publishes it.",
        "description": (
            "This draft record exists so the admin publishing workflow can be tested: it is not "
            "published, so it never appears on the public homepage, Explore page, map or planner."
        ),
        "category": "culture",
        "district": "sepahijala",
        "locality": "Melaghar",
        "latitude": None,
        "longitude": None,
        "extra_tags": "",
        "popularity": 1,
        "is_published": False,
        "image_alt": "Placeholder illustration for a draft destination record.",
    },
]

BUSINESSES = [
    {
        "name": "Demo Homestay near Bishalgarh",
        "slug": "demo-homestay-bishalgarh",
        "category": "Homestay",
        "short_description": "Demo listing used to test the Local Experiences directory.",
        "description": (
            "This is a demonstration record, not a real business. It exists so the directory, the "
            "filters and the inquiry form can be tested before real partners are onboarded."
        ),
        "district": "sepahijala",
        "locality": "Bishalgarh",
        "approval_status": "approved",
        "status_note": "Demo listing for UI testing - replace with a verified partner before launch.",
        "image_alt": "Illustration of a simple guest house with a garden.",
    },
    {
        "name": "Demo Local Guide - Agartala",
        "slug": "demo-local-guide-agartala",
        "category": "Local Guide",
        "short_description": "Demo listing used to test the guides category.",
        "description": (
            "Demonstration record for the guide category. Contact details are intentionally empty "
            "because the prototype must not publish unverified personal contact information."
        ),
        "district": "west-tripura",
        "locality": "Agartala",
        "languages": "Bengali, English, Kokborok",
        "approval_status": "approved",
        "status_note": "Demo listing for UI testing - no real contact details are stored.",
        "image_alt": "Illustration of a guide holding a map.",
    },
    {
        "name": "Demo Restaurant - Udaipur",
        "slug": "demo-restaurant-udaipur",
        "category": "Restaurant",
        "short_description": "Demo listing used to test the food category.",
        "description": (
            "Demonstration record for the restaurant category, including the optional price note "
            "field which stays empty until a verified partner supplies prices."
        ),
        "district": "gomati",
        "locality": "Udaipur",
        "approval_status": "approved",
        "status_note": "Demo listing for UI testing - replace with a verified partner before launch.",
        "image_alt": "Illustration of a plate of local food on a table.",
    },
    {
        "name": "Demo Transport Service - Agartala",
        "slug": "demo-transport-service-agartala",
        "category": "Transport",
        "short_description": "Demo listing used to test the transport category.",
        "description": (
            "Demonstration record for transport providers. The prototype does not show live "
            "availability or take bookings."
        ),
        "district": "west-tripura",
        "locality": "Agartala",
        "approval_status": "approved",
        "status_note": "Demo listing for UI testing.",
        "image_alt": "Illustration of a small vehicle on a road.",
    },
    {
        "name": "Demo Handicraft Co-operative",
        "slug": "demo-handicraft-cooperative",
        "category": "Handicrafts",
        "short_description": "Pending demo listing that an administrator has to approve first.",
        "description": (
            "Demonstration record left in the pending state so the admin approval workflow can be "
            "tested. Pending records never appear on the public Local Experiences page."
        ),
        "district": "west-tripura",
        "locality": "Agartala",
        "approval_status": "pending",
        "status_note": "Demo listing for UI testing.",
        "image_alt": "Illustration of woven bamboo baskets.",
    },
    {
        "name": "Demo Cultural Experience - Jampui Hills",
        "slug": "demo-cultural-experience-jampui",
        "category": "Cultural Experience",
        "short_description": "Pending demo listing for cultural experiences.",
        "description": (
            "Demonstration record for cultural experiences, left in the pending state. Any real "
            "cultural description must be reviewed by community representatives before publishing."
        ),
        "district": "north-tripura",
        "locality": "Vanghmun",
        "approval_status": "pending",
        "status_note": "Demo listing for UI testing.",
        "image_alt": "Illustration of dancers performing in a village square.",
    },
]


def _upsert(model, lookup: dict, values: dict):
    """Fetch a record by its unique fields or create it, then apply ``values``."""
    instance = model.query.filter_by(**lookup).first()
    if instance is None:
        instance = model(**lookup)
        db.session.add(instance)
    for key, value in values.items():
        setattr(instance, key, value)
    return instance


def seed_categories() -> int:
    count = 0
    for data in CATEGORIES:
        _upsert(Category, {"slug": data["slug"]}, data)
        count += 1
    db.session.commit()
    return count


def seed_districts() -> int:
    count = 0
    for data in DISTRICTS:
        _upsert(District, {"slug": data["slug"]}, data)
        count += 1
    db.session.commit()
    return count


def seed_places() -> int:
    categories = {category.slug: category for category in Category.query.all()}
    districts = {district.slug: district for district in District.query.all()}
    count = 0
    for data in PLACES:
        payload = dict(data)
        category = categories.get(payload.pop("category"))
        district = districts.get(payload.pop("district"))
        if category is None or district is None:
            raise RuntimeError(f"Category or district missing while seeding {data['slug']}")
        values = dict(payload)
        values["category_id"] = category.id
        values["district_id"] = district.id
        values.setdefault("is_published", True)
        values["image_url"] = f"{IMAGE_BASE}/{data['slug']}.svg"
        values["gallery"] = [
            {"url": f"{IMAGE_BASE}/{data['slug']}.svg", "alt": data.get("image_alt") or data["name"]},
            {"url": f"{IMAGE_BASE}/{data['slug']}-view.svg", "alt": f"Second placeholder view of {data['name']}"},
        ]
        values["coordinates_verified"] = False
        values["coordinate_source"] = "Approximate location compiled from public maps - pending field verification."
        values["is_verified"] = False
        values["verified_by"] = None
        values["last_verified_at"] = None
        values["verification_notes"] = (
            "Not yet verified. Fees, opening hours, closed days and best season are intentionally blank."
        )
        values["source_note"] = SOURCE_NOTE
        values.setdefault("address", data.get("locality"))
        _upsert(Place, {"slug": data["slug"]}, values)
        count += 1
    db.session.commit()
    return count


def seed_businesses() -> int:
    districts = {district.slug: district for district in District.query.all()}
    count = 0
    for index, data in enumerate(BUSINESSES):
        payload = dict(data)
        district = districts.get(payload.pop("district"))
        values = dict(payload)
        values["district_id"] = district.id if district else None
        values["image_url"] = f"{IMAGE_BASE}/businesses/{data['slug']}.svg"
        values.setdefault("contact_name", None)
        values.setdefault("contact_phone", None)
        values.setdefault("contact_email", None)
        values.setdefault("price_note", None)
        values.setdefault("latitude", None)
        values.setdefault("longitude", None)
        _upsert(Business, {"slug": data["slug"]}, values)
        count += 1
    db.session.commit()
    return count


def seed_admin(email: str, password: str, name: str = "Site Administrator") -> User | None:
    """Create or update the administrator account (never overwrites a password with an empty one)."""
    if not email or not password:
        return None
    user = User.query.filter_by(email=email.lower()).first()
    if user is None:
        user = User(name=name, email=email.lower(), role="admin")
        db.session.add(user)
    user.role = "admin"
    user.set_password(password)
    db.session.commit()
    return user


def seed_all(with_admin: bool = False, admin_email: str = "", admin_password: str = "") -> dict:
    """Seed every table and return a summary of what was written."""
    summary = {
        "categories": seed_categories(),
        "districts": seed_districts(),
        "places": seed_places(),
        "businesses": seed_businesses(),
        "admin": None,
    }
    if with_admin:
        admin = seed_admin(admin_email, admin_password)
        summary["admin"] = admin.email if admin else None
    return summary


def seed_today() -> date:  # pragma: no cover - convenience for scripts
    return date.today()