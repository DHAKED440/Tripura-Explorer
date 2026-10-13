"""Editorial overview of Tripura's festivals, crafts and food.

This content is a *brief editorial overview* written for the prototype. It is
kept in one module instead of being typed into templates, and every entry is
flagged ``community_reviewed=False`` until a community representative or the
state culture department has approved the wording.

Nothing here is a bookable provider - the Local Experiences directory handles
that, and only approved records are shown publicly.
"""

CULTURAL_HIGHLIGHTS = [
    {
        "kind": "Festival",
        "name": "Kharchi Puja",
        "month": "July",
        "place": "Old Agartala (Chaturdash Devta temple)",
        "summary": (
            "A week-long worship of the fourteen deities, attended by large numbers of "
            "pilgrims in Old Agartala."
        ),
        "community_reviewed": False,
    },
    {
        "kind": "Festival",
        "name": "Garia Puja",
        "month": "April",
        "place": "Across Tripura",
        "summary": (
            "A harvest festival of the indigenous communities in which the Garia deity is "
            "worshipped with music and dance."
        ),
        "community_reviewed": False,
    },
    {
        "kind": "Festival",
        "name": "Ker Puja",
        "month": "July",
        "place": "Across Tripura",
        "summary": (
            "A traditional festival in which the guardian deity of the community, Ker, is "
            "worshipped for the well-being of the area."
        ),
        "community_reviewed": False,
    },
    {
        "kind": "Festival",
        "name": "Durga Puja",
        "month": "September / October",
        "place": "Agartala and district towns",
        "summary": (
            "Bengali Durga Puja with community pandals; the largest celebrations are in "
            "Agartala and Udaipur."
        ),
        "community_reviewed": False,
    },
    {
        "kind": "Festival",
        "name": "Ashokastami Mela",
        "month": "April",
        "place": "Unakoti Hills (Kailashahar)",
        "summary": (
            "A historic hill pilgrimage and fair held at the sacred stream of Unakoti, drawing "
            "thousands of devotees for sacred bathing amidst rock-cut sculptures."
        ),
        "community_reviewed": False,
    },
    {
        "kind": "Festival",
        "name": "Jampui Orange Festival",
        "month": "November",
        "place": "Vanghmun (Jampui Hills)",
        "summary": (
            "Annual orange harvest celebrations featuring vibrant Mizo folk music, dance, "
            "handicrafts, and community feasts atop Tripura's highest ridge."
        ),
        "community_reviewed": False,
    },
    {
        "kind": "Festival",
        "name": "Neermahal Boat Race & Carnival",
        "month": "September",
        "place": "Rudrasagar Lake (Melaghar)",
        "summary": (
            "Traditional water festival where long wooden snake boats compete on Rudrasagar "
            "lake against the majestic backdrop of Neermahal water palace."
        ),
        "community_reviewed": False,
    },
    {
        "kind": "Craft",
        "name": "Bamboo and cane craft",
        "month": "All year",
        "place": "Districts across Tripura",
        "summary": (
            "Baskets, mats, furniture and decorative items woven from bamboo and cane by "
            "artisan families."
        ),
        "community_reviewed": False,
    },
    {
        "kind": "Craft",
        "name": "Handloom: Risa and Pachra",
        "month": "All year",
        "place": "Handloom clusters across Tripura",
        "summary": (
            "Risa and Pachra are traditional handwoven cloths of the indigenous communities, "
            "sold through handloom outlets and weaving co-operatives."
        ),
        "community_reviewed": False,
    },
    {
        "kind": "Craft",
        "name": "Shitalpati Natural Cool Mats",
        "month": "All year",
        "place": "Kumarghat & Santirbazar",
        "summary": (
            "Fine handwoven cooling mats made from wild Murta reeds, prized across the "
            "region for retaining natural coolness during the hot summer season."
        ),
        "community_reviewed": False,
    },
    {
        "kind": "Food",
        "name": "Mui Borok and Berma",
        "month": "All year",
        "place": "Local eateries across Tripura",
        "summary": (
            "Mui Borok is the traditional cuisine of the indigenous communities; Berma is "
            "fermented fish, a common flavouring. Dishes are usually cooked without oil."
        ),
        "community_reviewed": False,
    },
    {
        "kind": "Food",
        "name": "Chakhwi and Bangui Rice",
        "month": "All year",
        "place": "Traditional Tripuri kitchens",
        "summary": (
            "Chakhwi is a signature bamboo shoot and pork/chicken curry cooked with natural alkali; "
            "Bangui is sun-dried glutinous rice steamed inside aromatic herbal banana leaves."
        ),
        "community_reviewed": False,
    },
    {
        "kind": "Food",
        "name": "Matabari Peda",
        "month": "All year",
        "place": "Udaipur (Gomati district)",
        "summary": (
            "Iconic milk sweet prepared by slow-simmering pure buffalo milk with sugar and cardamom, "
            "offered as prasad at the 500-year-old Tripura Sundari temple."
        ),
        "community_reviewed": False,
    },
    {
        "kind": "Performance",
        "name": "Hojagiri dance",
        "month": "Festivals such as Hojagiri / Garia",
        "place": "Bru (Reang) communities",
        "summary": (
            "A balancing dance in which performers balance on the edge of a pitcher while "
            "moving a bottle on the head."
        ),
        "community_reviewed": False,
    },
    {
        "kind": "Performance",
        "name": "Lebang Boomani dance",
        "month": "Harvest season (Autumn)",
        "place": "Khowai & West Tripura",
        "summary": (
            "Charming harvest folk dance where Tripuri youth mimic the catching of festive insects "
            "using rhythmic bamboo clappers (Tok-ka) to cheerful folk music."
        ),
        "community_reviewed": False,
    },
    {
        "kind": "Performance",
        "name": "Cheraw bamboo dance",
        "month": "Orange festival & celebrations",
        "place": "Jampui Hills (North Tripura)",
        "summary": (
            "Fast-paced traditional bamboo dance where skilled Mizo dancers leap in and out of "
            "rhythmically clapping horizontal bamboo poles."
        ),
        "community_reviewed": False,
    },
]


def grouped_highlights() -> dict[str, list[dict]]:
    """Highlights grouped by ``kind`` for the Local Experiences page."""
    grouped: dict[str, list[dict]] = {}
    for item in CULTURAL_HIGHLIGHTS:
        grouped.setdefault(item["kind"], []).append(item)
    return grouped