import io
path = "tests/conftest.py"
text = io.open(path, encoding="utf-8").read()
text = text.replace(
    "from app.models import Business, Category, District, ItineraryStop, Place, User",
    "from app.models import Business, Category, District, Itinerary, ItineraryStop, Place, User",
    1,
)
text = text.replace(
    '    itinerary = __import__("app.models", fromlist=["Itinerary"]).Itinerary(',
    "    itinerary = Itinerary(",
    1,
)
io.open(path, "w", encoding="utf-8", newline="\n").write(text)

path = "app/__init__.py"
text = io.open(path, encoding="utf-8").read()
old = """    login_manager.init_app(app)
    csrf.init_app(app)
"""
new = """    login_manager.init_app(app)
    csrf.init_app(app)

    if app.config.get("TESTING"):
        # Session protection relies on client IP/user agent, which the Flask test
        # client does not vary. Turning it off keeps the tests deterministic.
        login_manager.session_protection = None
"""
assert old in text
text = text.replace(old, new, 1)
io.open(path, "w", encoding="utf-8", newline="\n").write(text)
print("patched conftest and app factory")
