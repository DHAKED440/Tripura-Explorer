"""Smart Route Lab Blueprint: Graph theory routes and optimization API endpoints.

Serves the interactive laboratory page and provides REST endpoints for Dijkstra,
A*, Kruskal MST, BFS/DFS, Held-Karp TSP, Personalized constrained journey planning,
and empirical Pareto trade-off comparisons.
"""
from __future__ import annotations

from flask import Blueprint, abort, current_app, jsonify, render_template, request
from flask_login import current_user

from app.extensions import csrf, db
from app.models import Place, RouteConnection, SavedSmartRoute
from app.services.ai_route_assistant import AIRouteAssistant
from app.services.graph_service import GraphService
from app.services.graph_traversal_service import GraphTraversalService
from app.services.personalization_service import PersonalizationService
from app.services.route_optimization_service import RouteOptimizationService
from app.services.shortest_path_service import ShortestPathService
from app.services.spanning_tree_service import SpanningTreeService
from app.services.tsp_service import TSPService

bp = Blueprint("smart_route", __name__)


def _get_json_payload() -> dict:
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form.to_dict()


# --------------------------------------------------------------------------- #
# Public Laboratory Page
# --------------------------------------------------------------------------- #
@bp.route("/smart-route-lab", methods=["GET"])
def lab_page():
    """Render the Smart Route Lab page with interactive Dual Visualizations."""
    places = Place.query.filter_by(is_published=True).order_by(Place.popularity.desc()).all()
    graph_svc = GraphService(places=places)
    graph_data = graph_svc.serialize_for_ui()
    metrics = graph_svc.get_graph_metrics()

    return render_template(
        "smart_route_lab.html",
        places=places,
        initial_graph_json=graph_data,
        metrics=metrics,
        default_start_id=places[0].id if places else None,
    )


# --------------------------------------------------------------------------- #
# Graph Data & Metrics Endpoints
# --------------------------------------------------------------------------- #
@bp.route("/api/smart-route/graph", methods=["GET"])
def get_graph():
    """Return complete graph nodes, edges, components, and metrics."""
    weight_metric = request.args.get("weight_metric", "time")
    transport_mode = request.args.get("transport_mode")
    graph_svc = GraphService(weight_metric=weight_metric, transport_mode=transport_mode)
    data = graph_svc.serialize_for_ui()
    return jsonify({
        "success": True,
        "graph": data,
        "nodes": data["nodes"],
        "edges": data["edges"],
        "metrics": data["metrics"],
        "components": data["components"],
    })


@bp.route("/api/smart-route/graph/<int:destination_id>", methods=["GET"])
def get_node_details(destination_id: int):
    """Return specific node degree, neighbors, and incident edges."""
    graph_svc = GraphService()
    if destination_id not in graph_svc.places_by_id:
        return jsonify({"success": False, "error": "Destination not found"}), 404

    place = graph_svc.places_by_id[destination_id]
    neighbors = graph_svc.get_neighbors(destination_id)
    degree = graph_svc.get_node_degree(destination_id)

    return jsonify({
        "success": True,
        "node": place.to_dict(),
        "degree": degree,
        "neighbors": [
            {
                "neighbor_id": nid,
                "neighbor_name": graph_svc.places_by_id[nid].name,
                "weight": w,
                "edge": edge_info,
            }
            for nid, w, edge_info in neighbors
        ],
    })


@bp.route("/api/smart-route/metrics", methods=["GET"])
def get_metrics():
    """Return network connectivity metrics and data-quality audit report."""
    graph_svc = GraphService()
    return jsonify({
        "success": True,
        "metrics": graph_svc.get_graph_metrics(),
        "data_quality_audit": graph_svc.audit_data_quality(),
    })


