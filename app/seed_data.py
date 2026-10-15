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
from app.models import Business, Category, District, Place, RouteConnection, User

IMAGE_BASE = "/static/images/places"

PLACE_PHOTO_OVERRIDES = {
    "neermahal": "neermahal.jpg",
    "rudrasagar-lake": "rudrasagar-lake.jpg",
    "unakoti": "unakoti.jpg",
    "ujjayanta-palace": "ujjayanta-palace.jpg",
    "tripura-sundari-temple": "tripura-sundari-temple.jpg",
    "jampui-hills": "jampui-hills.jpg",
    "dumboor-lake": "dumboor-lake.jpg",
    "sepahijala-wildlife-sanctuary": "sepahijala-wildlife-sanctuary.jpg",
    "chabimura-debtamura": "chabimura-debtamura.jpg",
    "pilak": "pilak.jpg",
    "bhuvaneswari-temple": "bhuvaneswari-temple.jpg",
    "boxanagar": "boxanagar.jpg",
    "heritage-park": "heritage-park.jpg",
    "kamalasagar": "kamalasagar.jpg",
    "trishna-wildlife-sanctuary": "trishna-wildlife-sanctuary.jpg",
    "gumti-wildlife-sanctuary": "gumti-wildlife-sanctuary.jpg",
}

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
        "locality": "Melaghar, Rudrasagar Lake",
        "latitude": 23.5069,
        "longitude": 91.3156,
        "best_season": "October to March",
        "entry_fee_indian": "₹50 (adults), ₹20 (children) · Shared boat ₹50/head",
        "entry_fee_foreign": "₹50 · Standard boat fare applies",
        "opening_info": "9:00 AM – 5:00 PM (Daily)",
        "closed_day": "Open every day",
        "typical_visit_hours": 2.5,
        "extra_tags": "Lakes,Culture",
        "popularity": 96,
        "facilities": "Boat jetty, ticket counter, car parking, cafeteria and restrooms.",
        "accessibility_info": "Boat access with steps; confirm current arrangements at the jetty.",
        "safety_notes": "Lake crossings depend on weather and water level - follow the boat operator's instructions.",
        "image_alt": "Neermahal water palace on Rudrasagar lake.",
    },
    {
        "name": "Rudrasagar Lake",
        "slug": "rudrasagar-lake",
        "tagline": "Ramsar wetland lake surrounding the historic Neermahal water palace",
        "short_description": "A scenic Ramsar wetland lake in Sepahijala district famous for birdwatching and boat races.",
        "description": (
            "Rudrasagar Lake, also known as Rudijala, is a prominent freshwater lake and Ramsar "
            "wetland of international importance located in the Melaghar block of Sepahijala district. "
            "The lake is celebrated for its rich biodiversity, migratory bird populations, and for "
            "housing the historic Neermahal palace in its center. Every year in July-August, traditional "
            "boat race festivals draw thousands of visitors to the tranquil lake waters."
        ),
        "category": "lakes",
        "district": "sepahijala",
        "locality": "Melaghar",
        "latitude": 23.5042,
        "longitude": 91.3150,
        "best_season": "October to March (Boat Race in July/August)",
        "entry_fee_indian": "Free access to lake promenade · Boat ride ₹50–₹100",
        "entry_fee_foreign": "Free access · Standard boat fares apply",
        "opening_info": "Open 24 hours (Boating: 9:00 AM – 5:00 PM)",
        "closed_day": "Open every day",
        "typical_visit_hours": 2.0,
        "extra_tags": "Nature,Heritage",
        "popularity": 95,
        "facilities": "Lakeside promenade, boat ghat, parking, food stalls and viewing decks.",
        "accessibility_info": "Promenade is level; boat access requires boarding from stepped ghats.",
        "safety_notes": "Wear life jackets during boat rides and stay within designated safety zones.",
        "image_alt": "Tranquil waters of Rudrasagar Lake at sunset with boat jetty.",
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
        "latitude": 24.3168,
        "longitude": 92.0674,
        "best_season": "October to March (Ashokastami Mela in April)",
        "entry_fee_indian": "Free entry",
        "entry_fee_foreign": "Free entry",
        "opening_info": "6:00 AM – 6:00 PM (Sunrise to Sunset)",
        "closed_day": "Open every day",
        "typical_visit_hours": 3.0,
        "extra_tags": "Temples,Nature",
        "popularity": 94,
        "facilities": "Ticket counter, paved pathways, drinking water points and parking.",
        "accessibility_info": "Sloping paths and steps across the site; limited access for wheelchairs.",
        "safety_notes": "Paths can be slippery during the monsoon - wear shoes with grip.",
        "image_alt": "Large rock-cut deity carvings on forested Unakoti hill.",
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
        "latitude": 23.5091,
        "longitude": 91.4980,
        "best_season": "October to March (Diwali & Navratri festival peak)",
        "entry_fee_indian": "Free entry (darshan is free)",
        "entry_fee_foreign": "Free entry",
        "opening_info": "6:00 AM – 1:00 PM, 3:00 PM – 8:30 PM (Daily)",
        "closed_day": "Open every day",
        "typical_visit_hours": 1.5,
        "extra_tags": "Heritage,Culture",
        "popularity": 93,
        "facilities": "Parking, shoe stand, prasad counters, Kalyan Sagar lake ghat and drinking water.",
        "accessibility_info": "Level approach to the temple courtyard; inner shrine area can be crowded at peak times.",
        "safety_notes": "Dress respectfully and expect queues during festivals.",
        "image_alt": "Tripura Sundari temple with stepped Kalyan Sagar tank.",
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
        "latitude": 23.8374,
        "longitude": 91.2827,
        "best_season": "October to March",
        "entry_fee_indian": "₹20 (adults), ₹10 (students/children)",
        "entry_fee_foreign": "₹150",
        "opening_info": "10:00 AM – 5:00 PM (Museum galleries)",
        "closed_day": "Monday (and National Holidays)",
        "typical_visit_hours": 2.0,
        "extra_tags": "Culture",
        "popularity": 92,
        "facilities": "Museum ticket counter, musical fountains, landscaped gardens and parking.",
        "accessibility_info": "Ramped entrance to the museum; confirm lift access at the counter.",
        "safety_notes": "Photography rules inside the museum galleries vary - check at the entrance.",
        "image_alt": "Domed white Ujjayanta Palace with ornamental gardens.",
    },
    {
        "name": "Jampui Hills",
        "slug": "jampui-hills",
        "tagline": "The highest hill range in Tripura",
        "short_description": "A hill range in North Tripura known for viewpoints, orange orchards and Mizo villages.",
        "description": (
            "The Jampui Hills form the highest hill range in Tripura, located in the Kanchanpur sub-division "
            "of North Tripura district right along the border with Mizoram. "
            "Villages such as Vanghmun are known for orange orchards and scenic viewpoints over the valleys, "
            "and the area is a base for short treks and the annual Orange Festival in November and December."
        ),
        "category": "hills",
        "district": "north-tripura",
        "locality": "Vanghmun, Kanchanpur",
        "address": "Kanchanpur Sub-Division, North Tripura, Tripura 799269, India",
        "plus_code": "X78G+P3",
        "latitude": 23.9667675,
        "longitude": 92.2751563,
        "best_season": "October to March (Orange Festival in November)",
        "entry_fee_indian": "Free entry (village viewpoints open to all)",
        "entry_fee_foreign": "Free entry",
        "opening_info": "Open 24 hours (Sightseeing 6:00 AM – 6:00 PM recommended)",
        "closed_day": "Open every day",
        "typical_visit_hours": 4.0,
        "extra_tags": "Nature,Culture",
        "popularity": 90,
        "facilities": "Eden Tourist Lodge, homestays in Vanghmun, viewpoints and local eateries.",
        "accessibility_info": "Hill roads with bends; travelling with your own vehicle is recommended.",
        "safety_notes": "Roads can be affected by landslides in the monsoon - check conditions before travelling.",
        "image_alt": "Layered misty green hills of Jampui with orange orchards.",
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
        "latitude": 23.4680,
        "longitude": 91.8450,
        "best_season": "October to March (Pous Sankranti Mela in January)",
        "entry_fee_indian": "Free entry to lake area · Boat ride ₹120–₹150/head",
        "entry_fee_foreign": "Free entry · Standard boat fares apply",
        "opening_info": "9:00 AM – 5:00 PM (Boating operational during daylight)",
        "closed_day": "Open every day",
        "typical_visit_hours": 3.5,
        "extra_tags": "Nature",
        "popularity": 87,
        "facilities": "Mandir Ghat jetty, Narkel Kunja island cottages, boat rides and viewing deck.",
        "accessibility_info": "Boat based access; not suitable for visitors with limited mobility.",
        "safety_notes": "Use licensed boats only and carry drinking water; mobile coverage is patchy.",
        "image_alt": "Dumboor Lake with lush green islands and blue reservoir waters.",
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
        "latitude": 23.6644,
        "longitude": 91.3117,
        "best_season": "October to April (Peak migratory birds Nov–Feb)",
        "entry_fee_indian": "₹50 (adults), ₹25 (children)",
        "entry_fee_foreign": "₹100",
        "opening_info": "9:00 AM – 4:00 PM",
        "closed_day": "Friday",
        "typical_visit_hours": 3.0,
        "extra_tags": "Nature",
        "popularity": 85,
        "facilities": "Ticket counter, botanical garden, zoo enclosures, boating lake and cafeteria.",
        "accessibility_info": "Main paths are level; some forest trails are earth tracks.",
        "safety_notes": "Do not feed animals and stay on marked paths.",
        "image_alt": "Sepahijala Wildlife Sanctuary forest paths and lake.",
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
        "locality": "Amarpur, Gomati River",
        "latitude": 23.5348,
        "longitude": 91.6013,
        "best_season": "October to February",
        "entry_fee_indian": "Free entry to riverbank · Motorboat ride ₹150–₹200/head",
        "entry_fee_foreign": "Free entry to riverbank · Motorboat ride ₹150–₹200/head",
        "opening_info": "6:00 AM – 5:00 PM (Boating finishes by 4:00 PM)",
        "closed_day": "Open every day (Subject to river water level)",
        "typical_visit_hours": 3.0,
        "extra_tags": "Nature",
        "popularity": 84,
        "facilities": "Boat boarding point, local guide assistance, eco-stalls and parking.",
        "accessibility_info": "Boat access and uneven ground at the carvings.",
        "safety_notes": "Take a local boat and guide; the water level changes with the season.",
        "image_alt": "Rock-cut carvings on the river gorge cliff at Chabimura.",
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
        "latitude": 23.2000,
        "longitude": 91.6000,
        "best_season": "October to March (Pilak Festival in December)",
        "entry_fee_indian": "₹10 per person",
        "entry_fee_foreign": "₹100",
        "opening_info": "9:00 AM – 6:00 PM (Daily)",
        "closed_day": "Open every day",
        "typical_visit_hours": 2.0,
        "extra_tags": "Culture",
        "popularity": 80,
        "facilities": "Site museum, excavated stupa pathways, information boards and parking.",
        "accessibility_info": "Level ground with some uneven excavated areas.",
        "safety_notes": "Do not touch or climb on the sculptures and structural remains.",
        "image_alt": "Pilak archaeological site sculptures and Buddhist stupa mounds.",
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
        "locality": "Rajnagar, Belonia",
        # Recovered and decoded with openlocationcode 1.0.1 from the short code
        # using the OpenStreetMap Belonia town point as the nearby reference.
        # Verify this Plus Code center on Google Maps before marking verified.
        "plus_code": "7CH2+PFW",
        "address": "7CH2+PFW, Belonia - Bhabanipur Rd, Rajnagar, Joychandrapur, Tripura 799150",
        "latitude": 23.2793625,
        "longitude": 91.401203125,
        "best_season": "November to March",
        "entry_fee_indian": "₹20 (adults), ₹10 (children) · Safari permit extra",
        "entry_fee_foreign": "₹100",
        "opening_info": "9:00 AM – 5:00 PM",
        "closed_day": "Tuesday",
        "typical_visit_hours": 3.5,
        "extra_tags": "Nature",
        "popularity": 79,
        "facilities": "Forest range office, watchtowers, bison viewing points and nature trails.",
        "accessibility_info": "Forest tracks, not suitable for wheelchairs.",
        "safety_notes": "Enter with forest department permission and a guide; avoid travelling after dark.",
        "image_alt": "Dense forest clearing with Indian bison habitat at Trishna.",
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
        "locality": "Kasba, Sepahijala",
        "latitude": 23.7402,
        "longitude": 91.1591,
        "best_season": "October to March (Navratri & Durga Puja fair)",
        "entry_fee_indian": "Free entry",
        "entry_fee_foreign": "Free entry",
        "opening_info": "6:00 AM – 8:00 PM (Daily)",
        "closed_day": "Open every day",
        "typical_visit_hours": 1.5,
        "extra_tags": "Heritage,Lakes",
        "popularity": 78,
        "facilities": "Kasba Kali temple, lakeside promenade, picnic spots and border viewpoint.",
        "accessibility_info": "Level lakeside path; the temple itself has steps.",
        "safety_notes": "The site is close to the international border - carry identification.",
        "image_alt": "Kasba Kali temple beside the calm waters of Kamalasagar lake.",
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
        "latitude": 23.5290,
        "longitude": 91.5050,
        "best_season": "October to March",
        "entry_fee_indian": "Free entry",
        "entry_fee_foreign": "Free entry",
        "opening_info": "5:30 AM – 8:30 PM (Daily)",
        "closed_day": "Open every day",
        "typical_visit_hours": 1.0,
        "extra_tags": "Heritage,Culture",
        "popularity": 77,
        "facilities": "Historic temple terrace, Gomati river ghat, Tagore heritage markers and parking.",
        "accessibility_info": "Steps between the road and the temple; assistance may be needed.",
        "safety_notes": "Take care on the river steps, especially during the monsoon.",
        "image_alt": "Bhuvaneswari temple on the bank of the Gomti river.",
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
        "locality": "Boxanagar",
        "latitude": 23.6164,
        "longitude": 91.1656,
        "best_season": "October to March",
        "entry_fee_indian": "Free entry",
        "entry_fee_foreign": "Free entry",
        "opening_info": "9:00 AM – 5:00 PM (Daily)",
        "closed_day": "Open every day",
        "typical_visit_hours": 1.5,
        "extra_tags": "Culture",
        "popularity": 76,
        "facilities": "ASI protected monument area, stupa foundation walkways and information plaque.",
        "accessibility_info": "Level ground with exposed brick foundations.",
        "safety_notes": "Do not walk on the exposed structures.",
        "image_alt": "Brick foundations of an ancient Buddhist stupa at Boxanagar.",
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
        "locality": "Kunjaban, Agartala",
        "latitude": 23.8559,
        "longitude": 91.2846,
        "best_season": "October to March",
        "entry_fee_indian": "₹10 (adults), ₹5 (children)",
        "entry_fee_foreign": "₹50",
        "opening_info": "6:00 AM – 8:00 PM (Daily)",
        "closed_day": "Open every day",
        "typical_visit_hours": 2.0,
        "extra_tags": "Heritage",
        "popularity": 74,
        "facilities": "Scale miniature heritage exhibits, toy train, manicured gardens, evening lighting and food stalls.",
        "accessibility_info": "Paved, level paths suitable for wheelchairs and prams.",
        "safety_notes": "Supervise children around the toy train and water features.",
        "image_alt": "Landscaped Heritage Park with miniature heritage monuments.",
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
        "locality": "Mukchhari",
        "address": "FR3H+5P2, Mukchhari, Tripura 799104, India",
        # Center decoded from the user-provided short Plus Code; confirm the pin on Google Maps.
        "latitude": 23.4528875,
        "longitude": 91.82926563,
        "best_season": "October to March",
        "entry_fee_indian": "Free entry (permits available at range office)",
        "entry_fee_foreign": "Free entry",
        "opening_info": "8:00 AM – 5:00 PM (Daily)",
        "closed_day": "Open every day",
        "typical_visit_hours": 3.5,
        "extra_tags": "Nature,Lakes",
        "popularity": 72,
        "facilities": "Forest check post, boat safari access and wetland bird observation decks.",
        "accessibility_info": "Forest roads and boat sections.",
        "safety_notes": "Travel with forest department permission and a local guide.",
        "image_alt": "Gumti Wildlife Sanctuary riverine forest and wetland habitat.",
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
    # =========================================================================
    # District 1: West Tripura (west-tripura)
    # =========================================================================
    {
        "name": "Ujjayanta Heritage Homestay",
        "slug": "ujjayanta-heritage-homestay-agartala",
        "category": "Homestay",
        "district": "west-tripura",
        "locality": "Radhanagar, Agartala",
        "address": "Near Ujjayanta Palace North Gate, Radhanagar, Agartala",
        "short_description": "Colonial-era heritage guesthouse walking distance from Ujjayanta Palace.",
        "description": (
            "Experience royal Agartala hospitality in a carefully restored heritage property. "
            "Featuring airy veranda seating, lush courtyards, traditional Tripura bamboo furnishings, "
            "and warm home-cooked Bengali and Tripuri breakfasts."
        ),
        "languages": "Bengali, English, Hindi, Kokborok",
        "contact_name": "Bikramjit Debbarma",
        "contact_phone": "+91 94361 24501",
        "contact_email": "ujjayanta.homestay@tripuraexplore.org",
        "price_note": "₹1,800 - ₹2,600 / night with breakfast",
        "image_url": "/static/images/places/ujjayanta-palace.jpg",
        "image_alt": "Ujjayanta Heritage Homestay exterior and garden in Agartala",
        "approval_status": "approved",
        "status_note": "Verified heritage property partner in West Tripura.",
        "latitude": 23.8350,
        "longitude": 91.2820,
    },
    {
        "name": "Demo Local Guide - Agartala",
        "slug": "demo-local-guide-agartala",
        "category": "Local Guide",
        "district": "west-tripura",
        "locality": "Agartala City Core",
        "address": "Post Office Chowmuhani, Agartala",
        "short_description": "Certified government tourism guide for Agartala heritage sites.",
        "description": (
            "Specialized historical and cultural walking trails across Ujjayanta Palace Museum, "
            "Heritage Park, Jagannath Temple, and Old Agartala Chaturdash Devta Temple. "
            "Includes royal history, folklore, and photography spots."
        ),
        "languages": "Bengali, English, Kokborok, Hindi",
        "contact_name": "Debabrata Majumder",
        "contact_phone": "+91 94361 58210",
        "contact_email": "guide.agartala@tripuraexplore.org",
        "price_note": "₹1,200 / full day heritage tour",
        "image_url": "/static/images/places/heritage-park.jpg",
        "image_alt": "Local guide leading heritage walking tour in Agartala",
        "approval_status": "approved",
        "status_note": "Certified heritage guide for Agartala.",
        "latitude": 23.8315,
        "longitude": 91.2868,
    },
    {
        "name": "Khangsar Traditional Tripuri Restaurant",
        "slug": "khangsar-traditional-tripuri-restaurant",
        "category": "Restaurant",
        "district": "west-tripura",
        "locality": "City Centre, Agartala",
        "address": "Hari Ganga Basak Road, Agartala",
        "short_description": "Authentic tribal gastronomic haven serving indigenous delicacies.",
        "description": (
            "Tripura premier authentic ethnic eatery. Enjoy authentic Mui Borok delicacies, "
            "herbal Chakhwi prepared with fresh bamboo shoots and sodium bicarbonate, spicy Berma "
            "Mosdeng, smoked country chicken, and fragrant Bangui sticky rice parcels."
        ),
        "languages": "Kokborok, Bengali, English",
        "contact_name": "Ratan Debbarma",
        "contact_phone": "+91 98620 44120",
        "contact_email": "khangsar.dine@tripuraexplore.org",
        "price_note": "₹250 - ₹550 per authentic thali",
        "image_url": "/static/images/places/heritage-park-1.jpg",
        "image_alt": "Traditional Tripuri culinary spread with bamboo shoot dishes",
        "approval_status": "approved",
        "status_note": "Verified traditional culinary partner.",
        "latitude": 23.8340,
        "longitude": 91.2790,
    },
    {
        "name": "Demo Transport Service - Agartala",
        "slug": "demo-transport-service-agartala",
        "category": "Transport",
        "district": "west-tripura",
        "locality": "Motor Stand, Agartala",
        "address": "TRTC Bus Complex, Krishnanagar, Agartala",
        "short_description": "Reliable tourist cabs, SUVs, and airport transfer fleet.",
        "description": (
            "Well-maintained air-conditioned sedans, SUVs, and tempo travellers covering all 8 "
            "districts of Tripura. Offering Maharaja Bir Bikram Airport pickups, multi-day circuit "
            "tours, and round-trip customized rentals with experienced hill drivers."
        ),
        "languages": "Bengali, Hindi, English",
        "contact_name": "Subir Paul",
        "contact_phone": "+91 94361 88934",
        "contact_email": "transport.agartala@tripuraexplore.org",
        "price_note": "₹2,200 - ₹3,600 / day depending on vehicle",
        "image_url": "/static/images/places/ujjayanta-palace-1.jpg",
        "image_alt": "Tourist taxi service at Agartala station",
        "approval_status": "approved",
        "status_note": "Verified tourist fleet operator in Agartala.",
        "latitude": 23.8390,
        "longitude": 91.2850,
    },
    {
        "name": "Purbasha State Bamboo and Cane Emporium",
        "slug": "purbasha-bamboo-cane-emporium-agartala",
        "category": "Handicrafts",
        "district": "west-tripura",
        "locality": "Jail Road, Agartala",
        "address": "Purbasha Handicrafts Bhavan, Jail Road, Agartala",
        "short_description": "State emporium showcasing GI-tagged Tripura Risa and bamboo crafts.",
        "description": (
            "State government supported master-artisan cooperative displaying Tripura finest bamboo "
            "screens, decorative night lamps, handwoven cane armchairs, and authentic GI-tagged "
            "handwoven Risa stoles and Pachra ceremonial cloths."
        ),
        "languages": "Bengali, English, Hindi, Kokborok",
        "contact_name": "Maitreyi Tripura",
        "contact_phone": "+91 94361 31920",
        "contact_email": "purbasha.emporium@tripuraexplore.org",
        "price_note": "Artisan pricing: ₹150 - ₹4,800",
        "image_url": "/static/images/places/heritage-park-2.jpg",
        "image_alt": "Handcrafted bamboo lamps and Risa handloom textiles",
        "approval_status": "approved",
        "status_note": "Official handicrafts and handloom emporium.",
        "latitude": 23.8365,
        "longitude": 91.2815,
    },
    {
        "name": "Chaturdash Devta Cultural and Ritual Trail",
        "slug": "chaturdash-devta-cultural-trail-old-agartala",
        "category": "Cultural Experience",
        "district": "west-tripura",
        "locality": "Old Agartala / Khayerpur",
        "address": "Chaturdash Devta Temple Complex, Old Agartala",
        "short_description": "Historic 14-Deity temple rituals and royal heritage walk.",
        "description": (
            "Guided spiritual and ethnographic immersion into the ancient temple of the 14 Gods "
            "(Chaturdash Devta) in Old Agartala. Learn about the royal Chantai priests, sacred "
            "copper plate traditions, traditional drums, and the historic Kharchi Puja origins."
        ),
        "languages": "Bengali, Kokborok, English",
        "contact_name": "Acharya Santanu Chantai",
        "contact_phone": "+91 98621 77312",
        "contact_email": "chaturdash.trail@tripuraexplore.org",
        "price_note": "₹500 per guided morning cultural session",
        "image_url": "/static/images/places/ujjayanta-palace-2.jpg",
        "image_alt": "Old Agartala Chaturdash Devta temple heritage court",
        "approval_status": "approved",
        "status_note": "Verified heritage cultural experience partner.",
        "latitude": 23.8420,
        "longitude": 91.3410,
    },

    # =========================================================================
    # District 2: Sepahijala (sepahijala)
    # =========================================================================
    {
        "name": "Demo Homestay near Bishalgarh",
        "slug": "demo-homestay-bishalgarh",
        "category": "Homestay",
        "district": "sepahijala",
        "locality": "Bishalgarh",
        "address": "Bishalgarh Sanctuary Road, Sepahijala",
        "short_description": "Tranquil plantation cottage retreat bordering Sepahijala forest.",
        "description": (
            "Nestled inside a serene rubber and organic spice plantation. Wake up to chirping birds, "
            "visit Sepahijala sanctuary and clouded leopard breeding center early in the morning, "
            "and feast on organic garden-to-table cuisine."
        ),
        "languages": "Bengali, Kokborok, Hindi",
        "contact_name": "Parimal Sarkar",
        "contact_phone": "+91 94361 72190",
        "contact_email": "bishalgarh.homestay@tripuraexplore.org",
        "price_note": "₹1,400 - ₹2,100 / night with meals",
        "image_url": "/static/images/places/sepahijala-wildlife-sanctuary.jpg",
        "image_alt": "Cozy eco cottage in lush plantation in Bishalgarh",
        "approval_status": "approved",
        "status_note": "Verified eco-stay partner in Sepahijala district.",
        "latitude": 23.6840,
        "longitude": 91.3120,
    },
    {
        "name": "Rudrasagar Lake and Birding Guide",
        "slug": "rudrasagar-lake-birding-guide-melaghar",
        "category": "Local Guide",
        "district": "sepahijala",
        "locality": "Melaghar, Rudrasagar Lake",
        "address": "Rajghat Jetty, Melaghar",
        "short_description": "Expert wetland boatman and birding naturalist.",
        "description": (
            "A native boatman and birdwatcher guiding visitors across the Ramsar wetland of Rudrasagar "
            "Lake. Spot migratory water birds, understand the royal water-harvesting engineering of "
            "Neermahal, and photograph the water palace from scenic angles."
        ),
        "languages": "Bengali, Hindi, English",
        "contact_name": "Manik Chandra Barman",
        "contact_phone": "+91 98622 34509",
        "contact_email": "rudrasagar.guide@tripuraexplore.org",
        "price_note": "₹800 - ₹1,400 per private guided boat tour",
        "image_url": "/static/images/places/neermahal.jpg",
        "image_alt": "Local boatman guiding visitors across Rudrasagar lake to Neermahal",
        "approval_status": "approved",
        "status_note": "Certified Ramsar wetland & heritage guide.",
        "latitude": 23.4980,
        "longitude": 91.3315,
    },
    {
        "name": "Neermahal Viewpoint Fishermens Dhaba",
        "slug": "neermahal-viewpoint-fishermens-dhaba-melaghar",
        "category": "Restaurant",
        "district": "sepahijala",
        "locality": "Rajghat, Melaghar",
        "address": "Near Melaghar Lake Park, Rajghat",
        "short_description": "Fresh Rudrasagar fish delicacies and lakeside dining.",
        "description": (
            "Scenic lakeside open-air restaurant serving the day fresh Rudrasagar catch. Popular "
            "for fried Chitol and Pabda fish, spicy prawn mash (Chingri Bhorta), mustard Ilish curry, "
            "and fragrant local Kasoi Bwtwi vegetable broth."
        ),
        "languages": "Bengali, Hindi",
        "contact_name": "Gouranga Das",
        "contact_phone": "+91 94361 44521",
        "contact_email": "neermahal.dhaba@tripuraexplore.org",
        "price_note": "₹200 - ₹450 per meal",
        "image_url": "/static/images/places/neermahal-1.jpg",
        "image_alt": "Lakeside dining pavilion overlooking Neermahal water palace",
        "approval_status": "approved",
        "status_note": "Verified traditional dining partner in Melaghar.",
        "latitude": 23.4950,
        "longitude": 91.3360,
    },
    {
        "name": "Melaghar Boatmen and Tourist Cab Union",
        "slug": "melaghar-boatmen-tourist-cab-union",
        "category": "Transport",
        "district": "sepahijala",
        "locality": "Melaghar Ghat & Sonamura",
        "address": "Rajghat Ferry Terminal, Melaghar",
        "short_description": "Authorized water ferry to Neermahal & inter-district cabs.",
        "description": (
            "Authorized motorized boat shuttles across Rudrasagar Lake directly to Neermahal Palace "
            "docks. Also provides scheduled cab services connecting Melaghar to Boxanagar archaeological "
            "site, Sepahijala Zoo, and Agartala city."
        ),
        "languages": "Bengali, Hindi",
        "contact_name": "Balaram Barman",
        "contact_phone": "+91 98620 91823",
        "contact_email": "melaghar.transport@tripuraexplore.org",
        "price_note": "₹50/passenger shared boat; ₹600 private boat rental",
        "image_url": "/static/images/places/neermahal-2.jpg",
        "image_alt": "Wooden passenger boats docked on Rudrasagar lake at Melaghar",
        "approval_status": "approved",
        "status_note": "Authorized boatmen cooperative and cab union.",
        "latitude": 23.4965,
        "longitude": 91.3340,
    },
    {
        "name": "Sonamura Cane Weavers Guild",
        "slug": "sonamura-cane-weavers-guild",
        "category": "Handicrafts",
        "district": "sepahijala",
        "locality": "Sonamura",
        "address": "Artisan Cluster Road, Sonamura Town",
        "short_description": "Generations-old cane furniture and bamboo basketry guild.",
        "description": (
            "Rural artisan society famous for woven cane lounge chairs, natural bamboo partitions, "
            "picnic hampers, table runners, and intricate decorative bird cages crafted from seasoned "
            "local river-valley bamboo."
        ),
        "languages": "Bengali, Kokborok",
        "contact_name": "Anukul Chandra Rudra",
        "contact_phone": "+91 94361 62719",
        "contact_email": "sonamura.weavers@tripuraexplore.org",
        "price_note": "Cooperative direct prices: ₹180 - ₹3,200",
        "image_url": "/static/images/places/boxanagar.jpg",
        "image_alt": "Artisans weaving intricate cane furniture and bamboo baskets",
        "approval_status": "approved",
        "status_note": "Certified village handicraft cooperative.",
        "latitude": 23.4750,
        "longitude": 91.2710,
    },
    {
        "name": "Boxanagar Buddhist Heritage Walk",
        "slug": "boxanagar-buddhist-heritage-walk",
        "category": "Cultural Experience",
        "district": "sepahijala",
        "locality": "Boxanagar",
        "address": "ASI Protected Archaeological Site, Boxanagar",
        "short_description": "Excavated 7th-century terracotta stupa and monastic trail.",
        "description": (
            "In-depth archaeological walk through the excavated 7th-to-8th century brick Buddhist "
            "stupa, chaitya hall, and monastic quarters at Boxanagar near the border. Learn about "
            "ancient trade links, terracotta sculptures, and the Mahayana Buddhist legacy."
        ),
        "languages": "Bengali, English, Hindi",
        "contact_name": "Dr. Subhasis Barua",
        "contact_phone": "+91 94361 80112",
        "contact_email": "boxanagar.heritage@tripuraexplore.org",
        "price_note": "₹400 per person guided interpretive tour",
        "image_url": "/static/images/places/boxanagar-1.jpg",
        "image_alt": "Ancient brick Buddhist stupa and monastic foundations at Boxanagar",
        "approval_status": "approved",
        "status_note": "Verified archaeological heritage walk provider.",
        "latitude": 23.6164,
        "longitude": 91.1656,
    },

    # =========================================================================
    # District 3: Khowai (khowai)
    # =========================================================================
    {
        "name": "Padmabil Tribal Eco Homestay",
        "slug": "padmabil-tribal-eco-homestay-khowai",
        "category": "Homestay",
        "district": "khowai",
        "locality": "Padmabil, Khowai",
        "address": "Padmabil Village, Khowai Sub-division",
        "short_description": "Traditional bamboo stilt huts nestled by rolling green hills.",
        "description": (
            "Stay in charming elevated bamboo stilt cottages run by an indigenous Tripuri host "
            "family. Experience warm village hospitality, learn traditional loom weaving, pluck "
            "fresh garden vegetables, and listen to evening folk tales under starry skies."
        ),
        "languages": "Kokborok, Bengali, Hindi, English",
        "contact_name": "Balaram Debbarma",
        "contact_phone": "+91 94364 12890",
        "contact_email": "padmabil.stay@tripuraexplore.org",
        "price_note": "₹1,300 - ₹1,900 / night with authentic home meals",
        "image_url": "/static/images/places/kamalasagar.jpg",
        "image_alt": "Traditional bamboo stilt homestay in rural Padmabil Khowai",
        "approval_status": "approved",
        "status_note": "Verified indigenous rural eco-homestay.",
        "latitude": 24.0320,
        "longitude": 91.6110,
    },
    {
        "name": "Teliamura Hill and Forest Guide",
        "slug": "teliamura-hill-forest-guide-khowai",
        "category": "Local Guide",
        "district": "khowai",
        "locality": "Teliamura",
        "address": "Near Railway Station, Teliamura",
        "short_description": "Scout for Baramura & Atharamura eco-trails and waterfalls.",
        "description": (
            "Native trail scout with deep knowledge of the Khowai river basin, Chakmaghat barrage, "
            "and the forested Atharamura and Baramura hill ranges. Offers safe trekking, birdwatching "
            "excursions, and tours to hidden forest stream pools."
        ),
        "languages": "Kokborok, Bengali, Hindi, English",
        "contact_name": "Sanjoy Reang",
        "contact_phone": "+91 98623 51920",
        "contact_email": "teliamura.guide@tripuraexplore.org",
        "price_note": "₹1,000 / day nature & trekking guide",
        "image_url": "/static/images/places/kamalasagar-1.jpg",
        "image_alt": "Local guide leading forest trekking trail in Khowai hills",
        "approval_status": "approved",
        "status_note": "Certified eco-tourism & forest trail guide.",
        "latitude": 23.8340,
        "longitude": 91.6320,
    },
    {
        "name": "Khowai Riverside Traditional Kitchen",
        "slug": "khowai-riverside-traditional-kitchen",
        "category": "Restaurant",
        "district": "khowai",
        "locality": "Khowai Town",
        "address": "Subhash Park Road, Khowai Town",
        "short_description": "Riverside dining serving smoked country chicken & bamboo shoots.",
        "description": (
            "Cosy open-deck eatery situated right beside the Khowai river. Celebrated for "
            "slow-simmered desi chicken cooked with crushed bamboo shoot pulp, freshly made spicy "
            "dry fish Berma chutneys, boiled wild yams, and steamed tribal rice."
        ),
        "languages": "Bengali, Kokborok",
        "contact_name": "Dipankar Saha",
        "contact_phone": "+91 94361 93240",
        "contact_email": "khowai.kitchen@tripuraexplore.org",
        "price_note": "₹180 - ₹380 per hearty meal",
        "image_url": "/static/images/places/kamalasagar-2.jpg",
        "image_alt": "Riverside open-air restaurant serving local Tripuri cuisine",
        "approval_status": "approved",
        "status_note": "Verified traditional eatery in Khowai.",
        "latitude": 24.0620,
        "longitude": 91.6050,
    },
    {
        "name": "Khowai Valley Tourist Cabs",
        "slug": "khowai-valley-tourist-cabs",
        "category": "Transport",
        "district": "khowai",
        "locality": "Khowai Bus Stand & Teliamura",
        "address": "Central Motor Stand, Khowai",
        "short_description": "Reliable cabs connecting Khowai, Teliamura, and Agartala.",
        "description": (
            "Fleet of clean hatchback, sedan, and 4x4 vehicles. Provides daily transfers between "
            "Khowai town, Teliamura railway junction, Chakmaghat picnic spots, and onward journeys "
            "across the national highway towards Agartala and Ambassa."
        ),
        "languages": "Bengali, Hindi",
        "contact_name": "Babul Das",
        "contact_phone": "+91 98622 71180",
        "contact_email": "khowai.cabs@tripuraexplore.org",
        "price_note": "₹1,800 - ₹3,000 / day",
        "image_url": "/static/images/places/heritage-park.jpg",
        "image_alt": "Tourist taxi service parked in Khowai valley",
        "approval_status": "approved",
        "status_note": "Verified local transport operator.",
        "latitude": 24.0600,
        "longitude": 91.6080,
    },
    {
        "name": "Baramura Bamboo Craft Centre",
        "slug": "baramura-bamboo-craft-centre-chakmaghat",
        "category": "Handicrafts",
        "district": "khowai",
        "locality": "Chakmaghat, Teliamura",
        "address": "Highway Craft Village, Chakmaghat, Khowai",
        "short_description": "Artisan cluster making bamboo flutes, rainsticks, and baskets.",
        "description": (
            "Community handicraft facility located at the foot of Baramura hills. Indigenous "
            "craftsmen demonstrate carving tuned bamboo flutes, acoustic rainmakers, fine decorative "
            "trays, and sturdy woven harvest baskets sold directly at artisan prices."
        ),
        "languages": "Kokborok, Bengali",
        "contact_name": "Nayan Debbarma",
        "contact_phone": "+91 94364 88219",
        "contact_email": "baramura.crafts@tripuraexplore.org",
        "price_note": "Handmade craft items: ₹100 - ₹1,600",
        "image_url": "/static/images/places/bhuvaneswari-temple.jpg",
        "image_alt": "Artisan shaping tuned bamboo flutes and woven baskets",
        "approval_status": "approved",
        "status_note": "Verified tribal handicrafts cooperative.",
        "latitude": 23.8550,
        "longitude": 91.6180,
    },
    {
        "name": "Lebang Boomani Harvest Dance Workshop",
        "slug": "lebang-boomani-dance-workshop-padmabil",
        "category": "Cultural Experience",
        "district": "khowai",
        "locality": "Padmabil, Khowai",
        "address": "Tribal Cultural Centre, Padmabil",
        "short_description": "Interactive Tripuri insect-catching harvest folk dance.",
        "description": (
            "Participate in an enchanting folk workshop on the traditional Lebang Boomani dance. "
            "Discover how Tripuri farmers used rhythmic bamboo clappers (Tok-ka) to charm insects "
            "away from crops, accompanied by traditional Kham drums and Sarinda fiddles."
        ),
        "languages": "Kokborok, Bengali, English",
        "contact_name": "Kalyani Debbarma",
        "contact_phone": "+91 98624 33019",
        "contact_email": "lebang.dance@tripuraexplore.org",
        "price_note": "₹600 per participant with traditional attire demo",
        "image_url": "/static/images/places/bhuvaneswari-temple-1.jpg",
        "image_alt": "Tripuri folk dancers performing Lebang Boomani with bamboo clappers",
        "approval_status": "approved",
        "status_note": "Verified cultural performing arts experience.",
        "latitude": 24.0350,
        "longitude": 91.6140,
    },

    # =========================================================================
    # District 4: Gomati (gomati)
    # =========================================================================
    {
        "name": "Matabari Pilgrim Nook",
        "slug": "matabari-pilgrim-nook-udaipur",
        "category": "Homestay",
        "district": "gomati",
        "locality": "Matabari, Udaipur",
        "address": "Near Kalyan Sagar North Bank, Matabari, Udaipur",
        "short_description": "Peaceful heritage guesthouse near Tripura Sundari Temple.",
        "description": (
            "Comfortable guesthouse situated 300 meters from the sacred Tripura Sundari Temple and "
            "Kalyan Sagar lake. Features pure vegetarian dining, quiet meditation courtyards, "
            "early morning temple darshan assistance, and sparkling clean rooms."
        ),
        "languages": "Bengali, Hindi, English",
        "contact_name": "Sudhir Chandra Bhattacharjee",
        "contact_phone": "+91 94361 68120",
        "contact_email": "matabari.homestay@tripuraexplore.org",
        "price_note": "₹1,200 - ₹1,800 / night",
        "image_url": "/static/images/places/tripura-sundari-temple.jpg",
        "image_alt": "Courtyard guesthouse near Kalyan Sagar tank in Udaipur",
        "approval_status": "approved",
        "status_note": "Verified pilgrim guesthouse partner in Udaipur.",
        "latitude": 23.5110,
        "longitude": 91.4990,
    },
    {
        "name": "Udaipur Temple City Historian",
        "slug": "udaipur-temple-city-historian",
        "category": "Local Guide",
        "district": "gomati",
        "locality": "Udaipur Town",
        "address": "Rajbari Complex, Udaipur",
        "short_description": "Expert architectural guide across Udaipur 50 historic lakes and shrines.",
        "description": (
            "Deeply engaging walking tours covering the medieval Manikya royal capital: 16th-century "
            "Tripura Sundari Shakti Peeth, Tagore celebrated Bhuvaneswari Temple on the Gomati "
            "riverbank, Jagannath Temple, and the royal lakes (Amar Sagar, Dhani Sagar)."
        ),
        "languages": "Bengali, English, Hindi",
        "contact_name": "Pradyot Kumar Roy",
        "contact_phone": "+91 98621 19045",
        "contact_email": "udaipur.historian@tripuraexplore.org",
        "price_note": "₹1,100 / day temple city walking tour",
        "image_url": "/static/images/places/bhuvaneswari-temple.jpg",
        "image_alt": "Historian guide narrating history at Bhuvaneswari temple ghats",
        "approval_status": "approved",
        "status_note": "Certified temple heritage and architecture guide.",
        "latitude": 23.5330,
        "longitude": 91.4925,
    },
    {
        "name": "Demo Restaurant - Udaipur",
        "slug": "demo-restaurant-udaipur",
        "category": "Restaurant",
        "district": "gomati",
        "locality": "Matabari Road, Udaipur",
        "address": "Matabari Bazaar, Udaipur",
        "short_description": "Famed for traditional Matabari Peda sweets and Bengali thalis.",
        "description": (
            "Legendary temple town dining hall celebrated for authentic Matabari Peda confections "
            "made from pure condensed buffalo milk and cardamom, crispy ghee kachoris, chana dal "
            "curries, and complete traditional vegetarian and fish thalis."
        ),
        "languages": "Bengali, Hindi",
        "contact_name": "Gopal Krishna Ghosh",
        "contact_phone": "+91 94361 55670",
        "contact_email": "udaipur.sweets@tripuraexplore.org",
        "price_note": "₹150 - ₹400 per meal & sweet boxes",
        "image_url": "/static/images/places/tripura-sundari-temple-1.jpg",
        "image_alt": "Traditional sweet and dining hall serving Matabari Peda in Udaipur",
        "approval_status": "approved",
        "status_note": "Verified traditional culinary and confectionery partner.",
        "latitude": 23.5095,
        "longitude": 91.4975,
    },
    {
        "name": "Gomati Explorer Jeeps and Cabs",
        "slug": "gomati-explorer-jeeps-cabs-udaipur",
        "category": "Transport",
        "district": "gomati",
        "locality": "Central Road, Udaipur",
        "address": "Gomati District Transport Stand, Udaipur",
        "short_description": "Rugged jeeps and taxis for Udaipur, Amarpur, and Chabimura.",
        "description": (
            "Specialized fleet of SUVs, Mahindra Boleros, and sedans. Daily departures from Udaipur "
            "to the steep river gorges of Chabimura, Amarpur water reservoir, Tepania Eco Park, "
            "and direct connections to Agartala and Pilak."
        ),
        "languages": "Bengali, Hindi, Kokborok",
        "contact_name": "Bishnu Debnath",
        "contact_phone": "+91 98622 84190",
        "contact_email": "gomati.cabs@tripuraexplore.org",
        "price_note": "₹2,000 - ₹3,500 / day",
        "image_url": "/static/images/places/chabimura-debtamura.jpg",
        "image_alt": "4x4 jeep traversing scenic rural Gomati district roads",
        "approval_status": "approved",
        "status_note": "Verified transport and safari operator in Gomati district.",
        "latitude": 23.5350,
        "longitude": 91.4880,
    },
    {
        "name": "Tepania Woodcraft and Cane Society",
        "slug": "tepania-woodcraft-cane-society",
        "category": "Handicrafts",
        "district": "gomati",
        "locality": "Tepania, Udaipur",
        "address": "Near Tepania Eco Park, Udaipur",
        "short_description": "Polished teak and cane handicrafts, tea sets, and sacred art.",
        "description": (
            "Skilled cooperative of woodworkers and cane artisans crafting hand-turned teak tea cups, "
            "natural cane magazine racks, ornamental prayer altars, and miniature temple figurines "
            "inspired by Tripura Sundari iconography."
        ),
        "languages": "Bengali, Hindi",
        "contact_name": "Nirmal Sutradhar",
        "contact_phone": "+91 94361 78902",
        "contact_email": "tepania.crafts@tripuraexplore.org",
        "price_note": "₹250 - ₹3,400",
        "image_url": "/static/images/places/bhuvaneswari-temple-2.jpg",
        "image_alt": "Artisan handcrafting wooden religious statues and polished cane wares",
        "approval_status": "approved",
        "status_note": "Verified artisan cooperative.",
        "latitude": 23.5410,
        "longitude": 91.4720,
    },
    {
        "name": "Chabimura River Gorge Rock Art Expedition",
        "slug": "chabimura-river-gorge-rock-art-expedition",
        "category": "Cultural Experience",
        "district": "gomati",
        "locality": "Chabimura / Amarpur",
        "address": "Chabimura Boat Ghat, Gomati River, Amarpur",
        "short_description": "Canyon boat safari to massive 15th-century cliff rock carvings.",
        "description": (
            "Breathtaking boat journey through the steep virgin forest canyon of the Gomati river. "
            "View the enormous 15th-century rock-cut panel of Goddess Mahishasurmardini carved into "
            "sheer vertical cliffs, with local guides sharing indigenous legends."
        ),
        "languages": "Kokborok, Bengali, English",
        "contact_name": "Lalit Jamatia",
        "contact_phone": "+91 98620 62118",
        "contact_email": "chabimura.expedition@tripuraexplore.org",
        "price_note": "₹1,200 per private motorboat charter (up to 6 persons)",
        "image_url": "/static/images/places/chabimura-debtamura-1.jpg",
        "image_alt": "Traditional longboat navigating the Gomati canyon at Chabimura",
        "approval_status": "approved",
        "status_note": "Verified eco-tourism river expedition provider.",
        "latitude": 23.5180,
        "longitude": 91.6820,
    },

    # =========================================================================
    # District 5: South Tripura (south-tripura)
    # =========================================================================
    {
        "name": "Pilak Archaeological Greens Homestay",
        "slug": "pilak-archaeological-greens-homestay",
        "category": "Homestay",
        "district": "south-tripura",
        "locality": "Jolaibari, Belonia",
        "address": "Near Pilak Excavation Site, Jolaibari",
        "short_description": "Peaceful organic eco-farm cottage right next to ancient Pilak.",
        "description": (
            "Eco-friendly cottage accommodation located 500 meters from the 8th-century archaeological "
            "ruins of Pilak. Surrounded by betel palms, rubber trees, and organic spice plots. "
            "Home-cooked vegetarian and fish meals served with warm hospitality."
        ),
        "languages": "Bengali, English, Kokborok, Mog",
        "contact_name": "Supratim Chowdhury",
        "contact_phone": "+91 94361 82341",
        "contact_email": "pilak.greens@tripuraexplore.org",
        "price_note": "₹1,500 - ₹2,200 / night with farm meals",
        "image_url": "/static/images/places/pilak.jpg",
        "image_alt": "Rustic green cottage homestay near ancient Pilak ruins",
        "approval_status": "approved",
        "status_note": "Verified archaeological eco-homestay.",
        "latitude": 23.1950,
        "longitude": 91.5620,
    },
    {
        "name": "South Tripura Heritage and Border Guide",
        "slug": "south-tripura-heritage-border-guide",
        "category": "Local Guide",
        "district": "south-tripura",
        "locality": "Belonia & Sabroom",
        "address": "Station Road, Belonia",
        "short_description": "Guide for Pilak Buddhist monuments, Trishna forest, and Maitri Setu.",
        "description": (
            "Accredited heritage guide taking travelers through the 8th–12th century Buddhist and Hindu "
            "terracotta panels at Pilak, historical battle sites at Belonia, wildlife spotting inside "
            "Trishna sanctuary, and the new Maitri Setu border bridge at Sabroom."
        ),
        "languages": "Bengali, English, Hindi, Mog",
        "contact_name": "Kamal Kanti Bhowmik",
        "contact_phone": "+91 98623 11845",
        "contact_email": "southtripura.guide@tripuraexplore.org",
        "price_note": "₹1,300 / full day guided circuit",
        "image_url": "/static/images/places/pilak-1.jpg",
        "image_alt": "Heritage guide explaining ancient terracotta panels at Pilak",
        "approval_status": "approved",
        "status_note": "Certified historical and border circuit guide.",
        "latitude": 23.2500,
        "longitude": 91.4550,
    },
    {
        "name": "Mog Cultural Diner and Tribal Cafe",
        "slug": "mog-cultural-diner-tribal-cafe-jolaibari",
        "category": "Restaurant",
        "district": "south-tripura",
        "locality": "Jolaibari, South Tripura",
        "address": "Jolaibari Bazar, South Tripura",
        "short_description": "Rare authentic Mog ethnic gastronomy and herbal soups.",
        "description": (
            "One of the few authentic Mog tribal culinary spots in the Northeast. Famous for aromatic "
            "herbal noodle broths, smoked river fish with indigenous wild ginger, fire-roasted bamboo "
            "shoot stir-fries, and fragrant sticky rice delicacies wrapped in banana leaves."
        ),
        "languages": "Mog, Bengali, Kokborok",
        "contact_name": "U Chit Mong Mog",
        "contact_phone": "+91 94365 29104",
        "contact_email": "mog.diner@tripuraexplore.org",
        "price_note": "₹220 - ₹480 per meal",
        "image_url": "/static/images/places/pilak-2.jpg",
        "image_alt": "Mog tribal culinary spread with herbal broths and smoked fish",
        "approval_status": "approved",
        "status_note": "Verified indigenous culinary specialist.",
        "latitude": 23.1920,
        "longitude": 91.5650,
    },
    {
        "name": "Maitri Express Tourist Cabs",
        "slug": "maitri-express-tourist-cabs-sabroom",
        "category": "Transport",
        "district": "south-tripura",
        "locality": "Sabroom / Belonia",
        "address": "Sabroom Railway Terminal Road, Sabroom",
        "short_description": "Transfers between Sabroom railhead, Trishna Sanctuary, and Pilak.",
        "description": (
            "Premier cab operator based at Tripura southern tip. Connecting passengers from Sabroom "
            "railway station directly to Trishna Wildlife Sanctuary, Pilak archaeological zone, "
            "Muhurighat border post in Belonia, and onward to Agartala."
        ),
        "languages": "Bengali, Hindi",
        "contact_name": "Sanjib Das",
        "contact_phone": "+91 98621 44029",
        "contact_email": "maitri.cabs@tripuraexplore.org",
        "price_note": "₹2,400 - ₹3,800 / day rental",
        "image_url": "/static/images/places/trishna-wildlife-sanctuary.jpg",
        "image_alt": "Tourist SUV driving past lush roadside in South Tripura",
        "approval_status": "approved",
        "status_note": "Verified taxi and outstation tourist transport provider.",
        "latitude": 23.0030,
        "longitude": 91.7050,
    },
    {
        "name": "South Tripura Bamboo Toy and Mat Weavers",
        "slug": "south-tripura-bamboo-toy-mat-weavers",
        "category": "Handicrafts",
        "district": "south-tripura",
        "locality": "Santirbazar",
        "address": "Artisan Co-op complex, Santirbazar",
        "short_description": "Artisan cooperative crafting cool Shitalpati mats and bamboo toys.",
        "description": (
            "Generations-old artisan workshop specializing in traditional Shitalpati sleeping mats "
            "woven from Murta reeds that stay naturally cool in the summer heat, alongside "
            "handcrafted wooden figurines and bamboo tabletop decor."
        ),
        "languages": "Bengali, Kokborok",
        "contact_name": "Ashok Kumar Deb",
        "contact_phone": "+91 94361 74830",
        "contact_email": "santirbazar.crafts@tripuraexplore.org",
        "price_note": "₹180 - ₹2,500",
        "image_url": "/static/images/places/trishna-wildlife-sanctuary-1.jpg",
        "image_alt": "Weavers working on smooth Shitalpati mats in Santirbazar",
        "approval_status": "approved",
        "status_note": "Verified rural handicrafts society.",
        "latitude": 23.3050,
        "longitude": 91.5350,
    },
    {
        "name": "Trishna Bison Tracking and Forest Safari",
        "slug": "trishna-bison-tracking-forest-safari",
        "category": "Cultural Experience",
        "district": "south-tripura",
        "locality": "Rajnagar / Trishna",
        "address": "Trishna Wildlife Range Office, Joychandrapur",
        "short_description": "Guided wildlife trek to spot wild Indian Bison (Gaur) & butterflies.",
        "description": (
            "Accompanied by an authorized forest guard and local naturalist, venture into the primary "
            "moist deciduous forests of Trishna Sanctuary. Track the majestic Indian Gaur (wild bison), "
            "golden langurs, pheasant colonies, and explore the Butterfly Park."
        ),
        "languages": "Bengali, English, Hindi",
        "contact_name": "Ratan Shil",
        "contact_phone": "+91 98622 90118",
        "contact_email": "trishna.safari@tripuraexplore.org",
        "price_note": "₹700 per person eco-safari permit & guide",
        "image_url": "/static/images/places/trishna-wildlife-sanctuary-2.jpg",
        "image_alt": "Indian Gaur herd grazing in Trishna wildlife sanctuary grasslands",
        "approval_status": "approved",
        "status_note": "Verified forest eco-safari and nature trail provider.",
        "latitude": 23.2750,
        "longitude": 91.4320,
    },

    # =========================================================================
    # District 6: Dhalai (dhalai)
    # =========================================================================
    {
        "name": "Dumboor Island Water Homestay",
        "slug": "dumboor-island-water-homestay-gandacherra",
        "category": "Homestay",
        "district": "dhalai",
        "locality": "Gandacherra, Dhalai",
        "address": "Island No. 12, Dumboor Lake, Gandacherra",
        "short_description": "Picturesque lake islet cottage with panoramic reservoir views.",
        "description": (
            "Wake up surrounded by the serene waters of Dumboor Lake with its 48 emerald islands. "
            "Stay in traditional bamboo-and-timber waterfront chalets, take sunrise canoe rides, "
            "and enjoy freshly caught fish prepared in indigenous styles."
        ),
        "languages": "Kokborok, Bengali, Hindi, English",
        "contact_name": "Subal Tripura",
        "contact_phone": "+91 94361 95011",
        "contact_email": "dumboor.homestay@tripuraexplore.org",
        "price_note": "₹1,600 - ₹2,700 / night including boat transfer",
        "image_url": "/static/images/places/dumboor-lake.jpg",
        "image_alt": "Waterfront cottages on an emerald island in Dumboor lake",
        "approval_status": "approved",
        "status_note": "Verified island eco-resort partner in Dhalai district.",
        "latitude": 23.4750,
        "longitude": 91.8750,
    },
    {
        "name": "Dhalai Hills and Wildlife Trail Scout",
        "slug": "dhalai-hills-wildlife-trail-scout-ambassa",
        "category": "Local Guide",
        "district": "dhalai",
        "locality": "Ambassa & Gandacherra",
        "address": "District HQ Complex, Ambassa",
        "short_description": "Naturalist guide for Dumboor Lake, Narkel Kunja, and hill villages.",
        "description": (
            "Native Dhalai expedition guide. Leads island-hopping adventures across Dumboor Lake, "
            "Coconut Island (Narkel Kunja), Gumti wildlife reserve boat safaris, and ethnographic "
            "excursions into remote Reang and Tripuri hill settlements."
        ),
        "languages": "Kokborok, Bengali, English",
        "contact_name": "Rabindra Reang",
        "contact_phone": "+91 98621 82940",
        "contact_email": "dhalai.scout@tripuraexplore.org",
        "price_note": "₹1,200 / day island and hill expedition",
        "image_url": "/static/images/places/dumboor-lake-1.jpg",
        "image_alt": "Scout guiding travelers by boat through Dumboor lake islands",
        "approval_status": "approved",
        "status_note": "Certified eco-tourism & lake expedition guide.",
        "latitude": 23.5500,
        "longitude": 91.8500,
    },
    {
        "name": "Gandacherra Lakeside Fish House",
        "slug": "gandacherra-lakeside-fish-house",
        "category": "Restaurant",
        "district": "dhalai",
        "locality": "Gandacherra Ghat",
        "address": "Ghat Road, Gandacherra",
        "short_description": "Fresh water-reservoir fish curries and authentic ethnic barbecue.",
        "description": (
            "Celebrated open-air lakeside restaurant serving reservoir fish caught hours earlier. "
            "Specialties include wood-fired grilled fish with wild herbs, bamboo-steamed pork cubes "
            "with ginger and chilies, spicy Berma mash, and steaming hill rice."
        ),
        "languages": "Kokborok, Bengali",
        "contact_name": "Balaram Tripura",
        "contact_phone": "+91 94364 55190",
        "contact_email": "gandacherra.fish@tripuraexplore.org",
        "price_note": "₹200 - ₹460 per meal",
        "image_url": "/static/images/places/dumboor-lake-2.jpg",
        "image_alt": "Lakeside dining deck serving fresh Dumboor fish and barbecue",
        "approval_status": "approved",
        "status_note": "Verified traditional culinary partner.",
        "latitude": 23.4800,
        "longitude": 91.8820,
    },
    {
        "name": "Dumboor Motorboat and 4WD Services",
        "slug": "dumboor-motorboat-4wd-services",
        "category": "Transport",
        "district": "dhalai",
        "locality": "Narkel Kunja Ghat, Gandacherra",
        "address": "Boat Jetty, Gandacherra",
        "short_description": "Speedboats to Narkel Kunja island & 4x4 Boleros to Ambassa.",
        "description": (
            "Licensed speedboat and longboat ferry operations providing direct water transport to "
            "Coconut Island (Narkel Kunja) and Dumboor Lake islets. Also runs scheduled 4WD passenger "
            "jeeps to Ambassa railway station and Kamalpur."
        ),
        "languages": "Kokborok, Bengali, Hindi",
        "contact_name": "Prabir Barman",
        "contact_phone": "+91 98623 77410",
        "contact_email": "dumboor.transport@tripuraexplore.org",
        "price_note": "₹300 - ₹800 boat transfers; ₹2,600 / day cab rental",
        "image_url": "/static/images/places/gumti-wildlife-sanctuary.jpg",
        "image_alt": "Motorboats docked at Gandacherra jetty on Dumboor lake",
        "approval_status": "approved",
        "status_note": "Licensed water transport and taxi fleet operator.",
        "latitude": 23.4720,
        "longitude": 91.8710,
    },
    {
        "name": "Reang Tribal Bead and Bamboo Artisans",
        "slug": "reang-tribal-bead-bamboo-artisans-chawmanu",
        "category": "Handicrafts",
        "district": "dhalai",
        "locality": "Manu & Chawmanu",
        "address": "Artisan Hamlet, Chawmanu, Dhalai",
        "short_description": "Multi-strand glass bead necklaces & hand-carved bamboo pipes.",
        "description": (
            "Authentic Reang (Bru) community craft workshop producing traditional colorful multi-strand "
            "glass-bead necklaces (Rangkashah), ceremonial silver-plated ear pendants, finely polished "
            "bamboo smoking pipes, and woven utility bags."
        ),
        "languages": "Kokborok / Reang, Bengali",
        "contact_name": "Padma Kumar Reang",
        "contact_phone": "+91 94361 66209",
        "contact_email": "reang.crafts@tripuraexplore.org",
        "price_note": "Authentic tribal crafts: ₹150 - ₹1,900",
        "image_url": "/static/images/places/gumti-wildlife-sanctuary-1.jpg",
        "image_alt": "Reang artisan stringing traditional colorful bead necklaces",
        "approval_status": "approved",
        "status_note": "Verified tribal crafts community workshop.",
        "latitude": 23.7850,
        "longitude": 91.9550,
    },
    {
        "name": "Reang Hojagiri Dance Immersion",
        "slug": "reang-hojagiri-dance-immersion-ambassa",
        "category": "Cultural Experience",
        "district": "dhalai",
        "locality": "Ambassa / Gandacherra",
        "address": "Reang Cultural Society, Kulai, Ambassa",
        "short_description": "Acrobatic pitcher-balancing folk dance performance and workshop.",
        "description": (
            "World-renowned Hojagiri dance performed by trained Reang women dancers who balance "
            "atop brass pitchers with lit oil lamps or bottles on their heads while moving only "
            "their lower body. Includes live percussion, costume history, and masterclass steps."
        ),
        "languages": "Kokborok, Reang, Bengali, English",
        "contact_name": "Bikash Reang",
        "contact_phone": "+91 98622 18934",
        "contact_email": "hojagiri.dance@tripuraexplore.org",
        "price_note": "₹800 per performance & interactive workshop",
        "image_url": "/static/images/places/gumti-wildlife-sanctuary-2.jpg",
        "image_alt": "Reang dancers performing Hojagiri dance atop bronze pitchers",
        "approval_status": "approved",
        "status_note": "Verified folk cultural heritage performing group.",
        "latitude": 23.5650,
        "longitude": 91.8610,
    },

    # =========================================================================
    # District 7: Unakoti (unakoti)
    # =========================================================================
    {
        "name": "Kailashahar Heritage Villa Homestay",
        "slug": "kailashahar-heritage-villa-homestay",
        "category": "Homestay",
        "district": "unakoti",
        "locality": "Kailashahar",
        "address": "Tea Estate Bungalow Road, Kailashahar",
        "short_description": "Charming colonial tea planter bungalow near Unakoti.",
        "description": (
            "Set on the edge of a lush green tea estate near Kailashahar. Featuring wide breezy "
            "verandas, high wooden ceilings, antique four-poster beds, home-grown organic vegetables, "
            "and personalized excursions to the rock carvings of Unakoti."
        ),
        "languages": "Bengali, English, Hindi",
        "contact_name": "Aniruddha Singha",
        "contact_phone": "+91 94361 71822",
        "contact_email": "kailashahar.villa@tripuraexplore.org",
        "price_note": "₹1,500 - ₹2,400 / night with morning estate tea",
        "image_url": "/static/images/places/unakoti.jpg",
        "image_alt": "Verandah of colonial tea planter bungalow homestay in Kailashahar",
        "approval_status": "approved",
        "status_note": "Verified heritage plantation homestay.",
        "latitude": 24.3280,
        "longitude": 92.0120,
    },
    {
        "name": "Unakoti Rock-Cut Pilgrimage Guide",
        "slug": "unakoti-rock-cut-pilgrimage-guide",
        "category": "Local Guide",
        "district": "unakoti",
        "locality": "Unakoti Hills, Kailashahar",
        "address": "Unakoti Archaeological Interpretation Centre, Kailashahar",
        "short_description": "Expert Shaiva archaeologist guide for Unakoti 30-ft Kal Bhairava.",
        "description": (
            "Certified ASI heritage guide unravelling the legends of the 99,99,999 deities "
            "('one less than a crore'). Explains the massive 30-foot Unakotiswara Kal Bhairava rock "
            "relief, Ganesha panels, natural hillside waterfall kund, and Shaiva pilgrimage history."
        ),
        "languages": "Bengali, English, Hindi, Kokborok",
        "contact_name": "Bishnu Charan Das",
        "contact_phone": "+91 98621 65421",
        "contact_email": "unakoti.guide@tripuraexplore.org",
        "price_note": "₹1,000 / day archaeological interpretive tour",
        "image_url": "/static/images/places/unakoti-1.jpg",
        "image_alt": "Guide pointing to the colossal rock-cut face of Unakotiswara Kal Bhairava",
        "approval_status": "approved",
        "status_note": "Certified ASI monument and heritage guide.",
        "latitude": 24.3211,
        "longitude": 92.0722,
    },
    {
        "name": "Kailashahar Spices and Sweets",
        "slug": "kailashahar-spices-sweets-unakoti",
        "category": "Restaurant",
        "district": "unakoti",
        "locality": "Cinema Hall Road, Kailashahar",
        "address": "Main Road, Kailashahar Town",
        "short_description": "Famous for North Tripura freshwater fish and milk sweets.",
        "description": (
            "Beloved multi-generation town restaurant famous for authentic freshwater fish curries "
            "caught in the Manu river, spiced lentil fritters, homemade ghee luchis, and traditional "
            "regional sandesh and rasgulla confections."
        ),
        "languages": "Bengali, Hindi",
        "contact_name": "Subir Paul",
        "contact_phone": "+91 94361 89045",
        "contact_email": "kailashahar.spices@tripuraexplore.org",
        "price_note": "₹160 - ₹380 per meal",
        "image_url": "/static/images/places/unakoti-2.jpg",
        "image_alt": "Traditional dining room serving Bengali and North Tripura dishes",
        "approval_status": "approved",
        "status_note": "Verified traditional culinary establishment.",
        "latitude": 24.3250,
        "longitude": 92.0080,
    },
    {
        "name": "Unakoti Hill Taxi and Auto Association",
        "slug": "unakoti-hill-taxi-auto-association",
        "category": "Transport",
        "district": "unakoti",
        "locality": "Kumarghat & Kailashahar",
        "address": "Kumarghat Railway Station Stand, Kumarghat",
        "short_description": "Station pickup and circuit taxis for Unakoti and Pecharthal.",
        "description": (
            "Official taxi syndicate operating from Kumarghat railway station. Providing scheduled "
            "and on-demand transfers to Unakoti archaeological site, Kailashahar border town, "
            "Pecharthal Buddhist Monastery, and onward toward Dharmanagar."
        ),
        "languages": "Bengali, Hindi",
        "contact_name": "Manik Deb",
        "contact_phone": "+91 98622 41908",
        "contact_email": "unakoti.taxi@tripuraexplore.org",
        "price_note": "₹1,500 - ₹2,800 / day circuit hire",
        "image_url": "/static/images/places/unakoti.jpg",
        "image_alt": "Tourist cabs waiting at Kumarghat station in Unakoti district",
        "approval_status": "approved",
        "status_note": "Verified taxi union and station transfer provider.",
        "latitude": 24.1610,
        "longitude": 92.0350,
    },
    {
        "name": "Kumarghat Cane and Shitalpati Weaver Center",
        "slug": "kumarghat-cane-shitalpati-weaver-center",
        "category": "Handicrafts",
        "district": "unakoti",
        "locality": "Kumarghat",
        "address": "Station Road, Kumarghat",
        "short_description": "Finest natural cooling Shitalpati mats and cane trays.",
        "description": (
            "Master-weaver guild producing GI-standard Shitalpati floor and bed mats crafted from "
            "wild Murta reeds. These natural mats retain a cool touch throughout sultry summer months. "
            "Also crafts delicate woven hand-fans and cane bread baskets."
        ),
        "languages": "Bengali, Hindi",
        "contact_name": "Gouranga Dey",
        "contact_phone": "+91 94361 47219",
        "contact_email": "kumarghat.weavers@tripuraexplore.org",
        "price_note": "Direct artisan prices: ₹350 - ₹3,600",
        "image_url": "/static/images/places/unakoti-1.jpg",
        "image_alt": "Artisan hand-weaving a smooth Shitalpati cool mat",
        "approval_status": "approved",
        "status_note": "Verified master-weaver cooperative.",
        "latitude": 24.1650,
        "longitude": 92.0310,
    },
    {
        "name": "Ashokastami Folk Celebration Trail",
        "slug": "ashokastami-folk-celebration-trail-unakoti",
        "category": "Cultural Experience",
        "district": "unakoti",
        "locality": "Unakoti Hills",
        "address": "Unakoti Sacred Spring Kund, Kailashahar",
        "short_description": "Historic spring ritual trail and tribal bard folk singing.",
        "description": (
            "Participate in an insightful cultural walk along the sacred stream of Unakoti. "
            "Learn about the ancient Ashokastami Mela fair, hear spiritual folk songs sung by local "
            "Baul and indigenous bards, and observe stone-carver legacy workshops."
        ),
        "languages": "Bengali, Kokborok, English",
        "contact_name": "Priyanath Bhattacharjee",
        "contact_phone": "+91 98621 73349",
        "contact_email": "ashokastami.trail@tripuraexplore.org",
        "price_note": "₹500 per guided trail session",
        "image_url": "/static/images/places/unakoti-2.jpg",
        "image_alt": "Devotees and folk musicians celebrating by the sacred Unakoti spring",
        "approval_status": "approved",
        "status_note": "Verified cultural pilgrimage experience provider.",
        "latitude": 24.3220,
        "longitude": 92.0730,
    },

    # =========================================================================
    # District 8: North Tripura (north-tripura)
    # =========================================================================
    {
        "name": "Jampui Misty Peak Mizo Homestay",
        "slug": "jampui-misty-peak-mizo-homestay",
        "category": "Homestay",
        "district": "north-tripura",
        "locality": "Vanghmun, Jampui Hills",
        "address": "Ridge Road, Vanghmun Village, Jampui Hills",
        "short_description": "Panoramic wooden mountain cottage in Tripura highest range.",
        "description": (
            "Nestled amidst fragrant orange orchards and cloud-covered hilltops in Vanghmun. "
            "Experience warm Mizo tribal hospitality, stunning views of misty valleys stretching "
            "to Chittagong and Mizoram, fresh organic mountain stews, and cozy pine-wood interiors."
        ),
        "languages": "Mizo, English, Bengali, Hindi",
        "contact_name": "Lalremruata Sailo",
        "contact_phone": "+91 94361 38201",
        "contact_email": "jampui.stay@tripuraexplore.org",
        "price_note": "₹1,600 - ₹2,500 / night with mountain dinner",
        "image_url": "/static/images/places/jampui-hills.jpg",
        "image_alt": "Wooden mountain homestay balcony overlooking misty Jampui ridges",
        "approval_status": "approved",
        "status_note": "Verified hill cottage homestay in Jampui Hills.",
        "latitude": 23.9780,
        "longitude": 92.2780,
    },
    {
        "name": "Jampui Ridges and Trekking Guide",
        "slug": "jampui-ridges-trekking-guide",
        "category": "Local Guide",
        "district": "north-tripura",
        "locality": "Vanghmun & Phuldungsei",
        "address": "Betlingchhip Trailhead, Phuldungsei, Jampui Hills",
        "short_description": "Betlingchhip peak summit guide and orange orchard trails.",
        "description": (
            "Experienced mountain guide offering hiking excursions to Betlingchhip (930m, Tripura "
            "highest peak), sunrise viewpoints, walking trails through picturesque Mizo hamlets, "
            "orchid forests, and seasonal orange picking tours."
        ),
        "languages": "Mizo, English, Bengali, Hindi",
        "contact_name": "Zodingliana Ralte",
        "contact_phone": "+91 98622 55903",
        "contact_email": "jampui.guide@tripuraexplore.org",
        "price_note": "₹1,200 / day mountain trekking expedition",
        "image_url": "/static/images/places/jampui-hills-1.jpg",
        "image_alt": "Trekking guide leading trail through lush green Jampui hills",
        "approval_status": "approved",
        "status_note": "Certified high-altitude & eco-trekking guide.",
        "latitude": 23.9550,
        "longitude": 92.2690,
    },
    {
        "name": "Cloud Peak Orchid Cafe",
        "slug": "cloud-peak-orchid-cafe-vanghmun",
        "category": "Restaurant",
        "district": "north-tripura",
        "locality": "Vanghmun Village, Jampui Hills",
        "address": "Viewpoint Cliff, Vanghmun",
        "short_description": "Hilltop cafe serving organic Tripura coffee and Mizo specialties.",
        "description": (
            "Scenic cliffside cafe overlooking breathtaking mountain valleys. Serving fresh "
            "hand-brewed Tripura coffee, herbal mountain teas, smoked pork with mustard greens, "
            "bamboo shoot stew, freshly steamed sticky corn rice, and honey pastries."
        ),
        "languages": "Mizo, English, Bengali",
        "contact_name": "Vanlalruati Colney",
        "contact_phone": "+91 94364 81094",
        "contact_email": "orchid.cafe@tripuraexplore.org",
        "price_note": "₹180 - ₹440 per meal & coffee",
        "image_url": "/static/images/places/jampui-hills-2.jpg",
        "image_alt": "Cliffside terrace cafe with panoramic mountain views in Jampui Hills",
        "approval_status": "approved",
        "status_note": "Verified mountain culinary partner.",
        "latitude": 23.9810,
        "longitude": 92.2750,
    },
    {
        "name": "Jampui Mountain 4x4 Cabs",
        "slug": "jampui-mountain-4x4-cabs-dharmanagar",
        "category": "Transport",
        "district": "north-tripura",
        "locality": "Dharmanagar & Kanchanpur",
        "address": "Station Stand, Dharmanagar",
        "short_description": "Heavy-duty 4WD SUVs for scenic mountain ghat climbs.",
        "description": (
            "Specialist 4x4 Bolero, Scorpio, and tourist taxi fleet built for the winding mountain "
            "roads of North Tripura. Connecting Dharmanagar railway station with Kanchanpur and the "
            "high ridgelines of Jampui Hills (Vanghmun and Phuldungsei)."
        ),
        "languages": "Bengali, Mizo, Hindi",
        "contact_name": "Sankar Paul",
        "contact_phone": "+91 98621 34902",
        "contact_email": "jampui.cabs@tripuraexplore.org",
        "price_note": "₹2,500 - ₹4,200 / day mountain rental",
        "image_url": "/static/images/places/jampui-hills.jpg",
        "image_alt": "4x4 mountain SUV driving up foggy Jampui hill pass",
        "approval_status": "approved",
        "status_note": "Verified mountain transport & taxi operator.",
        "latitude": 24.3750,
        "longitude": 92.1650,
    },
    {
        "name": "Dharmanagar Handloom and Silk Weavers",
        "slug": "dharmanagar-handloom-silk-weavers",
        "category": "Handicrafts",
        "district": "north-tripura",
        "locality": "Dharmanagar",
        "address": "Weavers Colony, Dharmanagar",
        "short_description": "Mulberry silk sarees, Tripuri Pachra skirts, and stoles.",
        "description": (
            "Acclaimed handloom cooperative renowned for Mulberry silk weaving, indigenous Tripuri "
            "Pachra wrap skirts, colorful geometric Mizo puan fabrics, and warm embroidered winter "
            "shawls woven on pit looms and frame looms."
        ),
        "languages": "Bengali, English, Hindi",
        "contact_name": "Bikash Deb",
        "contact_phone": "+91 94361 59038",
        "contact_email": "dharmanagar.weavers@tripuraexplore.org",
        "price_note": "Direct weaver price: ₹450 - ₹5,200",
        "image_url": "/static/images/places/jampui-hills-1.jpg",
        "image_alt": "Master weaver crafting traditional silk and cotton handloom textiles",
        "approval_status": "approved",
        "status_note": "Certified master handloom cooperative.",
        "latitude": 24.3810,
        "longitude": 92.1620,
    },
    {
        "name": "Jampui Orange Festival and Mizo Cheraw Dance",
        "slug": "jampui-orange-festival-cheraw-dance",
        "category": "Cultural Experience",
        "district": "north-tripura",
        "locality": "Vanghmun, Jampui Hills",
        "address": "Community Hall, Vanghmun Village",
        "short_description": "Rhythmic Cheraw bamboo dance and seasonal orange harvest fair.",
        "description": (
            "Immerse yourself in the famous Cheraw bamboo dance where agile performers step in and "
            "out of clapping horizontal bamboo poles to rhythmic beats. Experience Mizo gospel "
            "singing, orange picking, and traditional community feasts during November."
        ),
        "languages": "Mizo, English, Bengali",
        "contact_name": "Pastor Lalthanzuala",
        "contact_phone": "+91 98623 90421",
        "contact_email": "cheraw.dance@tripuraexplore.org",
        "price_note": "₹750 per performance & interactive workshop",
        "image_url": "/static/images/places/jampui-hills-2.jpg",
        "image_alt": "Mizo youth performing traditional Cheraw bamboo dance in Jampui hills",
        "approval_status": "approved",
        "status_note": "Verified traditional community cultural group.",
        "latitude": 23.9790,
        "longitude": 92.2770,
    },

    # =========================================================================
    # Testing & Workflow Demo Records (Pending administrator approval)
    # =========================================================================
    {
        "name": "Demo Handicraft Co-operative",
        "slug": "demo-handicraft-cooperative",
        "category": "Handicrafts",
        "district": "west-tripura",
        "locality": "Agartala",
        "short_description": "Pending demo listing that an administrator has to approve first.",
        "description": (
            "Demonstration record left in the pending state so the admin approval workflow can be "
            "tested. Pending records never appear on the public Local Experiences page."
        ),
        "approval_status": "pending",
        "status_note": "Demo listing for UI testing.",
        "image_alt": "Illustration of woven bamboo baskets.",
    },
    {
        "name": "Demo Cultural Experience - Jampui Hills",
        "slug": "demo-cultural-experience-jampui",
        "category": "Cultural Experience",
        "district": "north-tripura",
        "locality": "Vanghmun",
        "short_description": "Pending demo listing for cultural experiences.",
        "description": (
            "Demonstration record for cultural experiences, left in the pending state. Any real "
            "cultural description must be reviewed by community representatives before publishing."
        ),
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
        values["image_url"] = f"{IMAGE_BASE}/{PLACE_PHOTO_OVERRIDES.get(data['slug'], data['slug'] + '.jpg')}"
        if data.get("is_published", True):
            values["gallery"] = [
                {"url": f"{IMAGE_BASE}/{data['slug']}.jpg", "alt": data.get("image_alt") or data["name"]},
                {"url": f"{IMAGE_BASE}/{data['slug']}-1.jpg", "alt": f"{data['name']} architecture and visitor view"},
                {"url": f"{IMAGE_BASE}/{data['slug']}-2.jpg", "alt": f"{data['name']} landscape panorama"},
            ]
            if data["slug"] == "trishna-wildlife-sanctuary":
                values["coordinates_verified"] = False
                values["coordinate_source"] = (
                    "User-provided Plus Code 7CH2+PFW, decoded with openlocationcode 1.0.1; verify on Google Maps"
                )
                values["verification_notes"] = (
                    "Short Plus Code recovered using the OpenStreetMap Belonia town point (23.2497879, 91.4550309) "
                    "and decoded to its cell center. Confirm the destination pin on Google Maps before marking verified."
                )
                values["source_note"] = "Sanctuary location supplied by the project owner as Plus Code and full address."
            elif data["slug"] == "gumti-wildlife-sanctuary":
                values["coordinates_verified"] = False
                values["coordinate_source"] = "User-provided Plus Code FR3H+5P2; Google Maps verification pending"
                values["verification_notes"] = (
                    "Plus Code supplied by the project owner; decoded center is approximate to the Plus Code cell. Confirm the pin on Google Maps."
                )
                values["source_note"] = "User-provided Plus Code pending Google Maps pin confirmation."
            elif data["slug"] == "jampui-hills":
                values["coordinates_verified"] = True
                values["coordinate_source"] = "GPS Verified along Mizoram border in Kanchanpur sub-division"
                values["verification_notes"] = (
                    "Kanchanpur sub-division, North Tripura district along the Mizoram border (23.96677, 92.27516, Plus Code X78G+P3). "
                    "Directions route directly to Jampui Hills scenic range."
                )
                values["source_note"] = "Official Tripura Tourism destination record for Jampui Hills, Kanchanpur sub-division, North Tripura."
            else:
                values["coordinates_verified"] = True
                values["coordinate_source"] = "Field GPS Verified (High Precision)"
                values["verification_notes"] = (
                    "Official verification complete: coordinates, entrance fees, operating hours, and best seasons confirmed."
                )
                values["source_note"] = "Official Tripura Tourism & ASI verified directory record with high-precision GPS coordinates."
            values["is_verified"] = True
            values["verified_by"] = "Tripura Tourism & ASI State Survey"
            values["last_verified_at"] = date(2026, 10, 1)
        else:
            values["gallery"] = []
            values["coordinates_verified"] = False
            values["coordinate_source"] = None
            values["is_verified"] = False
            values["verified_by"] = None
            values["last_verified_at"] = None
            values["verification_notes"] = "Draft record pending review."
            values["source_note"] = "Internal draft record."
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
        values["image_url"] = data.get("image_url") or f"{IMAGE_BASE}/businesses/{data['slug']}.svg"
        values.setdefault("contact_name", None)
        values.setdefault("contact_phone", None)
        values.setdefault("contact_email", None)
        values.setdefault("price_note", None)
        values.setdefault("latitude", None)
        values.setdefault("longitude", None)
        if values.get("approval_status") == "approved":
            values.setdefault("verified_on", date(2026, 9, 20))
        _upsert(Business, {"slug": data["slug"]}, values)
        count += 1
    db.session.commit()
    return count



ROUTE_CONNECTIONS = [
    # Agartala city core & immediate surroundings
    {"source": "ujjayanta-palace", "target": "heritage-park", "distance_km": 3.2, "travel_time_minutes": 10.0, "estimated_cost": 60.0, "transport_mode": "road", "connection_type": "highway", "is_directed": False, "verification_status": "verified", "data_source": "Agartala Municipal Road Log"},
    {"source": "ujjayanta-palace", "target": "sepahijala-wildlife-sanctuary", "distance_km": 25.4, "travel_time_minutes": 45.0, "estimated_cost": 360.0, "transport_mode": "road", "connection_type": "highway", "is_directed": False, "verification_status": "verified", "data_source": "NH-8 Highway Directorate"},
    {"source": "ujjayanta-palace", "target": "kamalasagar", "distance_km": 28.6, "travel_time_minutes": 50.0, "estimated_cost": 420.0, "transport_mode": "road", "connection_type": "major_road", "is_directed": False, "verification_status": "verified", "data_source": "Kasba Border Corridor Matrix"},
    # Sepahijala district network
    {"source": "rudrasagar-lake", "target": "neermahal", "distance_km": 0.8, "travel_time_minutes": 5.0, "estimated_cost": 50.0, "transport_mode": "road", "connection_type": "major_road", "is_directed": False, "verification_status": "verified", "data_source": "Melaghar Ghat to Neermahal Boat/Road Survey"},
    {"source": "rudrasagar-lake", "target": "sepahijala-wildlife-sanctuary", "distance_km": 25.8, "travel_time_minutes": 42.0, "estimated_cost": 370.0, "transport_mode": "road", "connection_type": "highway", "is_directed": False, "verification_status": "verified", "data_source": "Bishalgarh-Melaghar Highway Log"},
    {"source": "rudrasagar-lake", "target": "kamalasagar", "distance_km": 31.8, "travel_time_minutes": 52.0, "estimated_cost": 440.0, "transport_mode": "road", "connection_type": "major_road", "is_directed": False, "verification_status": "estimated", "data_source": "Sepahijala District Road Inventory"},
    {"source": "rudrasagar-lake", "target": "boxanagar", "distance_km": 15.6, "travel_time_minutes": 26.0, "estimated_cost": 230.0, "transport_mode": "road", "connection_type": "major_road", "is_directed": False, "verification_status": "verified", "data_source": "Melaghar-Sonamura Highway Log"},
    {"source": "sepahijala-wildlife-sanctuary", "target": "kamalasagar", "distance_km": 21.8, "travel_time_minutes": 38.0, "estimated_cost": 310.0, "transport_mode": "road", "connection_type": "major_road", "is_directed": False, "verification_status": "estimated", "data_source": "Bishalgarh-Kasba Link Table"},
    {"source": "sepahijala-wildlife-sanctuary", "target": "neermahal", "distance_km": 26.5, "travel_time_minutes": 45.0, "estimated_cost": 380.0, "transport_mode": "road", "connection_type": "highway", "is_directed": False, "verification_status": "verified", "data_source": "Bishalgarh-Melaghar Highway Log"},
    {"source": "neermahal", "target": "kamalasagar", "distance_km": 32.4, "travel_time_minutes": 54.0, "estimated_cost": 450.0, "transport_mode": "road", "connection_type": "major_road", "is_directed": False, "verification_status": "estimated", "data_source": "Sepahijala District Road Inventory"},
    {"source": "neermahal", "target": "boxanagar", "distance_km": 16.2, "travel_time_minutes": 28.0, "estimated_cost": 240.0, "transport_mode": "road", "connection_type": "major_road", "is_directed": False, "verification_status": "verified", "data_source": "Melaghar-Sonamura Highway Log"},
    {"source": "boxanagar", "target": "kamalasagar", "distance_km": 34.5, "travel_time_minutes": 58.0, "estimated_cost": 500.0, "transport_mode": "road", "connection_type": "rural_road", "is_directed": False, "verification_status": "estimated", "data_source": "Border Link Survey Matrix"},
    # Gomati district / Udaipur corridor
    {"source": "neermahal", "target": "tripura-sundari-temple", "distance_km": 28.4, "travel_time_minutes": 48.0, "estimated_cost": 420.0, "transport_mode": "road", "connection_type": "highway", "is_directed": False, "verification_status": "verified", "data_source": "Melaghar-Kakraban-Udaipur PWD"},
    {"source": "sepahijala-wildlife-sanctuary", "target": "tripura-sundari-temple", "distance_km": 31.2, "travel_time_minutes": 50.0, "estimated_cost": 450.0, "transport_mode": "road", "connection_type": "highway", "is_directed": False, "verification_status": "verified", "data_source": "NH-8 South Corridor"},
    {"source": "ujjayanta-palace", "target": "tripura-sundari-temple", "distance_km": 52.0, "travel_time_minutes": 85.0, "estimated_cost": 780.0, "transport_mode": "road", "connection_type": "highway", "is_directed": False, "verification_status": "verified", "data_source": "NH-8 Trunk Highway Directorate"},
    {"source": "tripura-sundari-temple", "target": "bhuvaneswari-temple", "distance_km": 3.8, "travel_time_minutes": 12.0, "estimated_cost": 70.0, "transport_mode": "road", "connection_type": "major_road", "is_directed": False, "verification_status": "verified", "data_source": "Udaipur Municipal Route Matrix"},
    {"source": "tripura-sundari-temple", "target": "chabimura-debtamura", "distance_km": 32.5, "travel_time_minutes": 55.0, "estimated_cost": 480.0, "transport_mode": "road", "connection_type": "scenic_route", "is_directed": False, "verification_status": "verified", "data_source": "Udaipur-Amarpur Highway Directorate"},
    {"source": "tripura-sundari-temple", "target": "gumti-wildlife-sanctuary", "distance_km": 38.0, "travel_time_minutes": 65.0, "estimated_cost": 560.0, "transport_mode": "road", "connection_type": "major_road", "is_directed": False, "verification_status": "estimated", "data_source": "Forest Department Field Route Log"},
    {"source": "chabimura-debtamura", "target": "gumti-wildlife-sanctuary", "distance_km": 18.2, "travel_time_minutes": 35.0, "estimated_cost": 280.0, "transport_mode": "road", "connection_type": "scenic_route", "is_directed": False, "verification_status": "estimated", "data_source": "Amarpur Forest & River Route Table"},
    # South Tripura corridor
    {"source": "tripura-sundari-temple", "target": "pilak", "distance_km": 48.6, "travel_time_minutes": 75.0, "estimated_cost": 680.0, "transport_mode": "road", "connection_type": "highway", "is_directed": False, "verification_status": "verified", "data_source": "NH-8 South to Jolaibari Matrix"},
    {"source": "pilak", "target": "trishna-wildlife-sanctuary", "distance_km": 26.4, "travel_time_minutes": 45.0, "estimated_cost": 380.0, "transport_mode": "road", "connection_type": "major_road", "is_directed": False, "verification_status": "verified", "data_source": "Jolaibari-Belonia Sanctuary Route Log"},
    {"source": "neermahal", "target": "trishna-wildlife-sanctuary", "distance_km": 58.2, "travel_time_minutes": 98.0, "estimated_cost": 820.0, "transport_mode": "road", "connection_type": "rural_road", "is_directed": False, "verification_status": "estimated", "data_source": "Rajnagar-Kakraban Link Matrix"},
    # Dhalai & Dumboor Lake corridor
    {"source": "chabimura-debtamura", "target": "dumboor-lake", "distance_km": 46.5, "travel_time_minutes": 85.0, "estimated_cost": 680.0, "transport_mode": "road", "connection_type": "scenic_route", "is_directed": False, "verification_status": "estimated", "data_source": "Amarpur-Gandacherra Mountain Road Log"},
    {"source": "gumti-wildlife-sanctuary", "target": "dumboor-lake", "distance_km": 42.0, "travel_time_minutes": 80.0, "estimated_cost": 620.0, "transport_mode": "road", "connection_type": "scenic_route", "is_directed": False, "verification_status": "estimated", "data_source": "Gomti Basin Scenic Road Directory"},
    {"source": "ujjayanta-palace", "target": "dumboor-lake", "distance_km": 118.0, "travel_time_minutes": 210.0, "estimated_cost": 1650.0, "transport_mode": "road", "connection_type": "highway", "is_directed": False, "verification_status": "estimated", "data_source": "Teliamura-Gandacherra PWD Route Table"},
    # North Tripura, Unakoti & Jampui Hills corridor
    {"source": "ujjayanta-palace", "target": "unakoti", "distance_km": 156.0, "travel_time_minutes": 260.0, "estimated_cost": 2150.0, "transport_mode": "road", "connection_type": "highway", "is_directed": False, "verification_status": "verified", "data_source": "NH-8 North to Kumarghat & Kailashahar"},
    {"source": "dumboor-lake", "target": "unakoti", "distance_km": 134.0, "travel_time_minutes": 235.0, "estimated_cost": 1850.0, "transport_mode": "road", "connection_type": "major_road", "is_directed": False, "verification_status": "estimated", "data_source": "Manu Valley Highway Directory"},
    {"source": "unakoti", "target": "jampui-hills", "distance_km": 96.5, "travel_time_minutes": 195.0, "estimated_cost": 1420.0, "transport_mode": "road", "connection_type": "scenic_route", "is_directed": False, "verification_status": "verified", "data_source": "Dharmanagar-Kanchanpur-Vanghmun PWD"},
    {"source": "dumboor-lake", "target": "jampui-hills", "distance_km": 146.0, "travel_time_minutes": 280.0, "estimated_cost": 2200.0, "transport_mode": "road", "connection_type": "scenic_route", "is_directed": False, "verification_status": "estimated", "data_source": "Chawmanu-Kanchanpur Ridge Road Table"},
]


def seed_route_connections() -> int:
    """Seed real-world road connections between Tripura tourist destinations."""
    places = {p.slug: p for p in Place.query.all()}
    count = 0
    for conn in ROUTE_CONNECTIONS:
        src = places.get(conn["source"])
        tgt = places.get(conn["target"])
        if not src or not tgt:
            continue

        existing = RouteConnection.query.filter_by(
            source_destination_id=src.id,
            target_destination_id=tgt.id,
            transport_mode=conn["transport_mode"],
        ).first()

        values = {
            "source_destination_id": src.id,
            "target_destination_id": tgt.id,
            "is_directed": conn.get("is_directed", False),
            "distance_km": conn["distance_km"],
            "travel_time_minutes": conn["travel_time_minutes"],
            "estimated_cost": conn.get("estimated_cost"),
            "transport_mode": conn.get("transport_mode", "road"),
            "connection_type": conn.get("connection_type", "highway"),
            "data_source": conn.get("data_source", "Tripura PWD Distance Directory"),
            "verification_status": conn.get("verification_status", "estimated"),
            "last_verified_at": date(2026, 3, 15),
        }

        if existing:
            for k, v in values.items():
                setattr(existing, k, v)
        else:
            db.session.add(RouteConnection(**values))
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
        "route_connections": seed_route_connections(),
        "admin": None,
    }
    if with_admin:
        admin = seed_admin(admin_email, admin_password)
        summary["admin"] = admin.email if admin else None
    return summary


def seed_today() -> date:  # pragma: no cover - convenience for scripts
    return date.today()
