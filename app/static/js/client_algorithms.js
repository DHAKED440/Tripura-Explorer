/**
 * Client-Side Graph Algorithms Engine & ApiClient
 * Provides 100% offline-capable generator functions yielding step-by-step
 * execution snapshots for interactive playback across Graph Explorer & Tourist Mode.
 *
 * Each step object shape:
 * {
 *   currentNode: number | null,
 *   visited: number[],
 *   frontier: number[],
 *   distances: Object<number, number>,
 *   parent: Object<number, number | null>,
 *   relaxedEdge: { source: number, target: number, weight: number } | null,
 *   done: boolean,
 *   action: string,
 *   explanation: string,
 *   pathNodeIds?: number[],
 *   totalCost?: number,
 *   open_set?: Array<{ node_id: number, node_name: string, cost?: number }>,
 *   closed_set?: number[]
 * }
 */

(function (window) {
  'use strict';

  // --- Geodesic Haversine Distance (km) ---
  function haversineKm(lat1, lon1, lat2, lon2) {
    if (lat1 == null || lon1 == null || lat2 == null || lon2 == null) return 0;
    const R = 6371.0; // Earth mean radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180.0;
    const dLon = (lon2 - lon1) * Math.PI / 180.0;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180.0) *
      Math.cos(lat2 * Math.PI / 180.0) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  // --- Graph Structure Builder ---
  function buildGraphAdjacency(nodes, edges, weightMetric) {
    const nodesMap = new Map();
    nodes.forEach(n => nodesMap.set(n.id, n));

    let maxDist = 1.0;
    let maxTime = 1.0;
    let maxCost = 1.0;

    edges.forEach(e => {
      if (e.distance_km && e.distance_km > maxDist) maxDist = e.distance_km;
      if (e.travel_time_minutes && e.travel_time_minutes > maxTime) maxTime = e.travel_time_minutes;
      const c = e.estimated_cost != null ? e.estimated_cost : (e.distance_km ? e.distance_km * 12.0 : 50);
      if (c > maxCost) maxCost = c;
    });

    const getEdgeWeight = (e) => {
      const metric = (weightMetric || 'time').toLowerCase();
      if (metric === 'distance') {
        return Number(e.distance_km || 1.0);
      } else if (metric === 'cost') {
        return Number(e.estimated_cost != null ? e.estimated_cost : (e.distance_km || 1) * 12.0);
      } else if (metric === 'balanced') {
        const dNorm = (e.distance_km || 1.0) / maxDist;
        const tNorm = (e.travel_time_minutes || 1.0) / maxTime;
        const costVal = e.estimated_cost != null ? e.estimated_cost : (e.distance_km || 1) * 12.0;
        const cNorm = costVal / maxCost;
        return Number((0.33 * dNorm + 0.34 * tNorm + 0.33 * cNorm).toFixed(4));
      } else {
        // default: travel time in minutes
        return Number(e.travel_time_minutes || 10.0);
      }
    };

    const adj = new Map();
    nodes.forEach(n => adj.set(n.id, []));

    const processedEdges = [];

    edges.forEach(e => {
      const u = e.source;
      const v = e.target;
      if (!nodesMap.has(u) || !nodesMap.has(v)) return;

      const w = getEdgeWeight(e);
      const edgeObj = {
        id: e.id,
        source: u,
        target: v,
        weight: w,
        distance_km: Number(e.distance_km || 0),
        travel_time_minutes: Number(e.travel_time_minutes || 0),
        estimated_cost: Number(e.estimated_cost != null ? e.estimated_cost : (e.distance_km || 0) * 12.0),
        is_directed: Boolean(e.is_directed),
        raw: e,
      };

      processedEdges.push(edgeObj);

      if (!adj.has(u)) adj.set(u, []);
      adj.get(u).push({ neighborId: v, weight: w, edge: edgeObj });

      if (!e.is_directed) {
        if (!adj.has(v)) adj.set(v, []);
        adj.get(v).push({ neighborId: u, weight: w, edge: edgeObj });
      }
    });

    return {
      nodes,
      edges: processedEdges,
      nodesMap,
      adj,
      getEdgeWeight,
      maxDist,
      maxTime,
      maxCost,
    };
  }

  // --- Path Reconstruction Helper ---
  function reconstructPath(parent, startId, targetId) {
    if (targetId == null || parent[targetId] === undefined && startId !== targetId) {
      return [];
    }
    const path = [];
    let curr = targetId;
    while (curr != null) {
      path.unshift(curr);
      if (curr === startId) break;
      curr = parent[curr];
    }
    return path[0] === startId ? path : [];
  }

  // Calculate aggregate metrics for a node path sequence
  function calculatePathMetrics(pathNodeIds, graph) {
    let totalDist = 0;
    let totalTime = 0;
    let totalCost = 0;

    for (let i = 0; i < pathNodeIds.length - 1; i++) {
      const u = pathNodeIds[i];
      const v = pathNodeIds[i + 1];
      const neighbors = graph.adj.get(u) || [];
      const conn = neighbors.find(n => n.neighborId === v);
      if (conn && conn.edge) {
        totalDist += conn.edge.distance_km;
        totalTime += conn.edge.travel_time_minutes;
        totalCost += conn.edge.estimated_cost;
      } else {
        const uNode = graph.nodesMap.get(u);
        const vNode = graph.nodesMap.get(v);
        const est = (uNode && vNode) ? haversineKm(uNode.latitude, uNode.longitude, vNode.latitude, vNode.longitude) : 10;
        totalDist += est;
        totalTime += est * 1.5;
        totalCost += est * 12;
      }
    }

    return { totalDist, totalTime, totalCost };
  }

  // =========================================================================
  // 1. Breadth-First Search (BFS) Generator
  // =========================================================================
  function* bfsGenerator(graph, startId, targetId) {
    console.log(`[BFS] Initializing search: start=${startId}, target=${targetId}`);
    const visited = new Set();
    const queue = [startId];
    visited.add(startId);

    const parent = { [startId]: null };
    const distances = { [startId]: 0 };

    yield {
      currentNode: startId,
      visited: Array.from(visited),
      frontier: [...queue],
      distances: { ...distances },
      parent: { ...parent },
      relaxedEdge: null,
      done: false,
      action: 'Initialize BFS',
      explanation: `Initialized BFS at source vertex ${graph.nodesMap.get(startId)?.name || startId}. Enqueued to frontier.`,
      open_set: queue.map(nid => ({ node_id: nid, node_name: graph.nodesMap.get(nid)?.name || nid })),
      closed_set: [],
    };

    while (queue.length > 0) {
      const u = queue.shift();
      const uName = graph.nodesMap.get(u)?.name || u;

      yield {
        currentNode: u,
        visited: Array.from(visited),
        frontier: [...queue],
        distances: { ...distances },
        parent: { ...parent },
        relaxedEdge: null,
        done: false,
        action: 'Dequeue Vertex',
        explanation: `Dequeued vertex ${uName} from frontier. Exploring outward highway connections.`,
        open_set: queue.map(nid => ({ node_id: nid, node_name: graph.nodesMap.get(nid)?.name || nid })),
        closed_set: Array.from(visited),
      };

      if (targetId != null && u === targetId) {
        const path = reconstructPath(parent, startId, targetId);
        const metrics = calculatePathMetrics(path, graph);
        yield {
          currentNode: u,
          visited: Array.from(visited),
          frontier: [...queue],
          distances: { ...distances },
          parent: { ...parent },
          relaxedEdge: null,
          done: true,
          pathNodeIds: path,
          totalCost: distances[u],
          total_distance_km: metrics.totalDist,
          total_time_minutes: metrics.totalTime,
          total_cost_inr: metrics.totalCost,
          action: 'Target Discovered',
          explanation: `Target vertex ${uName} reached! Reconstructed shortest unweighted path (${path.length} hops).`,
          open_set: [],
          closed_set: Array.from(visited),
        };
        return;
      }

      const neighbors = graph.adj.get(u) || [];
      for (const { neighborId: v, weight } of neighbors) {
        if (!visited.has(v)) {
          visited.add(v);
          parent[v] = u;
          distances[v] = (distances[u] || 0) + 1;
          queue.push(v);

          const vName = graph.nodesMap.get(v)?.name || v;
          yield {
            currentNode: u,
            visited: Array.from(visited),
            frontier: [...queue],
            distances: { ...distances },
            parent: { ...parent },
            relaxedEdge: { source: u, target: v, weight: 1 },
            done: false,
            action: 'Discover & Enqueue',
            explanation: `Discovered unvisited neighbor ${vName} via edge (${uName} -> ${vName}). tentative hop distance = ${distances[v]}.`,
            open_set: queue.map(nid => ({ node_id: nid, node_name: graph.nodesMap.get(nid)?.name || nid })),
            closed_set: Array.from(visited),
          };

          if (targetId != null && v === targetId) {
            const path = reconstructPath(parent, startId, targetId);
            const metrics = calculatePathMetrics(path, graph);
            yield {
              currentNode: v,
              visited: Array.from(visited),
              frontier: [...queue],
              distances: { ...distances },
              parent: { ...parent },
              relaxedEdge: { source: u, target: v, weight: 1 },
              done: true,
              pathNodeIds: path,
              totalCost: distances[v],
              total_distance_km: metrics.totalDist,
              total_time_minutes: metrics.totalTime,
              total_cost_inr: metrics.totalCost,
              action: 'Target Discovered',
              explanation: `Target vertex ${vName} discovered! Shortest unweighted corridor found.`,
              open_set: [],
              closed_set: Array.from(visited),
            };
            return;
          }
        }
      }
    }

    const path = targetId != null ? reconstructPath(parent, startId, targetId) : [];
    yield {
      currentNode: null,
      visited: Array.from(visited),
      frontier: [],
      distances: { ...distances },
      parent: { ...parent },
      relaxedEdge: null,
      done: true,
      pathNodeIds: path,
      action: targetId != null && path.length === 0 ? 'No Path Found' : 'BFS Traversal Complete',
      explanation: targetId != null && path.length === 0
        ? `No connecting path exists between ${graph.nodesMap.get(startId)?.name || startId} and ${graph.nodesMap.get(targetId)?.name || targetId} (disconnected network components).`
        : `Completed complete BFS traversal. Explored ${visited.size} reachable destinations.`,
      open_set: [],
      closed_set: Array.from(visited),
    };
  }

  // =========================================================================
  // 2. Depth-First Search (DFS) Generator
  // =========================================================================
  function* dfsGenerator(graph, startId, targetId) {
    console.log(`[DFS] Initializing search: start=${startId}, target=${targetId}`);
    const visited = new Set();
    const stack = [startId];
    const parent = { [startId]: null };
    const distances = { [startId]: 0 };

    yield {
      currentNode: startId,
      visited: [],
      frontier: [...stack],
      distances: { ...distances },
      parent: { ...parent },
      relaxedEdge: null,
      done: false,
      action: 'Initialize DFS',
      explanation: `Initialized DFS stack with start vertex ${graph.nodesMap.get(startId)?.name || startId}.`,
      open_set: stack.map(nid => ({ node_id: nid, node_name: graph.nodesMap.get(nid)?.name || nid })),
      closed_set: [],
    };

    while (stack.length > 0) {
      const u = stack.pop();
      if (visited.has(u)) continue;

      visited.add(u);
      const uName = graph.nodesMap.get(u)?.name || u;

      yield {
        currentNode: u,
        visited: Array.from(visited),
        frontier: [...stack],
        distances: { ...distances },
        parent: { ...parent },
        relaxedEdge: null,
        done: false,
        action: 'Visit Vertex',
        explanation: `Popped ${uName} from DFS stack. Marking as visited.`,
        open_set: stack.map(nid => ({ node_id: nid, node_name: graph.nodesMap.get(nid)?.name || nid })),
        closed_set: Array.from(visited),
      };

      if (targetId != null && u === targetId) {
        const path = reconstructPath(parent, startId, targetId);
        const metrics = calculatePathMetrics(path, graph);
        yield {
          currentNode: u,
          visited: Array.from(visited),
          frontier: [...stack],
          distances: { ...distances },
          parent: { ...parent },
          relaxedEdge: null,
          done: true,
          pathNodeIds: path,
          totalCost: distances[u] || path.length,
          total_distance_km: metrics.totalDist,
          total_time_minutes: metrics.totalTime,
          total_cost_inr: metrics.totalCost,
          action: 'Target Discovered',
          explanation: `DFS reached target vertex ${uName}! Reconstructed deep traversal path.`,
          open_set: [],
          closed_set: Array.from(visited),
        };
        return;
      }

      const neighbors = graph.adj.get(u) || [];
      // Push neighbors in reverse order for intuitive exploration
      for (let i = neighbors.length - 1; i >= 0; i--) {
        const { neighborId: v } = neighbors[i];
        if (!visited.has(v)) {
          if (parent[v] === undefined) {
            parent[v] = u;
            distances[v] = (distances[u] || 0) + 1;
          }
          stack.push(v);

          yield {
            currentNode: u,
            visited: Array.from(visited),
            frontier: [...stack],
            distances: { ...distances },
            parent: { ...parent },
            relaxedEdge: { source: u, target: v, weight: 1 },
            done: false,
            action: 'Push to Stack',
            explanation: `Pushed adjacent vertex ${graph.nodesMap.get(v)?.name || v} onto DFS stack.`,
            open_set: stack.map(nid => ({ node_id: nid, node_name: graph.nodesMap.get(nid)?.name || nid })),
            closed_set: Array.from(visited),
          };
        }
      }
    }

    const path = targetId != null ? reconstructPath(parent, startId, targetId) : [];
    yield {
      currentNode: null,
      visited: Array.from(visited),
      frontier: [],
      distances: { ...distances },
      parent: { ...parent },
      relaxedEdge: null,
      done: true,
      pathNodeIds: path,
      action: targetId != null && path.length === 0 ? 'No Path Found' : 'DFS Complete',
      explanation: targetId != null && path.length === 0
        ? `No path found between ${graph.nodesMap.get(startId)?.name || startId} and ${graph.nodesMap.get(targetId)?.name || targetId}.`
        : `DFS traversal complete. Total nodes visited: ${visited.size}.`,
      open_set: [],
      closed_set: Array.from(visited),
    };
  }

  // =========================================================================
  // 3. Dijkstra's Algorithm Generator
  // =========================================================================
  function* dijkstraGenerator(graph, startId, targetId, weightMetric) {
    console.log(`[Dijkstra] Initializing search: start=${startId}, target=${targetId}, metric=${weightMetric}`);
    const distances = {};
    const parent = {};
    const visited = new Set();

    graph.nodes.forEach(n => {
      distances[n.id] = Infinity;
      parent[n.id] = null;
    });
    distances[startId] = 0;

    // Check negative weights
    const hasNegativeWeights = graph.edges.some(e => e.weight < 0);
    if (hasNegativeWeights) {
      console.warn('[Dijkstra] Warning: Graph contains negative weights. Dijkstra may yield suboptimal results.');
    }

    // Min-priority queue: [{ node: id, cost: num }]
    const pq = [{ node: startId, cost: 0 }];

    const startName = graph.nodesMap.get(startId)?.name || startId;
    yield {
      currentNode: startId,
      visited: [],
      frontier: [startId],
      distances: { ...distances },
      parent: { ...parent },
      relaxedEdge: null,
      done: false,
      action: 'Initialize Dijkstra',
      explanation: `Set d(${startName}) = 0.0 and all other tentative distances to ∞. Inserted source vertex into priority queue Q.`,
      open_set: [{ node_id: startId, node_name: startName, cost: 0 }],
      closed_set: [],
    };

    while (pq.length > 0) {
      // Extract minimum
      pq.sort((a, b) => a.cost - b.cost);
      const { node: u, cost: uDist } = pq.shift();

      if (visited.has(u)) continue;
      visited.add(u);

      const uName = graph.nodesMap.get(u)?.name || u;
      yield {
        currentNode: u,
        visited: Array.from(visited),
        frontier: pq.map(item => item.node),
        distances: { ...distances },
        parent: { ...parent },
        relaxedEdge: null,
        done: false,
        action: 'Extract Min Vertex',
        explanation: `Extracted vertex ${uName} with minimum tentative distance d = ${uDist.toFixed(1)}. Added to closed set S.`,
        open_set: pq.map(i => ({ node_id: i.node, node_name: graph.nodesMap.get(i.node)?.name || i.node, cost: i.cost })),
        closed_set: Array.from(visited),
      };

      if (targetId != null && u === targetId) {
        const path = reconstructPath(parent, startId, targetId);
        const metrics = calculatePathMetrics(path, graph);
        yield {
          currentNode: u,
          visited: Array.from(visited),
          frontier: pq.map(item => item.node),
          distances: { ...distances },
          parent: { ...parent },
          relaxedEdge: null,
          done: true,
          pathNodeIds: path,
          totalCost: distances[u],
          total_distance_km: metrics.totalDist,
          total_time_minutes: metrics.totalTime,
          total_cost_inr: metrics.totalCost,
          action: 'Target Reached (Optimal)',
          explanation: `Optimal shortest path reached at target ${uName}! Total cost = ${distances[u].toFixed(1)} (${metrics.totalDist.toFixed(1)} km, ${metrics.totalTime.toFixed(0)} min).`,
          open_set: [],
          closed_set: Array.from(visited),
        };
        return;
      }

      // Relax outgoing edges
      const neighbors = graph.adj.get(u) || [];
      for (const { neighborId: v, weight, edge } of neighbors) {
        if (visited.has(v)) continue;

        const newDist = distances[u] + weight;
        if (newDist < distances[v]) {
          const oldDist = distances[v];
          distances[v] = newDist;
          parent[v] = u;

          // Update priority queue
          const existingIdx = pq.findIndex(item => item.node === v);
          if (existingIdx >= 0) {
            pq[existingIdx].cost = newDist;
          } else {
            pq.push({ node: v, cost: newDist });
          }

          const vName = graph.nodesMap.get(v)?.name || v;
          yield {
            currentNode: u,
            visited: Array.from(visited),
            frontier: pq.map(item => item.node),
            distances: { ...distances },
            parent: { ...parent },
            relaxedEdge: { source: u, target: v, weight },
            done: false,
            action: 'Relax Edge',
            explanation: `Relaxed corridor (${uName} -> ${vName}): d[${vName}] improved from ${oldDist === Infinity ? '∞' : oldDist.toFixed(1)} to ${newDist.toFixed(1)}.`,
            open_set: pq.map(i => ({ node_id: i.node, node_name: graph.nodesMap.get(i.node)?.name || i.node, cost: i.cost })),
            closed_set: Array.from(visited),
          };
        }
      }
    }

    const path = targetId != null ? reconstructPath(parent, startId, targetId) : [];
    yield {
      currentNode: null,
      visited: Array.from(visited),
      frontier: [],
      distances: { ...distances },
      parent: { ...parent },
      relaxedEdge: null,
      done: true,
      pathNodeIds: path,
      action: path.length === 0 ? 'No Path Found' : 'Dijkstra Complete',
      explanation: path.length === 0
        ? `No connecting road path exists between ${startName} and target in this network.`
        : `Dijkstra solved all single-source shortest paths from ${startName}.`,
      open_set: [],
      closed_set: Array.from(visited),
    };
  }

  // =========================================================================
  // 4. A* Search Generator (Haversine Admissible Heuristic)
  // =========================================================================
  function* astarGenerator(graph, startId, targetId, weightMetric) {
    console.log(`[A* Search] Initializing: start=${startId}, target=${targetId}`);
    if (targetId == null) {
      // A* requires a goal node
      yield* dijkstraGenerator(graph, startId, targetId, weightMetric);
      return;
    }

    const targetNode = graph.nodesMap.get(targetId);
    if (!targetNode) {
      yield* dijkstraGenerator(graph, startId, targetId, weightMetric);
      return;
    }

    // Heuristic function: Great-circle distance converted to selected metric unit
    const h = (node) => {
      if (!node || node.latitude == null || targetNode.latitude == null) return 0;
      const distKm = haversineKm(node.latitude, node.longitude, targetNode.latitude, targetNode.longitude);
      const metric = (weightMetric || 'time').toLowerCase();
      if (metric === 'distance') {
        return distKm; // straight-line distance <= road distance
      } else if (metric === 'cost') {
        return distKm * 10.0; // conservative fuel estimate
      } else {
        // default time: assume maximum possible average highway speed (75 km/h)
        return (distKm / 75.0) * 60.0;
      }
    };

    const gScore = {};
    const fScore = {};
    const parent = {};
    const visited = new Set();

    graph.nodes.forEach(n => {
      gScore[n.id] = Infinity;
      fScore[n.id] = Infinity;
      parent[n.id] = null;
    });

    gScore[startId] = 0;
    fScore[startId] = h(graph.nodesMap.get(startId));

    const openSet = [{ node: startId, f: fScore[startId], g: 0 }];

    const startName = graph.nodesMap.get(startId)?.name || startId;
    const targetName = targetNode.name || targetId;

    yield {
      currentNode: startId,
      visited: [],
      frontier: [startId],
      distances: { ...gScore },
      parent: { ...parent },
      relaxedEdge: null,
      done: false,
      action: 'Initialize A*',
      explanation: `Initialized A* heuristic search to goal ${targetName}. h(${startName}) = ${fScore[startId].toFixed(1)}.`,
      open_set: openSet.map(i => ({ node_id: i.node, node_name: graph.nodesMap.get(i.node)?.name || i.node, cost: i.f })),
      closed_set: [],
    };

    while (openSet.length > 0) {
      openSet.sort((a, b) => a.f - b.f);
      const current = openSet.shift();
      const u = current.node;

      if (visited.has(u)) continue;
      visited.add(u);

      const uName = graph.nodesMap.get(u)?.name || u;

      yield {
        currentNode: u,
        visited: Array.from(visited),
        frontier: openSet.map(i => i.node),
        distances: { ...gScore },
        parent: { ...parent },
        relaxedEdge: null,
        done: false,
        action: 'Expand Vertex',
        explanation: `Expanding lowest f(n) vertex ${uName}: g = ${gScore[u].toFixed(1)}, h = ${(fScore[u] - gScore[u]).toFixed(1)}, f = ${fScore[u].toFixed(1)}.`,
        open_set: openSet.map(i => ({ node_id: i.node, node_name: graph.nodesMap.get(i.node)?.name || i.node, cost: i.f })),
        closed_set: Array.from(visited),
      };

      if (u === targetId) {
        const path = reconstructPath(parent, startId, targetId);
        const metrics = calculatePathMetrics(path, graph);
        yield {
          currentNode: u,
          visited: Array.from(visited),
          frontier: openSet.map(i => i.node),
          distances: { ...gScore },
          parent: { ...parent },
          relaxedEdge: null,
          done: true,
          pathNodeIds: path,
          totalCost: gScore[u],
          total_distance_km: metrics.totalDist,
          total_time_minutes: metrics.totalTime,
          total_cost_inr: metrics.totalCost,
          action: 'Goal Reached (A* Optimal)',
          explanation: `A* goal discovered with admissible lower bound! Optimal path length: ${metrics.totalDist.toFixed(1)} km (${metrics.totalTime.toFixed(0)} min).`,
          open_set: [],
          closed_set: Array.from(visited),
        };
        return;
      }

      const neighbors = graph.adj.get(u) || [];
      for (const { neighborId: v, weight, edge } of neighbors) {
        if (visited.has(v)) continue;

        const tentativeG = gScore[u] + weight;
        if (tentativeG < gScore[v]) {
          parent[v] = u;
          gScore[v] = tentativeG;
          const hVal = h(graph.nodesMap.get(v));
          fScore[v] = tentativeG + hVal;

          const existingIdx = openSet.findIndex(i => i.node === v);
          if (existingIdx >= 0) {
            openSet[existingIdx].f = fScore[v];
            openSet[existingIdx].g = tentativeG;
          } else {
            openSet.push({ node: v, f: fScore[v], g: tentativeG });
          }

          const vName = graph.nodesMap.get(v)?.name || v;
          yield {
            currentNode: u,
            visited: Array.from(visited),
            frontier: openSet.map(i => i.node),
            distances: { ...gScore },
            parent: { ...parent },
            relaxedEdge: { source: u, target: v, weight },
            done: false,
            action: 'Evaluate Neighbor',
            explanation: `Relaxed neighbor ${vName}: g=${tentativeG.toFixed(1)} + h=${hVal.toFixed(1)} => f=${fScore[v].toFixed(1)}.`,
            open_set: openSet.map(i => ({ node_id: i.node, node_name: graph.nodesMap.get(i.node)?.name || i.node, cost: i.f })),
            closed_set: Array.from(visited),
          };
        }
      }
    }

    const path = reconstructPath(parent, startId, targetId);
    yield {
      currentNode: null,
      visited: Array.from(visited),
      frontier: [],
      distances: { ...gScore },
      parent: { ...parent },
      relaxedEdge: null,
      done: true,
      pathNodeIds: path,
      action: 'Search Exhausted',
      explanation: path.length === 0 ? 'No viable path exists between selected endpoints.' : 'A* complete.',
      open_set: [],
      closed_set: Array.from(visited),
    };
  }

  // =========================================================================
  // 5. Bellman-Ford Algorithm Generator
  // =========================================================================
  function* bellmanFordGenerator(graph, startId, targetId, weightMetric) {
    console.log(`[Bellman-Ford] Initializing: start=${startId}, target=${targetId}`);
    const distances = {};
    const parent = {};
    const V = graph.nodes.length;

    graph.nodes.forEach(n => {
      distances[n.id] = Infinity;
      parent[n.id] = null;
    });
    distances[startId] = 0;

    // Collect all directed edge segments
    const allEdges = [];
    graph.nodes.forEach(uNode => {
      const neighbors = graph.adj.get(uNode.id) || [];
      neighbors.forEach(({ neighborId: v, weight, edge }) => {
        allEdges.push({ u: uNode.id, v, weight, edge });
      });
    });

    const startName = graph.nodesMap.get(startId)?.name || startId;
    yield {
      currentNode: startId,
      visited: [startId],
      frontier: [],
      distances: { ...distances },
      parent: { ...parent },
      relaxedEdge: null,
      done: false,
      action: 'Initialize Bellman-Ford',
      explanation: `Initialized Bellman-Ford: d(${startName}) = 0. All other ${V - 1} vertices initialized to ∞.`,
      open_set: [{ node_id: startId, node_name: startName, cost: 0 }],
      closed_set: [startId],
    };

    // Up to |V| - 1 passes
    for (let pass = 1; pass <= Math.max(1, V - 1); pass++) {
      let relaxedAny = false;

      for (const { u, v, weight } of allEdges) {
        if (distances[u] !== Infinity && distances[u] + weight < distances[v]) {
          const oldDist = distances[v];
          distances[v] = distances[u] + weight;
          parent[v] = u;
          relaxedAny = true;

          const uName = graph.nodesMap.get(u)?.name || u;
          const vName = graph.nodesMap.get(v)?.name || v;

          yield {
            currentNode: v,
            visited: Object.keys(distances).filter(k => distances[k] < Infinity).map(Number),
            frontier: [u, v],
            distances: { ...distances },
            parent: { ...parent },
            relaxedEdge: { source: u, target: v, weight },
            done: false,
            action: `Pass ${pass} Relaxation`,
            explanation: `Pass ${pass}/${V - 1}: Relaxed edge (${uName} -> ${vName}). d[${vName}] improved from ${oldDist === Infinity ? '∞' : oldDist.toFixed(1)} to ${distances[v].toFixed(1)}.`,
            open_set: [{ node_id: v, node_name: vName, cost: distances[v] }],
            closed_set: Object.keys(distances).filter(k => distances[k] < Infinity).map(Number),
          };
        }
      }

      if (!relaxedAny) {
        yield {
          currentNode: null,
          visited: Object.keys(distances).filter(k => distances[k] < Infinity).map(Number),
          frontier: [],
          distances: { ...distances },
          parent: { ...parent },
          relaxedEdge: null,
          done: false,
          action: 'Early Convergence',
          explanation: `No distances improved in Pass ${pass}. Bellman-Ford converged early to global optimal distances!`,
          open_set: [],
          closed_set: Object.keys(distances).filter(k => distances[k] < Infinity).map(Number),
        };
        break;
      }
    }

    // Check for negative weight cycles
    let hasNegativeCycle = false;
    for (const { u, v, weight } of allEdges) {
      if (distances[u] !== Infinity && distances[u] + weight < distances[v]) {
        hasNegativeCycle = true;
        yield {
          currentNode: v,
          visited: [],
          frontier: [u, v],
          distances: { ...distances },
          parent: { ...parent },
          relaxedEdge: { source: u, target: v, weight },
          done: true,
          pathNodeIds: [],
          action: 'Negative Cycle Detected',
          explanation: `Negative cycle detected reachable along corridor (${u} -> ${v})! Shortest paths are undefined.`,
          open_set: [],
          closed_set: [],
        };
        return;
      }
    }

    const path = targetId != null ? reconstructPath(parent, startId, targetId) : [];
    const metrics = calculatePathMetrics(path, graph);
    yield {
      currentNode: targetId,
      visited: Object.keys(distances).filter(k => distances[k] < Infinity).map(Number),
      frontier: [],
      distances: { ...distances },
      parent: { ...parent },
      relaxedEdge: null,
      done: true,
      pathNodeIds: path,
      totalCost: targetId != null ? distances[targetId] : 0,
      total_distance_km: metrics.totalDist,
      total_time_minutes: metrics.totalTime,
      total_cost_inr: metrics.totalCost,
      action: path.length > 0 ? 'Bellman-Ford Optimal' : 'Traversal Complete',
      explanation: path.length > 0
        ? `Bellman-Ford found shortest path to ${graph.nodesMap.get(targetId)?.name || targetId} with cost ${distances[targetId].toFixed(1)}.`
        : `Bellman-Ford execution finished across all highway corridors.`,
      open_set: [],
      closed_set: Object.keys(distances).filter(k => distances[k] < Infinity).map(Number),
    };
  }

  // =========================================================================
  // 6. Kruskal's Minimum Spanning Tree (MST) Generator
  // =========================================================================
  function* kruskalGenerator(graph, weightMetric) {
    console.log(`[Kruskal MST] Computing Minimum Spanning Tree`);
    // Disjoint Set Union (DSU) with Path Compression & Union by Rank
    const parent = {};
    const rank = {};
    graph.nodes.forEach(n => {
      parent[n.id] = n.id;
      rank[n.id] = 0;
    });

    const find = (i) => {
      if (parent[i] === i) return i;
      parent[i] = find(parent[i]);
      return parent[i];
    };

    const union = (rootX, rootY) => {
      if (rank[rootX] < rank[rootY]) {
        parent[rootX] = rootY;
      } else if (rank[rootX] > rank[rootY]) {
        parent[rootY] = rootX;
      } else {
        parent[rootY] = rootX;
        rank[rootX]++;
      }
    };

    // Sort edges ascending by weight
    const sortedEdges = [...graph.edges].sort((a, b) => a.weight - b.weight);
    const treeEdges = [];
    let totalWeight = 0;

    yield {
      currentNode: null,
      visited: [],
      frontier: [],
      distances: {},
      parent: {},
      relaxedEdge: null,
      done: false,
      action: 'Initialize Kruskal',
      explanation: `Sorted ${sortedEdges.length} highway corridors in ascending order of edge cost. Initialized Disjoint-Set Union.`,
      open_set: [],
      closed_set: [],
    };

    for (const edge of sortedEdges) {
      const u = edge.source;
      const v = edge.target;
      const rootU = find(u);
      const rootV = find(v);
      const uName = graph.nodesMap.get(u)?.name || u;
      const vName = graph.nodesMap.get(v)?.name || v;

      if (rootU !== rootV) {
        union(rootU, rootV);
        treeEdges.push(edge);
        totalWeight += edge.weight;

        yield {
          currentNode: v,
          visited: Array.from(new Set(treeEdges.flatMap(e => [e.source, e.target]))),
          frontier: [u, v],
          distances: { total_weight: totalWeight },
          parent: { ...parent },
          relaxedEdge: { source: u, target: v, weight: edge.weight },
          treeEdges: [...treeEdges],
          done: false,
          action: 'Add MST Edge',
          explanation: `Added corridor (${uName} &harr; ${vName}, weight ${edge.weight}) to Spanning Tree. Merged components.`,
          open_set: [],
          closed_set: Array.from(new Set(treeEdges.flatMap(e => [e.source, e.target]))),
        };

        if (treeEdges.length === graph.nodes.length - 1) {
          break; // MST connects all V vertices with V - 1 edges
        }
      } else {
        yield {
          currentNode: null,
          visited: Array.from(new Set(treeEdges.flatMap(e => [e.source, e.target]))),
          frontier: [],
          distances: { total_weight: totalWeight },
          parent: { ...parent },
          relaxedEdge: null,
          treeEdges: [...treeEdges],
          done: false,
          action: 'Reject Cycle Edge',
          explanation: `Rejected edge (${uName} &harr; ${vName}, weight ${edge.weight}) to prevent circular cycle.`,
          open_set: [],
          closed_set: Array.from(new Set(treeEdges.flatMap(e => [e.source, e.target]))),
        };
      }
    }

    yield {
      currentNode: null,
      visited: graph.nodes.map(n => n.id),
      frontier: [],
      distances: { total_weight: totalWeight },
      parent: {},
      relaxedEdge: null,
      tree_edges: treeEdges,
      treeEdges: treeEdges,
      total_weight: totalWeight,
      done: true,
      action: 'MST Complete',
      explanation: `Minimum Spanning Tree synthesized! Connected graph with ${treeEdges.length} backbone edges. Total network weight = ${totalWeight.toFixed(1)}.`,
      open_set: [],
      closed_set: graph.nodes.map(n => n.id),
    };
  }

  // =========================================================================
  // 7. Tourist Mode Multi-Stop Route Generator (Nearest-Neighbor + 2-Opt)
  // =========================================================================
  function* touristGenerator(graph, startId, stopIds, options = {}) {
    console.log(`[Tourist Route] Planning multi-stop journey from ${startId}`, stopIds);

    // Selected stops set (including start hub)
    const distinctStops = Array.from(new Set([startId, ...(stopIds || [])]));

    if (distinctStops.length <= 1) {
      // Pick top destinations as recommendations if none selected
      const topOther = graph.nodes.filter(n => n.id !== startId).slice(0, 4).map(n => n.id);
      distinctStops.push(...topOther);
    }

    yield {
      currentNode: startId,
      visited: [startId],
      frontier: distinctStops,
      distances: {},
      parent: {},
      relaxedEdge: null,
      done: false,
      action: 'Init Tour Itinerary',
      explanation: `Initialized Tourist Multi-Stop Optimization for ${distinctStops.length} stops originating at ${graph.nodesMap.get(startId)?.name || startId}.`,
      open_set: distinctStops.map(id => ({ node_id: id, node_name: graph.nodesMap.get(id)?.name || id })),
      closed_set: [startId],
    };

    // Phase 1: All-Pairs Dijkstra between selected stops
    const pairDist = new Map();
    const pairPath = new Map();

    for (const src of distinctStops) {
      for (const dst of distinctStops) {
        if (src === dst) {
          pairDist.set(`${src}->${dst}`, 0);
          pairPath.set(`${src}->${dst}`, [src]);
          continue;
        }

        // Run local Dijkstra
        const gen = dijkstraGenerator(graph, src, dst, options.weightMetric || 'time');
        let finalStep = null;
        for (const step of gen) {
          finalStep = step;
        }

        const path = (finalStep && finalStep.pathNodeIds && finalStep.pathNodeIds.length > 0)
          ? finalStep.pathNodeIds
          : [src, dst];
        const cost = (finalStep && finalStep.totalCost) ? finalStep.totalCost : 50;

        pairDist.set(`${src}->${dst}`, cost);
        pairPath.set(`${src}->${dst}`, path);
      }
    }

    // Phase 2: Nearest-Neighbor greedy tour construction
    const tourStops = [startId];
    const unvisited = new Set(distinctStops.filter(id => id !== startId));

    while (unvisited.size > 0) {
      const current = tourStops[tourStops.length - 1];
      let bestNext = null;
      let minCost = Infinity;

      for (const candidate of unvisited) {
        const cost = pairDist.get(`${current}->${candidate}`) || Infinity;
        if (cost < minCost) {
          minCost = cost;
          bestNext = candidate;
        }
      }

      if (bestNext == null) {
        bestNext = Array.from(unvisited)[0];
      }

      unvisited.delete(bestNext);
      tourStops.push(bestNext);

      const cName = graph.nodesMap.get(current)?.name || current;
      const nName = graph.nodesMap.get(bestNext)?.name || bestNext;

      yield {
        currentNode: bestNext,
        visited: [...tourStops],
        frontier: Array.from(unvisited),
        distances: { tour_stops_count: tourStops.length },
        parent: {},
        relaxedEdge: { source: current, target: bestNext, weight: minCost },
        done: false,
        action: 'Nearest Neighbor Leg',
        explanation: `Nearest-neighbor step: Connected ${cName} -> ${nName} (metric cost = ${minCost.toFixed(1)}).`,
        open_set: Array.from(unvisited).map(id => ({ node_id: id, node_name: graph.nodesMap.get(id)?.name || id })),
        closed_set: [...tourStops],
      };
    }

    // Close circuit back to start
    tourStops.push(startId);

    // Phase 3: 2-Opt Tour Improvement
    let improved = true;
    let iteration = 0;
    while (improved && iteration < 8) {
      improved = false;
      iteration++;

      for (let i = 1; i < tourStops.length - 2; i++) {
        for (let j = i + 1; j < tourStops.length - 1; j++) {
          const u1 = tourStops[i - 1];
          const v1 = tourStops[i];
          const u2 = tourStops[j];
          const v2 = tourStops[j + 1];

          const dCurrent = (pairDist.get(`${u1}->${v1}`) || 0) + (pairDist.get(`${u2}->${v2}`) || 0);
          const dSwapped = (pairDist.get(`${u1}->${u2}`) || 0) + (pairDist.get(`${v1}->${v2}`) || 0);

          if (dSwapped < dCurrent - 1e-4) {
            // Reverse segment between i and j
            const segment = tourStops.slice(i, j + 1).reverse();
            tourStops.splice(i, segment.length, ...segment);
            improved = true;

            yield {
              currentNode: tourStops[i],
              visited: [...tourStops],
              frontier: [],
              distances: { iteration },
              parent: {},
              relaxedEdge: { source: u1, target: u2, weight: dSwapped },
              done: false,
              action: '2-Opt Improvement Swap',
              explanation: `2-Opt optimized circuit order: untangled route crossing between stops ${i} and ${j} (saved ${(dCurrent - dSwapped).toFixed(1)} metric units).`,
              open_set: [],
              closed_set: [...tourStops],
            };
          }
        }
      }
    }

    // Expand tourStops into full detailed road vertex path
    const fullRoadPath = [];
    const legs = [];
    let cumulativeDist = 0;
    let cumulativeTime = 0;
    let cumulativeCost = 0;

    for (let i = 0; i < tourStops.length - 1; i++) {
      const u = tourStops[i];
      const v = tourStops[i + 1];
      const legPath = pairPath.get(`${u}->${v}`) || [u, v];
      const legMetrics = calculatePathMetrics(legPath, graph);

      legs.push({
        from_id: u,
        to_id: v,
        from_name: graph.nodesMap.get(u)?.name || u,
        to_name: graph.nodesMap.get(v)?.name || v,
        distance_km: legMetrics.totalDist,
        travel_time_minutes: legMetrics.totalTime,
        cost_inr: legMetrics.totalCost,
      });

      cumulativeDist += legMetrics.totalDist;
      cumulativeTime += legMetrics.totalTime;
      cumulativeCost += legMetrics.totalCost;

      if (i === 0) {
        fullRoadPath.push(...legPath);
      } else {
        fullRoadPath.push(...legPath.slice(1));
      }
    }

    // Build day-by-day timetable
    const days = Math.min(4, Math.max(1, options.days || 2));
    const dailyPlans = [];
    const stopsPerDay = Math.ceil((tourStops.length - 1) / days);

    for (let d = 1; d <= days; d++) {
      const startIdx = (d - 1) * stopsPerDay;
      const endIdx = Math.min(tourStops.length - 1, d * stopsPerDay);
      const dayStops = tourStops.slice(startIdx, endIdx + 1);

      const items = [];
      let curHour = 9;

      dayStops.forEach((stopId, idx) => {
        const place = graph.nodesMap.get(stopId);
        const timeStr = `${String(curHour).padStart(2, '0')}:00`;
        items.push({
          time: timeStr,
          title: `Visit ${place?.name || 'Destination'}`,
          details: `${place?.category || 'Highlight'} in ${place?.district || 'Tripura'}. Recommended dwell: ${place?.typical_visit_hours || 1.5} hrs.`,
        });
        curHour += 2;
      });

      dailyPlans.push({
        day_number: d,
        title: d === 1 ? 'Heritage & Imperial Core Circuit' : `Scenic & Regional Explorations (Day ${d})`,
        travel_hours: Math.max(1.5, (cumulativeTime / days) / 60.0),
        schedule_items: items,
      });
    }

    yield {
      currentNode: startId,
      visited: tourStops,
      frontier: [],
      distances: {
        total_distance_km: cumulativeDist,
        total_time_minutes: cumulativeTime,
        total_cost_inr: cumulativeCost,
      },
      parent: {},
      relaxedEdge: null,
      done: true,
      pathNodeIds: fullRoadPath,
      tour_node_ids: tourStops,
      itinerary: tourStops.map(id => graph.nodesMap.get(id)).filter(Boolean),
      daily_plans: dailyPlans,
      legs: legs,
      total_distance_km: cumulativeDist,
      total_time_minutes: cumulativeTime,
      total_cost_inr: cumulativeCost,
      feasible: true,
      action: 'Itinerary Synthesized',
      explanation: `Successfully synthesized ${days}-day optimized tourist tour visiting ${distinctStops.length} key destinations (${cumulativeDist.toFixed(1)} km total road travel).`,
      open_set: [],
      closed_set: tourStops,
    };
  }

  // =========================================================================
  // Algorithm Registry
  // =========================================================================
  const ALGORITHM_REGISTRY = {
    bfs: bfsGenerator,
    dfs: dfsGenerator,
    dijkstra: dijkstraGenerator,
    astar: astarGenerator,
    bellman_ford: bellmanFordGenerator,
    bellman: bellmanFordGenerator,
    kruskal: kruskalGenerator,
    tsp: touristGenerator,
    tourist: touristGenerator,
  };

  // =========================================================================
  // Robust ApiClient with Timeout and Retries
  // =========================================================================
  class LabApiClient {
    static async fetchWithRetry(url, options = {}, { retries = 2, timeoutMs = 4000 } = {}) {
      let lastError = null;

      for (let attempt = 0; attempt <= retries; attempt++) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

        try {
          const reqOptions = Object.assign({}, options, { signal: controller.signal });
          const response = await fetch(url, reqOptions);
          clearTimeout(timeoutId);

          if (!response.ok) {
            throw new Error(`Server returned HTTP ${response.status} (${response.statusText})`);
          }

          const data = await response.json();
          return { success: true, data };
        } catch (err) {
          clearTimeout(timeoutId);
          lastError = err;
          console.warn(`[LabApiClient] Attempt ${attempt + 1}/${retries + 1} failed for ${url}:`, err.message);

          if (attempt < retries) {
            // Wait 350ms before next retry
            await new Promise(res => setTimeout(res, 350));
          }
        }
      }

      return {
        success: false,
        error: lastError,
        isNetworkError: true,
        message: 'Could not contact laboratory server. Running locally via client-side graph engine.',
      };
    }
  }

  // Export to global window object
  window.ClientGraphAlgorithms = {
    buildGraphAdjacency,
    haversineKm,
    reconstructPath,
    calculatePathMetrics,
    bfsGenerator,
    dfsGenerator,
    dijkstraGenerator,
    astarGenerator,
    bellmanFordGenerator,
    kruskalGenerator,
    touristGenerator,
    ALGORITHM_REGISTRY,
    LabApiClient,
  };

})(window);