# --------------------------------------------------------------------------- #
# Algorithm Computation Endpoints
# --------------------------------------------------------------------------- #
@bp.route("/api/smart-route/shortest-path", methods=["POST"])
@csrf.exempt
def run_dijkstra():
    """Execute Dijkstra's algorithm between start_id and target_id."""
    data = _get_json_payload()
    start_id = data.get("start_id") or data.get("start_node_id")
    target_id = data.get("target_id") or data.get("target_node_id")
    weight_metric = data.get("weight_metric", "time")

    if not start_id or not target_id:
        return jsonify({"success": False, "error": "Both start_id and target_id are required."}), 400

    try:
        start_id = int(start_id)
        target_id = int(target_id)
    except ValueError:
        return jsonify({"success": False, "error": "Invalid start_id or target_id format."}), 400

    graph_svc = GraphService(weight_metric=weight_metric)
    sp_svc = ShortestPathService(graph_svc)
    result = sp_svc.dijkstra(start_id, target_id, record_steps=True)
    return jsonify(result)


@bp.route("/api/smart-route/astar", methods=["POST"])
@csrf.exempt
def run_astar():
    """Execute A* search algorithm using Haversine admissible heuristic."""
    data = _get_json_payload()
    start_id = data.get("start_id") or data.get("start_node_id")
    target_id = data.get("target_id") or data.get("target_node_id")
    weight_metric = data.get("weight_metric", "time")

    if not start_id or not target_id:
        return jsonify({"success": False, "error": "Both start_id and target_id are required."}), 400

    try:
        start_id = int(start_id)
        target_id = int(target_id)
    except ValueError:
        return jsonify({"success": False, "error": "Invalid start_id or target_id format."}), 400

    graph_svc = GraphService(weight_metric=weight_metric)
    sp_svc = ShortestPathService(graph_svc)
    result = sp_svc.astar(start_id, target_id, record_steps=True)
    return jsonify(result)


@bp.route("/api/smart-route/bellman-ford", methods=["POST"])
@csrf.exempt
def run_bellman_ford():
    """Execute Bellman-Ford algorithm with negative cycle detection."""
    data = _get_json_payload()
    start_id = data.get("start_id") or data.get("start_node_id")
    target_id = data.get("target_id") or data.get("target_node_id")
    weight_metric = data.get("weight_metric", "time")

    if not start_id or not target_id:
        return jsonify({"success": False, "error": "Both start_id and target_id are required."}), 400

    try:
        start_id = int(start_id)
        target_id = int(target_id)
    except ValueError:
        return jsonify({"success": False, "error": "Invalid start_id or target_id format."}), 400

    graph_svc = GraphService(weight_metric=weight_metric)
    sp_svc = ShortestPathService(graph_svc)
    result = sp_svc.bellman_ford(start_id, target_id, record_steps=True)
    return jsonify(result)


@bp.route("/api/smart-route/spanning-tree", methods=["GET", "POST"])
@csrf.exempt
def run_spanning_tree():
    """Execute Kruskal's algorithm with Disjoint-Set Union for MST."""
    data = _get_json_payload()
    weight_metric = data.get("weight_metric") or request.args.get("weight_metric", "distance")

    graph_svc = GraphService(weight_metric=weight_metric)
    st_svc = SpanningTreeService(graph_svc)
    result = st_svc.kruskal(record_steps=True)
    return jsonify(result)


@bp.route("/api/smart-route/bfs-dfs", methods=["GET", "POST"])
@csrf.exempt
def run_traversal():
    """Execute Breadth-First Search (BFS) or Depth-First Search (DFS)."""
    data = _get_json_payload()
    start_id = data.get("start_id") or request.args.get("start_id")
    mode = (data.get("mode") or data.get("algo") or request.args.get("algo") or request.args.get("mode") or "bfs").lower()
    target_id = data.get("target_id") or request.args.get("target_id")

    if not start_id:
        return jsonify({"success": False, "error": "start_id is required."}), 400

    try:
        start_id = int(start_id)
        if target_id:
            target_id = int(target_id)
    except ValueError:
        return jsonify({"success": False, "error": "Invalid node ID format."}), 400

    graph_svc = GraphService()
    trav_svc = GraphTraversalService(graph_svc)

    if mode == "dfs":
        result = trav_svc.dfs(start_id)
    else:
        result = trav_svc.bfs(start_id, target_id=target_id)
    return jsonify(result)


