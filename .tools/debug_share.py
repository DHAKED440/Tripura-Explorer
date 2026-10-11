import sys
sys.path.insert(0, ".")
from app import create_app
from app.extensions import db
from app.models import Itinerary, ItineraryStop, Place, User

app = create_app("testing")
with app.app_context():
    db.create_all()
    from app.seed_data import seed_categories, seed_districts, seed_places
    seed_categories(); seed_districts(); seed_places()
    user = User(name="T", email="t@example.com", role="user"); user.set_password("password123")
    db.session.add(user); db.session.commit()
    trip = Itinerary(user_id=user.id, title="T", duration_days=2, starting_location="Agartala")
    db.session.add(trip); db.session.commit()
    print("is_shared:", repr(trip.is_shared), "token:", repr(trip.share_token))
    anonymous = app.test_client()
    response = anonymous.get(f"/api/itineraries/{trip.id}")
    print("anonymous status:", response.status_code, response.get_json())