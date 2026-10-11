import sys
sys.path.insert(0, ".")
from app import create_app

app = create_app("development")
client = app.test_client()
r = client.post("/api/itineraries", json={"duration_days": 2, "starting_location": "Agartala", "interests": ["Lakes"]})
print(r.status_code)
print(r.data[:600])