@bp.route("/api/smart-route/multi-stop", methods=["POST"])
@csrf.exempt
def run_multi_stop():
    """Solve multi-stop TSP tour (Held-Karp exact DP for N<=10, else 2-opt heuristic)."""
    data = _get_json_payload()
    stop_ids = data.get("stop_ids", [])
    start_id = data.get("start_id") or data.get("origin_id")
    end_id = data.get("end_id")
    return_to_start = data.get("return_to_start", True)
    weight_metric = data.get("weight_metric", "time")

    if not stop_ids or not start_id:
        return jsonify({"success": False, "error": "Both start_id and stop_ids are required."}), 400

    try:
        start_id = int(start_id)
        stop_ids = [int(s) for s in stop_ids]
        if end_id:
            end_id = int(end_id)
    except ValueError:
        return jsonify({"success": False, "error": "Invalid destination ID format."}), 400

    graph_svc = GraphService(weight_metric=weight_metric)
    tsp_svc = TSPService(graph_svc)
    result = tsp_svc.solve_tour(
        stop_ids=stop_ids,
        start_id=start_id,
        end_id=end_id,
        return_to_start=return_to_start,
    )
    return jsonify(result)


@bp.route("/api/smart-route/personalize", methods=["POST"])
@csrf.exempt
def run_personalize():
    """Generate personalized, constraint-validated multi-day journey."""
    data = _get_json_payload()
    start_id = data.get("start_id") or data.get("start_node_id")
    duration_days = data.get("duration_days") or data.get("days", 2)
    interests = data.get("interests")
    if not interests:
        prim = data.get("primary_interest")
        interests = [prim] if prim and prim != "all" else []
    elif isinstance(interests, str):
        interests = [interests]

    pace = data.get("pace", "balanced").lower()
    if pace == "moderate":
        pace = "balanced"
    elif pace == "fast":
        pace = "packed"

    budget = data.get("budget")
    must_visit_ids = data.get("must_visit_ids", [])
    accessibility_required = bool(data.get("accessibility_required", False))
    return_to_start = bool(data.get("return_to_start", True))

    if not start_id:
        return jsonify({"success": False, "error": "start_id is required."}), 400

    try:
        start_id = int(start_id)
        duration_days = max(1, min(5, int(duration_days)))
        must_visit_ids = [int(sid) for sid in must_visit_ids if sid]
        if budget is not None and str(budget).strip():
            budget = float(budget)
        else:
            budget = None
    except ValueError:
        return jsonify({"success": False, "error": "Invalid parameter values."}), 400

    graph_svc = GraphService(weight_metric="time")
    pers_svc = PersonalizationService(graph_svc)
    result = pers_svc.build_personalized_itinerary(
        start_id=start_id,
        duration_days=duration_days,
        interests=interests,
        pace=pace,
        budget=budget,
        must_visit_ids=must_visit_ids,
        accessibility_required=accessibility_required,
        return_to_start=return_to_start,
    )
    return jsonify(result)


@bp.route("/api/smart-route/compare", methods=["GET", "POST"])
@csrf.exempt
def compare_objectives():
    """Compare candidate routes across Distance, Time, Cost, and Balanced objectives."""
    data = _get_json_payload()
    start_id = data.get("start_id") or request.args.get("start_id") or request.args.get("start_node_id")
    target_id = data.get("target_id") or request.args.get("target_id") or request.args.get("target_node_id")
    stop_ids = data.get("stop_ids", [])
    if not stop_ids and target_id:
        stop_ids = [target_id]
        return_to_start = False
    else:
        return_to_start = data.get("return_to_start", True)
    end_id = data.get("end_id")

    if not stop_ids or not start_id:
        return jsonify({"success": False, "error": "Both start_id and stop_ids/target_id are required."}), 400

    try:
        start_id = int(start_id)
        stop_ids = [int(s) for s in stop_ids]
        if end_id:
            end_id = int(end_id)
    except ValueError:
        return jsonify({"success": False, "error": "Invalid destination ID format."}), 400

    opt_svc = RouteOptimizationService()
    result = opt_svc.compare_objectives(
        stop_ids=stop_ids,
        start_id=start_id,
        end_id=end_id,
        return_to_start=return_to_start,
    )
    return jsonify(result)


