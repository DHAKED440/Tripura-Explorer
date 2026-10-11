import re
import sys

sys.path.insert(0, ".")
from app import create_app

app = create_app("development")
client = app.test_client()

page = client.get("/trip-planner")
csrf = re.search(rb'name="csrf-token" content="([^"]+)"', page.data).group(1).decode()
headers = {"X-CSRFToken": csrf}

paths = [
    "/", "/explore", "/explore?q=neermahal", "/explore?category=nature&district=gomati",
    "/explore?category=nonsense", "/explore?page=99", "/places/neermahal",
    "/places/neermahal-boat-ghat-draft", "/places/does-not-exist", "/map", "/api/places/map",
    "/api/places/map?category=lakes", "/api/featured-places", "/api/places", "/trip-planner",
    "/experiences", "/experiences?category=Homestay", "/experiences/demo-homestay-bishalgarh",
    "/experiences/demo-handicraft-cooperative", "/about", "/my-trips", "/profile", "/admin",
    "/api/itineraries/1", "/static/css/style.css", "/static/images/hero-tripura.svg",
]
for path in paths:
    response = client.get(path)
    print(response.status_code, path, len(response.data))

form = {
    "csrf_token": csrf, "duration_days": "2", "starting_location": "Agartala",
    "interests": ["Nature", "Lakes", "Heritage"], "budget": "8000", "travel_date": "2026-12-01",
}
post = client.post("/trip-planner", data=form)
print("POST /trip-planner ->", post.status_code, "has plan:", b"Suggested plan" in post.data)

bad = client.post("/trip-planner", data={"csrf_token": csrf, "duration_days": "9", "starting_location": "A", "interests": []})
print("POST invalid ->", bad.status_code, "error text:", b"Please fix the following" in bad.data)

api = client.post("/api/itineraries", json={"duration_days": 2, "starting_location": "Agartala", "interests": ["Lakes", "Temples"]}, headers=headers)
print("POST /api/itineraries ->", api.status_code, (api.get_json() or {}).get("plan", {}).get("matched_count"))

save = client.post("/api/itineraries", json={"duration_days": 1, "starting_location": "Agartala", "interests": ["Lakes"], "save": True}, headers=headers)
print("POST save without login ->", save.status_code, (save.get_json() or {}).get("error"))

report = client.post("/places/neermahal/report", data={"csrf_token": csrf, "message": "The fee shown is wrong.", "reporter_email": "visitor@example.com"})
print("POST report ->", report.status_code, report.headers.get("Location"))

inquiry = client.post("/api/inquiries", json={"business_id": 1, "name": "Test Visitor", "email": "v@example.com", "message": "Please share availability."}, headers=headers)
print("POST /api/inquiries ->", inquiry.status_code, (inquiry.get_json() or {}).get("status"))