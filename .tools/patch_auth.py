import io
path = "app/routes/auth.py"
text = io.open(path, encoding="utf-8").read()
old = """    trips = current_user.itineraries.order_by_by_created().all() if hasattr(current_user.itineraries, "order_by_by_created") else (
        current_user.itineraries.order_by(None).all()
    )
"""
new = """    from app.models import Itinerary

    trips = (
        Itinerary.query.filter_by(user_id=current_user.id)
        .order_by(Itinerary.updated_at.desc())
        .all()
    )
"""
assert old in text
text = text.replace(old, new, 1)
io.open(path, "w", encoding="utf-8", newline="\n").write(text)
print("profile query fixed")
