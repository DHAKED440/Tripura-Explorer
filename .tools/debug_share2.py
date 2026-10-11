import sys
sys.path.insert(0, ".")
from app import create_app
from app.extensions import db
from app.models import Itinerary, User

app = create_app("testing")
with app.app_context():
    db.create_all()
    from app.seed_data import seed_categories, seed_districts, seed_places
    seed_categories(); seed_districts(); seed_places()
    owner = User(name="Owner", email="owner@example.com", role="user"); owner.set_password("password123")
    other = User(name="Other", email="other@example.com", role="user"); other.set_password("password123")
    db.session.add_all([owner, other]); db.session.commit()
    trip = Itinerary(user_id=owner.id, title="Private", duration_days=2, starting_location="Agartala")
    db.session.add(trip); db.session.commit()
    trip_id = trip.id
    print("trip", trip_id, "owner", owner.id, "is_shared", repr(trip.is_shared))

client1 = app.test_client()
r = client1.post("/auth/login", data={"email": "owner@example.com", "password": "password123"})
print("login:", r.status_code)
print("client1 GET:", client1.get(f"/api/itineraries/{trip_id}").status_code)

client2 = app.test_client()
resp = client2.get(f"/api/itineraries/{trip_id}")
print("client2 GET:", resp.status_code, resp.get_json())
print("client2 cookies:", list(client2.cookie_jar))
print("client1 cookies:", list(client1.cookie_jar))