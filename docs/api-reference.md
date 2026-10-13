# Smart Route Lab — REST API Reference

All Smart Route Lab endpoints reside under `/api/smart-route/`. Internal machine-to-machine AJAX requests are CSRF-exempted. Responses are formatted as `application/json`.

---

## 1. Graph Topology & Metrics

### `GET /api/smart-route/graph`
Returns all vertices, highway edges, connected components, and metrics.

**Query Parameters:**
- `weight_metric` *(string, optional, default: `"time"`)*: `"time"`, `"distance"`, `"cost"`, or `"balanced"`.
- `transport_mode` *(string, optional)*: Filter by `"car"`, `"bus"`, etc.

**Response (200 OK):**
```json
{
  "success": true,
  "nodes": [
    {
      "id": 1,
      "name": "Ujjayanta Palace",
      "lat": 23.8364,
      "lng": 91.2775,
      "category": "Heritage",
      "popularity": 95,
      "degree": 5
    }
  ],
  "edges": [
    {
      "id": 1,
      "source": 1,
      "target": 3,
      "distance_km": 54.2,
      "travel_time_minutes": 78.0,
      "estimated_cost": 650.0,
      "weight": 78.0
    }
  ],
  "metrics": {
    "node_count": 15,
    "edge_count": 25,
    "density": 0.2381,
    "avg_degree": 3.33,
    "connected_components": 1,
    "verified_ratio": 1.0
  }
}
```

---

### `GET /api/smart-route/metrics`
Returns graph connectivity metrics and a comprehensive data quality audit report.

**Response (200 OK):**
```json
{
  "success": true,
  "metrics": { ... },
  "data_quality_audit": {
    "total_destinations": 15,
    "destinations_missing_coordinates": [],
    "total_connections": 25,
    "verified_connections": 25,
    "is_fully_connected": true,
    "isolated_nodes": []
  }
}
```

---

## 2. Algorithm Computation Endpoints

### `POST /api/smart-route/shortest-path`
Executes Dijkstra's algorithm between a source and target vertex.

**Request Body (JSON):**
```json
{
  "start_id": 1,
  "target_id": 3,
  "weight_metric": "time"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "reachable": true,
  "start_id": 1,
  "target_id": 3,
  "path_node_ids": [1, 2, 3],
  "total_distance_km": 54.2,
  "total_time_minutes": 78.0,
  "total_estimated_cost": 650.0,
  "algorithm": "Dijkstra",
  "guarantee": "exact_shortest_path",
  "steps": [ ... ]
}
```

---

### `POST /api/smart-route/astar`
Executes A* search using Haversine admissible heuristic.

**Request Body (JSON):**
```json
{
  "start_id": 1,
  "target_id": 7,
  "weight_metric": "distance"
}
```

---

### `GET` / `POST /api/smart-route/spanning-tree`
Computes the Minimum Spanning Tree (MST) using Kruskal's algorithm with Disjoint-Set Union.

**Query / Body Parameters:**
- `weight_metric` *(string, default: `"distance"`)*.

**Response (200 OK):**
```json
{
  "success": true,
  "algorithm": "Kruskal's MST",
  "guarantee": "exact_mst",
  "total_vertices": 15,
  "tree_edges": [ ... ],
  "mst_edge_count": 14,
  "total_weight": 412.5,
  "steps": [ ... ]
}
```

---

### `GET` / `POST /api/smart-route/bfs-dfs`
Executes Breadth-First Search (BFS) or Depth-First Search (DFS).

**Query / Body Parameters:**
- `start_id` *(int, required)*
- `mode` or `algo` *(string, `"bfs"` or `"dfs"`)*

---

### `POST /api/smart-route/multi-stop`
Computes an optimal Travelling Salesperson tour visiting all specified destination stops.

**Request Body (JSON):**
```json
{
  "start_id": 1,
  "stop_ids": [3, 5, 8],
  "weight_metric": "time",
  "return_to_start": true
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "algorithm": "Held-Karp Dynamic Programming (Bitmask)",
  "guarantee": "exact_tsp",
  "ordered_stop_ids": [1, 3, 5, 8, 1],
  "tour_node_ids": [1, 3, 5, 8, 1],
  "path_node_ids": [1, 2, 3, 5, 8, 1],
  "total_distance_km": 185.4,
  "total_time_minutes": 270.0,
  "steps": [ ... ]
}
```

---

## 3. Journey Planning & Optimization

### `POST /api/smart-route/personalize`
Synthesizes a personalized, constraint-validated multi-day journey with daily timetable schedules.

**Request Body (JSON):**
```json
{
  "start_id": 1,
  "duration_days": 2,
  "interests": ["heritage", "spiritual"],
  "pace": "moderate",
  "max_daily_travel_hours": 6.0
}
```

---

### `GET` / `POST /api/smart-route/compare`
Compares route alternatives across Distance, Time, Cost, and Balanced objectives and computes Pareto dominance.

**Query / Body Parameters:**
- `start_id` *(int, required)*
- `target_id` or `stop_ids` *(int or list of ints, required)*

**Response (200 OK):**
```json
{
  "success": true,
  "candidates": [
    {
      "objective": "time",
      "distance_km": 54.2,
      "time_minutes": 78.0,
      "cost_inr": 650.0,
      "is_pareto_optimal": true,
      "dominated_by": []
    }
  ],
  "routes": [ ... ],
  "trade_off_notes": [ ... ]
}
```

---

### `POST /api/smart-route/parse-query`
Parses natural language requests into structured planner parameters.

**Request Body (JSON):**
```json
{
  "query": "3-day spiritual and lake tour starting from Agartala"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "parsed": {
    "days": 3,
    "origin_id": 1,
    "primary_interest": "spiritual",
    "pace": "balanced"
  }
}
```

---

## 4. Route Persistence & Retrieval

### `POST /api/smart-route/save`
Persists a computed route to the database and generates a unique shareable token.

### `GET /api/smart-route/saved/<int:route_id>`
Retrieves saved route data by ID (with optional `token` query param).
