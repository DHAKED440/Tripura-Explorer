"""Graph Service: Builds and manages the weighted graph G = (V, E).

Provides adjacency list construction, node degree metrics, connectivity checks,
graph serialization for Leaflet and Canvas renderers, and comprehensive
data-quality auditing.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Tuple

from app.models import Place, RouteConnection
from app.services.destination_service import haversine_km


class GraphService:
    """In-memory weighted graph representation built from database records."""

    def __init__(
        self,
        places: Optional[List[Place]] = None,
        connections: Optional[List[RouteConnection]] = None,
        weight_metric: str = "time",  # 'time', 'distance', 'cost', 'balanced'
        transport_mode: Optional[str] = None,
        alpha: float = 0.33,  # balanced weight: distance
        beta: float = 0.34,   # balanced weight: time
        gamma: float = 0.33,  # balanced weight: cost
    ):
        self.weight_metric = weight_metric
        self.transport_mode = transport_mode
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

        # Load published places if not provided
        if places is None:
            self.places = Place.query.filter_by(is_published=True).all()
        else:
            self.places = places

        self.places_by_id: Dict[int, Place] = {p.id: p for p in self.places}

        # Load connections if not provided
        if connections is None:
            query = RouteConnection.query
            if transport_mode:
                query = query.filter_by(transport_mode=transport_mode)
            self.connections = query.all()
        else:
            self.connections = connections

        # Determine max weights for normalization
        self.max_distance = max([c.distance_km for c in self.connections], default=1.0) or 1.0
        self.max_time = max([c.travel_time_minutes for c in self.connections], default=1.0) or 1.0
        costs = [c.estimated_cost for c in self.connections if c.estimated_cost is not None]
        self.max_cost = max(costs, default=1.0) or 1.0

        # Build adjacency structures
        # node_id -> list of (neighbor_id, weight, edge_dict)
        self.adj: Dict[int, List[Tuple[int, float, Dict[str, Any]]]] = defaultdict(list)
        # edge lookup by (u, v)
        self.edges_by_pair: Dict[Tuple[int, int], Dict[str, Any]] = {}

        self._build_adjacency()

    def calculate_weight(self, conn: RouteConnection) -> float:
        """Calculate numerical weight w(u, v) based on selected optimization objective."""
        if self.weight_metric == "distance":
            return float(conn.distance_km)
        elif self.weight_metric == "cost":
            # If cost is unknown, use an estimated fuel/taxi rate based on distance: ~Rs 12/km
            return float(conn.estimated_cost if conn.estimated_cost is not None else conn.distance_km * 12.0)
        elif self.weight_metric == "balanced":
            d_norm = conn.distance_km / self.max_distance
            t_norm = conn.travel_time_minutes / self.max_time
            cost_val = conn.estimated_cost if conn.estimated_cost is not None else conn.distance_km * 12.0
            c_norm = cost_val / self.max_cost
            return float(self.alpha * d_norm + self.beta * t_norm + self.gamma * c_norm)
        else:
            # Default: travel time in minutes
            return float(conn.travel_time_minutes)

    def _build_adjacency(self) -> None:
        valid_ids = set(self.places_by_id.keys())

        for conn in self.connections:
            u, v = conn.source_destination_id, conn.target_destination_id
            if u not in valid_ids or v not in valid_ids:
                continue

            w = self.calculate_weight(conn)
            edge_info = conn.to_dict()
            edge_info["weight"] = round(w, 4)

            self.adj[u].append((v, w, edge_info))
            self.edges_by_pair[(u, v)] = edge_info

            # If bidirectional, add reverse edge
            if not conn.is_directed:
                self.adj[v].append((u, w, edge_info))
                self.edges_by_pair[(v, u)] = edge_info

    def get_neighbors(self, node_id: int) -> List[Tuple[int, float, Dict[str, Any]]]:
        """Return list of (neighbor_id, weight, edge_info) for given destination."""
        return self.adj.get(node_id, [])

    def get_node_degree(self, node_id: int) -> Dict[str, int]:
        """Return in-degree, out-degree and total degree of a vertex."""
        out_deg = len(self.adj.get(node_id, []))
        in_deg = 0
        for u in self.adj:
            if u != node_id:
                for v, _, _ in self.adj[u]:
                    if v == node_id:
                        in_deg += 1
        return {
            "in_degree": in_deg,
            "out_degree": out_deg,
            "total_degree": out_deg if not any(c.is_directed for c in self.connections) else in_deg + out_deg,
        }

    def get_connected_components(self) -> List[List[int]]:
        """Compute connected components of the graph using BFS."""
        visited: Set[int] = set()
        components: List[List[int]] = []

        for node_id in self.places_by_id:
            if node_id not in visited:
                comp: List[int] = []
                queue: deque = deque([node_id])
                visited.add(node_id)

                while queue:
                    curr = queue.popleft()
                    comp.append(curr)

                    # Look at all outgoing and incoming neighbors for weak connectivity
                    for neighbor, _, _ in self.adj.get(curr, []):
                        if neighbor not in visited and neighbor in self.places_by_id:
                            visited.add(neighbor)
                            queue.append(neighbor)

                    for other in self.places_by_id:
                        if other not in visited:
                            for neighbor, _, _ in self.adj.get(other, []):
                                if neighbor == curr:
                                    visited.add(other)
                                    queue.append(other)
                                    break
                components.append(sorted(comp))
        return components

    def get_graph_metrics(self) -> Dict[str, Any]:
        """Calculate network-level graph metrics: |V|, |E|, density, components, degrees."""
        v_count = len(self.places_by_id)
        components = self.get_connected_components()

        # Count unique edges
        unique_edges: Set[Tuple[int, int]] = set()
        for conn in self.connections:
            u, v = conn.source_destination_id, conn.target_destination_id
            if u in self.places_by_id and v in self.places_by_id:
                if conn.is_directed:
                    unique_edges.add((u, v))
                else:
                    unique_edges.add((min(u, v), max(u, v)))
        e_count = len(unique_edges)

        # Graph density for undirected graph: 2|E| / (|V|(|V|-1))
        density = 0.0
        if v_count > 1:
            density = (2.0 * e_count) / (v_count * (v_count - 1))

        degrees = [len(self.adj[nid]) for nid in self.places_by_id]
        avg_degree = sum(degrees) / v_count if v_count > 0 else 0.0

        isolated_nodes = [
            {"id": nid, "name": self.places_by_id[nid].name}
            for nid in self.places_by_id
            if len(self.adj[nid]) == 0
        ]

        verified_c = sum(1 for c in self.connections if getattr(c, "verification_status", None) == "verified")
        verified_r = verified_c / max(1, len(self.connections)) if self.connections else 1.0

        return {
            "vertex_count": v_count,
            "node_count": v_count,
            "edge_count": e_count,
            "density": round(density, 4),
            "average_degree": round(avg_degree, 2),
            "avg_degree": round(avg_degree, 2),
            "component_count": len(components),
            "connected_components": len(components),
            "is_connected": len(components) <= 1,
            "isolated_count": len(isolated_nodes),
            "isolated_nodes": isolated_nodes,
            "verified_count": verified_c,
            "verified_ratio": round(verified_r, 4),
            "weight_metric": self.weight_metric,
            "transport_mode": self.transport_mode or "all",
        }

    def serialize_for_ui(self) -> Dict[str, Any]:
        """Serialize complete graph structure for Leaflet Map and Abstract Canvas."""
        nodes = []
        for p in self.places:
            deg = self.get_node_degree(p.id)
            nodes.append({
                "id": p.id,
                "name": p.name,
                "slug": p.slug,
                "category": p.category.name if p.category else "Other",
                "category_slug": p.category.slug if p.category else "other",
                "district": p.district.name if p.district else "Unknown",
                "locality": p.locality,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "lat": p.latitude,
                "lng": p.longitude,
                "has_coordinates": p.has_coordinates,
                "coordinates_verified": p.coordinates_verified,
                "popularity": p.popularity,
                "image_url": p.image_url,
                "typical_visit_hours": p.typical_visit_hours or 1.5,
                "degree": deg["total_degree"],
                "in_degree": deg["in_degree"],
                "out_degree": deg["out_degree"],
            })

        edges = []
        seen = set()
        for conn in self.connections:
            u, v = conn.source_destination_id, conn.target_destination_id
            if u not in self.places_by_id or v not in self.places_by_id:
                continue

            pair_key = (u, v) if conn.is_directed else (min(u, v), max(u, v))
            if pair_key in seen:
                continue
            seen.add(pair_key)

            w = self.calculate_weight(conn)
            edges.append({
                "id": conn.id,
                "source": u,
                "target": v,
                "source_name": self.places_by_id[u].name,
                "target_name": self.places_by_id[v].name,
                "source_lat": self.places_by_id[u].latitude,
                "source_lng": self.places_by_id[u].longitude,
                "target_lat": self.places_by_id[v].latitude,
                "target_lng": self.places_by_id[v].longitude,
                "is_directed": conn.is_directed,
                "distance_km": round(conn.distance_km, 2),
                "travel_time_minutes": round(conn.travel_time_minutes, 1),
                "estimated_cost": round(conn.estimated_cost, 2) if conn.estimated_cost is not None else None,
                "weight": round(w, 4),
                "transport_mode": conn.transport_mode,
                "connection_type": conn.connection_type,
                "verification_status": conn.verification_status,
                "data_source": conn.data_source,
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "metrics": self.get_graph_metrics(),
            "components": self.get_connected_components(),
        }

    def audit_data_quality(self) -> Dict[str, Any]:
        """Perform comprehensive data-quality audit per Section 14."""
        missing_coords = [p.name for p in self.places if not p.has_coordinates]
        missing_time = [
            f"{c.source_place.name} -> {c.target_place.name}"
            for c in self.connections
            if c.travel_time_minutes is None or c.travel_time_minutes <= 0
        ]
        missing_distance = [
            f"{c.source_place.name} -> {c.target_place.name}"
            for c in self.connections
            if c.distance_km is None or c.distance_km <= 0
        ]
        missing_cost = [
            f"{c.source_place.name} -> {c.target_place.name}"
            for c in self.connections
            if c.estimated_cost is None
        ]

        verified_count = sum(1 for c in self.connections if c.verification_status == "verified")
        estimated_count = sum(1 for c in self.connections if c.verification_status == "estimated")
        illustrative_count = sum(1 for c in self.connections if c.verification_status == "illustrative")

        components = self.get_connected_components()

        return {
            "total_destinations": len(self.places),
            "destinations_missing_coordinates": missing_coords,
            "total_connections": len(self.connections),
            "verified_connections": verified_count,
            "estimated_connections": estimated_count,
            "illustrative_connections": illustrative_count,
            "connections_missing_time": missing_time,
            "connections_missing_distance": missing_distance,
            "connections_missing_cost": missing_cost,
            "connected_components_count": len(components),
            "is_fully_connected": len(components) <= 1,
            "isolated_nodes": [p.name for p in self.places if len(self.adj[p.id]) == 0],
            "missing_coords_nodes": missing_coords,
        }

    def audit_network_data(self) -> Dict[str, Any]:
        """Alias for audit_data_quality for testing and monitoring."""
        return self.audit_data_quality()
