"""Registration, sign in/out, profile and favourites."""
from app.extensions import db
from app.models import Favorite, User
from tests.conftest import ADMIN_EMAIL, USER_EMAIL, USER_PASSWORD, login


def test_registration_creates_an_account_and_signs_in(client, app):
    response = client.post(
        "/auth/register",
        data={
            "name": "New Visitor",
            "email": "new@example.com",
            "password": "a-good-password",
            "confirm_password": "a-good-password",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    user = User.query.filter_by(email="new@example.com").first()
    assert user is not None
    assert user.role == "user"


def test_password_is_hashed_and_never_stored_in_plain_text(client, app):
    client.post(
        "/auth/register",
        data={"name": "Hash Test", "email": "hash@example.com", "password": "supersecret1", "confirm_password": "supersecret1"},
    )
    user = User.query.filter_by(email="hash@example.com").first()
    assert user.password_hash != "supersecret1"
    assert "supersecret1" not in user.password_hash
    assert user.check_password("supersecret1")


def test_duplicate_email_is_rejected(client, app):
    response = client.post(
        "/auth/register",
        data={"name": "Copy Cat", "email": USER_EMAIL, "password": "another-password", "confirm_password": "another-password"},
    )
    assert b"already exists" in response.data
    assert User.query.filter_by(email=USER_EMAIL).count() == 1


def test_password_mismatch_is_rejected(client, app):
    response = client.post(
        "/auth/register",
        data={"name": "Mismatch", "email": "mismatch@example.com", "password": "password-one", "confirm_password": "password-two"},
    )
    assert b"Passwords must match" in response.data
    assert User.query.filter_by(email="mismatch@example.com").first() is None


def test_short_password_is_rejected(client, app):
    client.post(
        "/auth/register",
        data={"name": "Short", "email": "short@example.com", "password": "abc", "confirm_password": "abc"},
    )
    assert User.query.filter_by(email="short@example.com").first() is None


def test_login_and_logout(client, app):
    response = login(client)
    assert b"Signed in" in response.data
    assert b"Sign out" in response.data

    client.post("/auth/logout")
    assert b"Sign in" in client.get("/").data


def test_login_with_wrong_password(client):
    response = login(client, USER_EMAIL, "not-the-password")
    assert b"incorrect" in response.data.lower()


def test_login_with_unknown_email(client):
    response = login(client, "nobody@example.com", "whatever-password")
    assert b"incorrect" in response.data.lower()


def test_protected_pages_redirect_anonymous_visitors(client):
    for path in ["/profile", "/my-trips"]:
        response = client.get(path)
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]


def test_profile_shows_account_details(auth_client):
    body = auth_client.get("/profile").data
    assert USER_EMAIL.encode() in body
    assert b"No saved trips yet" in body


def test_next_parameter_cannot_redirect_to_another_site(client):
    response = client.post(
        "/auth/login?next=https://evil.example.com",
        data={"email": USER_EMAIL, "password": USER_PASSWORD},
    )
    assert response.status_code == 302
    assert "evil.example.com" not in response.headers["Location"]


def test_favourites_api_adds_and_removes(auth_client, app, place):
    created = auth_client.post("/api/favorites", json={"place_id": place.id})
    assert created.status_code == 201
    assert Favorite.query.filter_by(place_id=place.id).count() == 1

    again = auth_client.post("/api/favorites", json={"place_id": place.id})
    assert again.status_code == 201
    assert Favorite.query.filter_by(place_id=place.id).count() == 1

    removed = auth_client.delete(f"/api/favorites/{place.id}")
    assert removed.status_code == 200
    assert Favorite.query.filter_by(place_id=place.id).count() == 0


def test_favourites_require_login(client, place):
    assert client.post("/api/favorites", json={"place_id": place.id}).status_code in {302, 401}


def test_favourite_unknown_place(auth_client):
    response = auth_client.post("/api/favorites", json={"place_id": 987654})
    assert response.status_code == 404


def test_admin_can_sign_in_and_reach_the_dashboard(admin_client):
    response = admin_client.get("/admin")
    assert response.status_code == 200
    assert b"Dashboard" in response.data


def test_ordinary_user_cannot_open_admin(client, app):
    login(client)
    response = client.get("/admin")
    assert response.status_code == 403
    assert b"do not have access" in response.data