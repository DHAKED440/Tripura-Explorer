"""Comprehensive Test Suite for Smart Route Lab: Graph Theory & Route Optimization."""
from __future__ import annotations

import json
import pytest

from app.models import Place, RouteConnection, SavedSmartRoute
from app.services.ai_route_assistant import AIRouteAssistant
from app.services.graph_service import GraphService
from app.services.graph_traversal_service import GraphTraversalService
from app.services.personalization_service import PersonalizationService
from app.services.route_optimization_service import RouteOptimizationService
from app.services.shortest_path_service import ShortestPathService
from app.services.spanning_tree_service import SpanningTreeService
from app.services.tsp_service import TSPService
from tests.conftest import login


# --------------------------------------------------------------------------- #
# 1. Graph Construction & Topology Tests
# --------------------------------------------------------------------------- #
def test_graph_construction(app):
    with app.app_context():
        svc = GraphService()
        metrics = svc.get_graph_metrics()

        assert metrics["node_count"] >= 15
        assert metrics["edge_count"] >= 25
        assert metrics["avg_degree"] > 2.0
        assert metrics["connected_components"] == 1
        assert 0.0 < metrics["density"] < 1.0


def test_graph_serialization(app):
    with app.app_context():
        svc = GraphService()
        ui_data = svc.serialize_for_ui()

        assert "nodes" in ui_data
        assert "edges" in ui_data
        assert len(ui_data["nodes"]) >= 15
        assert len(ui_data["edges"]) >= 25

        node0 = ui_data["nodes"][0]
        assert "id" in node0
        assert "name" in node0
        assert "lat" in node0
        assert "lng" in node0


def test_data_quality_audit(app):
    with app.app_context():
        svc = GraphService()
        audit = svc.audit_network_data()

        assert "missing_coords_nodes" in audit
        assert "isolated_nodes" in audit
        assert len(audit["missing_coords_nodes"]) == 0
        assert len(audit["isolated_nodes"]) == 0


# --------------------------------------------------------------------------- #
# 2. Dijkstra & Shortest Path Tests
# --------------------------------------------------------------------------- #
def test_dijkstra_shortest_path(app):
    with app.app_context():
        agartala = Place.query.filter(Place.name.ilike("%Ujjayanta%")).first()
        udaipur = Place.query.filter(Place.name.ilike("%Tripura Sundari%")).first()

        assert agartala is not None
        assert udaipur is not None

        svc = ShortestPathService()
        result = svc.find_shortest_path(agartala.id, udaipur.id, metric="time", record_steps=True)

        assert result["success"] is True
        assert len(result["path_node_ids"]) >= 2
        assert result["path_node_ids"][0] == agartala.id
        assert result["path_node_ids"][-1] == udaipur.id
        assert result["total_distance_km"] > 0
        assert result["total_time_minutes"] > 0
        assert len(result["steps"]) > 0


def test_dijkstra_metrics_differ(app):
    with app.app_context():
        agartala = Place.query.filter(Place.name.ilike("%Ujjayanta%")).first()
        jampui = Place.query.filter(Place.name.ilike("%Jampui%")).first()

        svc = ShortestPathService()
        res_time = svc.find_shortest_path(agartala.id, jampui.id, metric="time")
        res_dist = svc.find_shortest_path(agartala.id, jampui.id, metric="distance")

        assert res_time["success"] is True
        assert res_dist["success"] is True
        # Both paths reach target
        assert res_time["path_node_ids"][-1] == jampui.id
        assert res_dist["path_node_ids"][-1] == jampui.id


# --------------------------------------------------------------------------- #
# 3. A* Search Algorithm Tests
# --------------------------------------------------------------------------- #
def test_astar_search_admissibility(app):
    with app.app_context():
        agartala = Place.query.filter(Place.name.ilike("%Ujjayanta%")).first()
        unakoti = Place.query.filter(Place.name.ilike("%Unakoti%")).first()

        svc = ShortestPathService()
        astar_res = svc.find_astar_path(agartala.id, unakoti.id, metric="distance", record_steps=True)
        dijkstra_res = svc.find_shortest_path(agartala.id, unakoti.id, metric="distance", record_steps=False)

        assert astar_res["success"] is True
        assert dijkstra_res["success"] is True
        # Both must find equivalent optimal path cost
        assert pytest.approx(astar_res["total_distance_km"], rel=1e-2) == dijkstra_res["total_distance_km"]
        assert len(astar_res["steps"]) > 0


