from tests.conftest import login


def test_debug_anonymous(app, client, saved_trip):
    login(client)
    anonymous = app.test_client()
    response = anonymous.get(f"/api/itineraries/{saved_trip.id}")
    print("STATUS", response.status_code)
    print("BODY", response.get_json())
    print("RULES", [str(rule) for rule in app.url_map.iter_rules() if "itineraries" in str(rule)])
    with client.session_transaction() as session:
        print("CLIENT SESSION", dict(session))
    import flask_login
    from app.extensions import db
    from app.models import Itinerary
    with app.test_request_context("/"):
        print("fresh request auth:", flask_login.current_user.is_authenticated)
    trip = db.session.get(Itinerary, saved_trip.id)
    print("trip is_shared", repr(trip.is_shared), "share_token", repr(trip.share_token), "user_id", trip.user_id)