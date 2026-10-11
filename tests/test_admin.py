"""TC-10 · administrator authorization and content management."""
from app.extensions import db
from app.models import Business, Place
from tests.conftest import login


def test_anonymous_visitor_is_redirected_from_admin(client):
    response = client.get("/admin/places")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_ordinary_user_gets_403_on_every_admin_route(client, app):
    login(client)
    for path in [
        "/admin",
        "/admin/places",
        "/admin/places/new",
        "/admin/categories",
        "/admin/providers",
        "/admin/inquiries",
        "/admin/corrections",
        "/admin/users",
    ]:
        assert client.get(path).status_code == 403, path


def test_ordinary_user_cannot_publish_a_place(client, app, place):
    login(client)
    response = client.post(f"/admin/places/{place.id}/publish")
    assert response.status_code == 403
    assert db.session.get(Place, place.id).is_published is True  # unchanged


def test_admin_sees_the_destination_list(admin_client):
    body = admin_client.get("/admin/places").data
    assert b"Destination records" in body
    assert b"Neermahal" in body


def test_admin_can_unpublish_and_publish(admin_client, app, place):
    admin_client.post(f"/admin/places/{place.id}/unpublish")
    assert db.session.get(Place, place.id).is_published is False
    assert admin_client.get(f"/places/{place.slug}").status_code == 404

    admin_client.post(f"/admin/places/{place.id}/publish")
    assert db.session.get(Place, place.id).is_published is True
    assert admin_client.get(f"/places/{place.slug}").status_code == 200


def test_admin_can_create_a_destination(admin_client, app):
    from app.models import Category, District

    category = Category.query.filter_by(slug="nature").first()
    district = District.query.filter_by(slug="gomati").first()
    response = admin_client.post(
        "/admin/places/new",
        data={
            "name": "Test Waterfall",
            "slug": "test-waterfall",
            "category_id": str(category.id),
            "district_id": str(district.id),
            "short_description": "A waterfall created by an administrator in a test.",
            "popularity": "10",
            "is_published": "y",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    created = Place.query.filter_by(slug="test-waterfall").first()
    assert created is not None
    assert created.is_published is True


def test_half_filled_coordinates_are_rejected(admin_client, app):
    from app.models import Category

    category = Category.query.filter_by(slug="nature").first()
    response = admin_client.post(
        "/admin/places/new",
        data={
            "name": "Half Coordinates",
            "slug": "half-coordinates",
            "category_id": str(category.id),
            "latitude": "23.5",
        },
    )
    assert response.status_code == 200
    assert Place.query.filter_by(slug="half-coordinates").first() is None
    assert b"Enter both latitude and longitude" in response.data


def test_verifying_a_record_requires_a_name(admin_client, app):
    from app.models import Category

    category = Category.query.filter_by(slug="nature").first()
    response = admin_client.post(
        "/admin/places/new",
        data={"name": "No Verifier", "slug": "no-verifier", "category_id": str(category.id), "is_verified": "y"},
    )
    assert Place.query.filter_by(slug="no-verifier").first() is None
    assert b"Record the name of the person" in response.data


def test_admin_can_edit_a_destination(admin_client, app, place):
    response = admin_client.post(
        f"/admin/places/{place.id}/edit",
        data={
            "name": "Neermahal (edited)",
            "slug": place.slug,
            "category_id": str(place.category_id),
            "district_id": str(place.district_id),
            "short_description": place.short_description,
            "popularity": str(place.popularity),
            "is_published": "y",
            "entry_fee_indian": "₹20 (verify)",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert db.session.get(Place, place.id).name == "Neermahal (edited)"


def test_admin_approves_a_provider(admin_client, app):
    pending = Business.query.filter_by(approval_status="pending").first()
    assert pending is not None
    admin_client.post(f"/admin/providers/{pending.id}/approve")
    assert db.session.get(Business, pending.id).approval_status == "approved"


def test_admin_can_add_a_category(admin_client, app):
    from app.models import Category

    admin_client.post("/admin/categories", data={"name": "Festivals", "slug": "festivals"}, follow_redirects=True)
    assert Category.query.filter_by(slug="festivals").first() is not None


def test_admin_sees_inquiry_and_correction_queues(admin_client, app, place):
    client = admin_client
    client.post(f"/places/{place.slug}/report", data={"message": "This fee is out of date."})
    assert b"Reported corrections" in client.get("/admin/corrections").data
    assert b"Visitor inquiries" in client.get("/admin/inquiries").data


def test_admin_cannot_change_their_own_role(admin_client, app):
    from app.models import User

    admin = User.query.filter_by(email="admin@example.com").first()
    admin_client.post(f"/admin/users/{admin.id}/role", data={"role": "user"})
    assert db.session.get(User, admin.id).role == "admin"


def test_seed_command_is_repeatable(runner, app):
    from app.models import Category, Place

    before = (Category.query.count(), Place.query.count())
    result = runner.invoke(args=["seed-data"])
    assert result.exit_code == 0
    assert (Category.query.count(), Place.query.count()) == before