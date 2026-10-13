"""Shared pytest fixtures.

Every test runs against a fresh in-memory SQLite database that is seeded with
the same repeatable prototype data the development server uses. No test touches
the developer's instance/tripura_explore.db file.
"""
from __future__ import annotations

import pytest

from app import create_app
from app.extensions import db
from app.models import Business, Category, District, Itinerary, ItineraryStop, Place, User
from app.seed_data import seed_businesses, seed_categories, seed_districts, seed_places, seed_route_connections

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin-password"
USER_EMAIL = "traveller@example.com"
USER_PASSWORD = "traveller-password"


@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        seed_categories()
        seed_districts()
        seed_places()
        seed_businesses()
        seed_route_connections()

        admin = User(name="Site Admin", email=ADMIN_EMAIL, role="admin")
        admin.set_password(ADMIN_PASSWORD)
        traveller = User(name="Test Traveller", email=USER_EMAIL, role="user")
        traveller.set_password(USER_PASSWORD)
        db.session.add_all([admin, traveller])
        db.session.commit()

        yield application

        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


def login(client, email=USER_EMAIL, password=USER_PASSWORD):
    return client.post(
        "/auth/login", data={"email": email, "password": password}, follow_redirects=True
    )


@pytest.fixture()
def auth_client(client):
    login(client)
    return client


@pytest.fixture()
def admin_client(client):
    login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    return client


@pytest.fixture()
def place(app):
    return Place.query.filter_by(slug="neermahal").first()


@pytest.fixture()
def traveller(app):
    return User.query.filter_by(email=USER_EMAIL).first()


@pytest.fixture()
def saved_trip(app, traveller):
    """A small saved itinerary owned by the traveller fixture."""
    places = Place.query.filter(Place.is_published.is_(True)).order_by(Place.popularity.desc()).limit(3).all()
    itinerary = Itinerary(
        user_id=traveller.id,
        title="Test trip",
        duration_days=2,
        starting_location="Agartala",
    )
    itinerary.set_interests(["Lakes", "Heritage"])
    db.session.add(itinerary)
    db.session.flush()
    for index, item in enumerate(places, start=1):
        db.session.add(
            ItineraryStop(
                itinerary_id=itinerary.id,
                place_id=item.id,
                day_number=1,
                stop_order=index,
            )
        )
    db.session.commit()
    return itinerary


__all__ = [
    "ADMIN_EMAIL",
    "ADMIN_PASSWORD",
    "USER_EMAIL",
    "USER_PASSWORD",
    "Business",
    "Category",
    "District",
    "Place",
    "login",
]