@bp.route("/api/smart-route/parse-query", methods=["POST"])
@csrf.exempt
def parse_natural_language():
    """Convert conversational natural-language prompt into validated planner parameters."""
    data = _get_json_payload()
    query = data.get("query", "")
    assistant = AIRouteAssistant()
    parsed = assistant.parse_natural_language_request(query)
    return jsonify(parsed)


# --------------------------------------------------------------------------- #
# Route Persistence Endpoints
# --------------------------------------------------------------------------- #
@bp.route("/api/smart-route/save", methods=["POST"])
@csrf.exempt
def save_smart_route():
    """Persist an optimized route to the database for later recall and sharing."""
    data = _get_json_payload()
    title = data.get("title", "My Optimized Tripura Route")
    start_id = data.get("start_id") or (data.get("ordered_stop_ids")[0] if data.get("ordered_stop_ids") else None)
    end_id = data.get("end_id")
    is_round_trip = bool(data.get("is_round_trip", True))
    selected_ids = data.get("selected_destination_ids") or data.get("ordered_stop_ids", [])
    objective = data.get("optimization_objective", "time")
    algorithm = data.get("algorithm_used", "dijkstra")
    guarantee = data.get("algorithm_guarantee", "exact_shortest_path")
    total_km = float(data.get("total_distance_km", 0.0))
    total_mins = float(data.get("total_time_minutes", 0.0))
    total_cost = data.get("total_estimated_cost") if data.get("total_estimated_cost") is not None else data.get("total_cost_inr")
    if total_cost is not None:
        total_cost = float(total_cost)

    ordered_stops = data.get("ordered_stops") or data.get("ordered_stop_ids", [])
    legs = data.get("legs", [])
    preferences = data.get("preferences", {})

    assistant = AIRouteAssistant()
    summary_notes = assistant.explain_route({
        "success": True,
        "total_distance_km": total_km,
        "total_time_minutes": total_mins,
        "algorithm": algorithm,
        "guarantee": guarantee,
        "ordered_stops": ordered_stops,
    })

    saved = SavedSmartRoute(
        user_id=current_user.id if current_user.is_authenticated else None,
        title=title,
        start_place_id=start_id,
        end_place_id=end_id,
        is_round_trip=is_round_trip,
        selected_destination_ids=selected_ids,
        optimization_objective=objective,
        algorithm_used=algorithm,
        algorithm_guarantee=guarantee,
        total_distance_km=total_km,
        total_time_minutes=total_mins,
        total_estimated_cost=total_cost,
        ordered_stops_json=ordered_stops,
        legs_json=legs,
        preferences_json=preferences,
        summary_notes=summary_notes,
    )
    db.session.add(saved)
    db.session.commit()

    return jsonify({
        "success": True,
        "route_id": saved.id,
        "saved_route_id": saved.id,
        "token": saved.share_token,
        "share_token": saved.share_token,
        "share_url": f"/smart-route-lab?route_id={saved.id}",
        "explanation": summary_notes,
    })


@bp.route("/api/smart-route/saved/<int:route_id>", methods=["GET"])
def get_saved_smart_route(route_id: int):
    """Retrieve saved route data by ID."""
    saved = db.session.get(SavedSmartRoute, route_id)
    if not saved:
        return jsonify({"success": False, "error": "Saved route not found"}), 404
    token = request.args.get("token")
    if token and saved.share_token != token and not (current_user.is_authenticated and saved.user_id == current_user.id):
        return jsonify({"success": False, "error": "Invalid share token"}), 403
    return jsonify({"success": True, "route": saved.to_dict()})
