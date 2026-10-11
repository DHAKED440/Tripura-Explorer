"""Database models.

Importing this package makes every model available from ``app.models`` so that
``db.create_all()`` and the migrations environment can discover them.
"""
from app.models.business import Business, Inquiry
from app.models.category import Category
from app.models.district import District
from app.models.feedback import CorrectionReport
from app.models.itinerary import Itinerary, ItineraryStop
from app.models.place import Place
from app.models.user import Favorite, User

__all__ = [
    "Business",
    "Category",
    "CorrectionReport",
    "District",
    "Favorite",
    "Inquiry",
    "Itinerary",
    "ItineraryStop",
    "Place",
    "User",
]