# --------------------------------------------------------------------------- #
# 4. Kruskal Minimum Spanning Tree Tests
# --------------------------------------------------------------------------- #
def test_kruskal_minimum_spanning_tree(app):
    with app.app_context():
        svc = SpanningTreeService()
        mst = svc.compute_minimum_spanning_tree(metric="distance", record_steps=True)

        assert mst["success"] is True
        assert mst["total_vertices"] >= 15
        # In a connected tree with V vertices, there are exactly V - 1 edges
        assert len(mst["tree_edges"]) == mst["total_vertices"] - 1
        assert mst["total_weight"] > 0
        assert len(mst["steps"]) > 0


# --------------------------------------------------------------------------- #
# 5. Held-Karp & TSP Tests
# --------------------------------------------------------------------------- #
def test_tsp_held_karp_exact(app):
    with app.app_context():
        places = Place.query.filter_by(is_published=True).limit(4).all()
        origin = places[0]
        stop_ids = [p.id for p in places[1:]]

        svc = TSPService()
        tour = svc.solve_multi_stop_tour(origin.id, stop_ids, metric="time", record_steps=True)

        assert tour["success"] is True
        assert len(tour["tour_node_ids"]) >= len(places) + 1
        # Origin should be start and end of the closed tour
        assert tour["tour_node_ids"][0] == origin.id
        assert tour["tour_node_ids"][-1] == origin.id
        assert tour["total_distance_km"] > 0
        assert len(tour["steps"]) > 0


# --------------------------------------------------------------------------- #
# 6. Graph Traversal (BFS & DFS) Tests
# --------------------------------------------------------------------------- #
def test_bfs_and_dfs_traversals(app):
    with app.app_context():
        start = Place.query.filter_by(is_published=True).first()
        svc = GraphTraversalService()

        bfs = svc.breadth_first_search(start.id)
        dfs = svc.depth_first_search(start.id)

        assert bfs["success"] is True
        assert dfs["success"] is True
        assert bfs["visited_order"][0] == start.id
        assert dfs["visited_order"][0] == start.id
        assert len(bfs["visited_order"]) == len(dfs["visited_order"])
        assert len(bfs["steps"]) > 0
        assert len(dfs["steps"]) > 0


# --------------------------------------------------------------------------- #
# 7. Multi-Objective Route Optimization & Pareto Front Tests
# --------------------------------------------------------------------------- #
def test_pareto_route_comparison(app):
    with app.app_context():
        agartala = Place.query.filter(Place.name.ilike("%Ujjayanta%")).first()
        unakoti = Place.query.filter(Place.name.ilike("%Unakoti%")).first()

        svc = RouteOptimizationService()
        comp = svc.compare_route_alternatives(agartala.id, unakoti.id)

        assert comp["success"] is True
        assert len(comp["routes"]) >= 3

        # At least one route must be on the Pareto frontier
        pareto_optimal_routes = [r for r in comp["routes"] if r["is_pareto_optimal"]]
        assert len(pareto_optimal_routes) >= 1


# --------------------------------------------------------------------------- #
# 8. Personalization & Multi-Day Itinerary Tests
# --------------------------------------------------------------------------- #
def test_personalized_itinerary_generation(app):
    with app.app_context():
        agartala = Place.query.filter(Place.name.ilike("%Ujjayanta%")).first()
        svc = PersonalizationService()

        res = svc.generate_personalized_journey(
            start_node_id=agartala.id,
            days=2,
            max_daily_travel_hours=6.0,
            primary_interest="heritage",
            pace="moderate",
            objective="balanced",
        )

        assert res["success"] is True
        assert len(res["daily_plans"]) == 2
        assert res["total_distance_km"] > 0
        assert len(res["itinerary"]) >= 2
        assert len(res["steps"]) > 0


def test_ai_route_assistant_heuristic_fallback(app):
    with app.app_context():
        assistant = AIRouteAssistant()
        parsed = assistant.parse_natural_language_query("Plan a 3-day spiritual and lake journey from Agartala")

        assert parsed["days"] == 3
        assert "spiritual" in parsed["primary_interest"] or "lake" in parsed["primary_interest"]
        assert parsed["origin_id"] is not None


# --------------------------------------------------------------------------- #
# 9. API Endpoint Integration Tests
# --------------------------------------------------------------------------- #
def test_api_lab_page_renders(client):
    res = client.get("/smart-route-lab")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "Smart Route Lab" in html
    assert "Tourist Mode" in html
    assert "Graph Explorer" in html
    assert "initial-graph-data" in html


def test_api_get_graph(client):
    res = client.get("/api/smart-route/graph?weight_metric=distance")
    assert res.status_code == 200
    data = res.get_json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) >= 15


