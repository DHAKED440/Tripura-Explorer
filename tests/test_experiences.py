"""Local experiences directory and inquiry handling."""
from app.models import Business, Inquiry


def test_only_approved_providers_are_listed(client, app):
    body = client.get("/experiences").data
    for provider in Business.query.filter_by(approval_status="approved").all():
        assert provider.name.encode() in body
    for provider in Business.query.filter_by(approval_status="pending").all():
        assert provider.name.encode() not in body


def test_pending_provider_detail_is_hidden(client, app):
    pending = Business.query.filter_by(approval_status="pending").first()
    assert client.get(f"/experiences/{pending.slug}").status_code == 404


def test_approved_provider_detail_renders(client, app):
    approved = Business.query.filter_by(approval_status="approved").first()
    response = client.get(f"/experiences/{approved.slug}")
    assert response.status_code == 200
    assert b"Send an inquiry" in response.data


def test_inquiry_filters_by_category_and_district(client):
    body = client.get("/experiences?category=Homestay").data
    assert b"Demo Homestay" in body
    assert b"Demo Restaurant" not in body


def test_valid_inquiry_is_stored(client, app):
    approved = Business.query.filter_by(approval_status="approved").first()
    response = client.post(
        "/api/inquiries",
        json={
            "business_id": approved.id,
            "name": "Prospective Guest",
            "email": "guest@example.com",
            "phone": "+91 00000 00000",
            "message": "Do you have a room for two nights in December?",
        },
    )
    assert response.status_code == 201
    inquiry = Inquiry.query.filter_by(business_id=approved.id).first()
    assert inquiry is not None
    assert inquiry.status == "new"


def test_invalid_inquiry_is_rejected(client, app):
    approved = Business.query.filter_by(approval_status="approved").first()
    response = client.post(
        "/api/inquiries",
        json={"business_id": approved.id, "name": "X", "email": "not-an-email", "message": "hi"},
    )
    assert response.status_code == 400
    assert len(response.get_json()["errors"]) >= 2
    assert Inquiry.query.count() == 0


def test_inquiry_for_unknown_provider(client):
    response = client.post(
        "/api/inquiries",
        json={"business_id": 999999, "name": "Someone", "email": "a@b.com", "message": "Hello there."},
    )
    assert response.status_code == 404


def test_inquiry_form_works_without_javascript(client, app):
    approved = Business.query.filter_by(approval_status="approved").first()
    response = client.post(
        f"/experiences/{approved.slug}/inquire",
        data={"name": "Form User", "email": "form@example.com", "message": "Please share your rates."},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert Inquiry.query.filter_by(business_id=approved.id).count() == 1


def test_inquiry_personal_data_is_not_public(client, app):
    approved = Business.query.filter_by(approval_status="approved").first()
    client.post(
        "/api/inquiries",
        json={
            "business_id": approved.id,
            "name": "Private Person",
            "email": "private@example.com",
            "message": "I would like to know more about this stay.",
        },
    )
    body = client.get(f"/experiences/{approved.slug}").data
    assert b"private@example.com" not in body
    assert b"Private Person" not in body


def test_public_provider_page_has_no_admin_controls(client):
    approved = Business.query.filter_by(approval_status="approved").first()
    body = client.get(f"/experiences/{approved.slug}").data
    assert b"Approve" not in body


def test_experiences_page_labels_demo_content(client):
    body = client.get("/experiences").data
    assert b"Demo listings" in body