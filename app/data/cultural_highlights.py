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
]


def grouped_highlights() -> dict[str, list[dict]]:
    """Highlights grouped by ``kind`` for the Local Experiences page."""
    grouped: dict[str, list[dict]] = {}
    for item in CULTURAL_HIGHLIGHTS:
        grouped.setdefault(item["kind"], []).append(item)
    return grouped