def test_api_shortest_path_endpoint(client, app):
    with app.app_context():
        places = Place.query.filter_by(is_published=True).all()
        p1, p2 = places[0], places[1]

    payload = {"start_node_id": p1.id, "target_node_id": p2.id, "weight_metric": "time"}
    res = client.post("/api/smart-route/shortest-path", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "path_node_ids" in data
    assert "steps" in data


def test_api_astar_endpoint(client, app):
    with app.app_context():
        places = Place.query.filter_by(is_published=True).all()
        p1, p2 = places[0], places[1]

    payload = {"start_node_id": p1.id, "target_node_id": p2.id, "weight_metric": "distance"}
    res = client.post("/api/smart-route/astar", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "path_node_ids" in data


def test_api_spanning_tree_endpoint(client):
    res = client.get("/api/smart-route/spanning-tree?weight_metric=distance")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "tree_edges" in data


def test_api_bfs_dfs_endpoint(client, app):
    with app.app_context():
        p1 = Place.query.first()

    res = client.get(f"/api/smart-route/bfs-dfs?algo=bfs&start_id={p1.id}")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "visited_order" in data


def test_api_multi_stop_tsp_endpoint(client, app):
    with app.app_context():
        places = Place.query.limit(4).all()
        origin = places[0]
        stops = [p.id for p in places[1:]]

    payload = {"origin_id": origin.id, "stop_ids": stops, "weight_metric": "time"}
    res = client.post("/api/smart-route/multi-stop", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "tour_node_ids" in data


def test_api_personalize_endpoint(client, app):
    with app.app_context():
        origin = Place.query.first()

    payload = {
        "start_node_id": origin.id,
        "days": 2,
        "max_daily_travel_hours": 6.0,
        "primary_interest": "heritage",
        "pace": "moderate",
        "objective": "balanced",
    }
    res = client.post("/api/smart-route/personalize", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "daily_plans" in data


def test_api_compare_endpoint(client, app):
    with app.app_context():
        places = Place.query.filter_by(is_published=True).all()
        p1, p2 = places[0], places[1]

    res = client.get(f"/api/smart-route/compare?start_node_id={p1.id}&target_node_id={p2.id}")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "routes" in data


def test_api_parse_query_endpoint(client):
    res = client.post("/api/smart-route/parse-query", json={"query": "2 days in Tripura focusing on temples"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["parsed"]["days"] == 2


def test_save_and_retrieve_smart_route(client, app):
    with app.app_context():
        places = Place.query.limit(3).all()
        ids = [p.id for p in places]

    # 1. Anonymous save
    payload = {
        "title": "Test Western Circuit",
        "notes": "Automated test notes",
        "ordered_stop_ids": ids,
        "legs": [],
        "total_distance_km": 110.5,
        "total_time_minutes": 180,
        "total_cost_inr": 350,
        "preferences": {"mode": "tourist"},
    }
    res = client.post("/api/smart-route/save", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "route_id" in data
    assert "token" in data

    route_id = data["route_id"]
    token = data["token"]

    # 2. Retrieve route
    get_res = client.get(f"/api/smart-route/saved/{route_id}?token={token}")
    assert get_res.status_code == 200
    saved = get_res.get_json()
    assert saved["success"] is True
    assert saved["route"]["title"] == "Test Western Circuit"
    assert saved["route"]["ordered_stop_ids"] == ids


def test_bellman_ford_shortest_path(app):
    with app.app_context():
        agartala = Place.query.filter(Place.name.ilike("%Ujjayanta%")).first()
        udaipur = Place.query.filter(Place.name.ilike("%Tripura Sundari%")).first()

        assert agartala is not None
        assert udaipur is not None

        svc = ShortestPathService()
        result = svc.find_bellman_ford_path(agartala.id, udaipur.id, metric="time", record_steps=True)

        assert result["success"] is True
        assert len(result["path_node_ids"]) >= 2
        assert result["path_node_ids"][0] == agartala.id
        assert result["path_node_ids"][-1] == udaipur.id
        assert result["total_distance_km"] > 0
        assert len(result["steps"]) > 0


def test_api_bellman_ford_endpoint(client, app):
    with app.app_context():
        places = Place.query.filter_by(is_published=True).all()
        p1, p2 = places[0], places[1]

    payload = {"start_node_id": p1.id, "target_node_id": p2.id, "weight_metric": "time"}
    res = client.post("/api/smart-route/bellman-ford", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "path_node_ids" in data
    assert "steps" in data

